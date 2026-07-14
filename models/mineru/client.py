import base64
import mimetypes
import os
import re
import urllib.parse

import requests

from config import config as app_config
from utils.log_utils import setup_logger
from utils.monitor_utils import log_time
from utils.storage.factory import StorageFactory

logger = setup_logger(__name__, './logs/client.log')


def _extract_base_url(url: str) -> str:
    """从完整 URL 中提取基础路径

    例如：https://example.com/path/file.jpg?param=value → https://example.com/path/
    """
    parsed = urllib.parse.urlparse(url)
    path_parts = parsed.path.rsplit('/', 1)
    base_path = path_parts[0] + '/' if len(path_parts) > 1 else parsed.path
    return f"{parsed.scheme}://{parsed.netloc}{base_path}"


class MineruClient:
    def __init__(self, base_url):
        self.base_url = base_url

    @log_time
    def parse_file(self,
                   file_path: str,
                   return_json: bool = False):
        """
        调用 MinerU 3.0 /file_parse 接口解析文档

        支持文档类型：PDF、图片（jpg/jpeg/png）、Word（docx）、PowerPoint（pptx）、Excel（xlsx）
        """
        endpoint = f"{self.base_url}/file_parse"
        file_name = os.path.basename(file_path)

        # MIME 类型自动识别
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        # 构建请求参数 — 分类管理
        # 写死 true 的参数
        payload = {
            "return_md": "true",
            "return_content_list": "true",
            "formula_enable": "true",
            "table_enable": "true",
            # 环境变量可配的参数（有默认值）
            "backend": app_config.mineru_backend,
            "lang_list": app_config.mineru_lang_list,
            "effort": app_config.mineru_effort,
            "image_analysis": app_config.mineru_image_analysis,
        }
        # server_url 非空时才传递
        if app_config.mineru_server_url:
            payload["server_url"] = app_config.mineru_server_url

        with open(file_path, "rb") as file_obj:
            files = [
                ("files", (file_name, file_obj, mime_type))
            ]
            try:
                response = requests.post(endpoint, data=payload, files=files, timeout=300)
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"MinerU response status: {response_data.get('status')}")
                return response_data
            except requests.HTTPError as e:
                logger.error(f"MinerU 请求失败，状态码：{e.response.status_code}")
                raise
            except requests.RequestException as e:
                logger.error(f"MinerU 请求异常：{e}")
                raise

    def post_process(self, extract_image,
                     extract_image_content,
                     file_name,
                     file_path,
                     return_json,
                     response):
        """
        后处理：解析 MinerU 3.0 响应，提取 md_content，处理图片（base64 → OSS 上传 → md 替换）
        """
        # 文件名去后缀，用于从 results 中索引
        file_key = os.path.splitext(file_name)[0]
        result = response.get("results", {}).get(file_key, {})
        md_content = result.get("md_content", "")
        images = result.get("images", {})  # {filename: "data:image/jpeg;base64,..."}

        # prefix_image_url 默认值
        prefix_image_url = "https://obs-nmhhht6.cucloud.cn/doc-rag-public"

        if extract_image and images and md_content:
            # 保存 base64 图片到本地，同时上传到 OSS，收集 URL 映射
            image_output_dir = "./data/images"
            if not os.path.exists(image_output_dir):
                os.makedirs(image_output_dir)

            url_map = {}  # {filename: oss_url}
            for img_filename, base64_data_uri in images.items():
                try:
                    # 解码 base64 data URI
                    # 格式："data:image/jpeg;base64,/9j/4AAQ..."
                    _, base64_data = base64_data_uri.split(",", 1)
                    image_data = base64.b64decode(base64_data)

                    # 保存到本地
                    save_path = os.path.join(image_output_dir, img_filename)
                    with open(save_path, "wb") as f:
                        f.write(image_data)

                    # 上传到 OSS/MinIO
                    storage = StorageFactory.get_storage()
                    download_link = storage.upload_file(save_path)
                    url_map[img_filename] = download_link

                    # 上传成功后删除临时文件
                    os.remove(save_path)
                    logger.info(f"图片 {img_filename} 已上传 OSS: {download_link}")

                    # 记录最后一张图片 URL，用于提取 prefix_image_url
                    prefix_image_url = download_link
                except Exception as e:
                    logger.error(f"处理图片 {img_filename} 失败：{e}，跳过")
                    continue

            # 将 md 中的 ![](images/{filename}) 替换为 ![]({oss_url})
            if url_map:
                def _replace_img_link(match):
                    img_path = match.group(1)
                    # MinerU 返回的 md 中图片引用格式有两种可能：
                    # 1. ![](images/xxx.jpg)
                    # 2. ![](xxx.jpg)
                    img_name = os.path.basename(img_path)
                    oss_url = url_map.get(img_name)
                    if oss_url:
                        return f'![]({oss_url})'
                    return match.group(0)

                md_content = re.sub(r'!\[\]\(([^)]+)\)', _replace_img_link, md_content)

        # 从最后成功上传的 URL 提取基础路径作为 prefix_image_url
        if prefix_image_url != "https://obs-nmhhht6.cucloud.cn/doc-rag-public":
            prefix_image_url = _extract_base_url(prefix_image_url)

        return md_content, "", prefix_image_url