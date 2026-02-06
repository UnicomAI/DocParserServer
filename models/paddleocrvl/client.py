import os
import re

import requests

from models.paddleocrvl.table_process_utils import extract_text_with_tables
from utils.file_utils import save_images_res_to_local, upload_to_oss
from utils.log_utils import setup_logger
from utils.minio_utils import upload_file_to_minio
from utils.monitor_utils import log_time
from config import config as app_config

logger = setup_logger(__name__, './logs/client.log')




class PaddleOCRVLClient:
    def __init__(self, base_url):
        self.base_url = base_url

    @log_time
    def extract_text_from_image(self, file_name):
        try:
            response = self.parse_file(file_name)
        except Exception as e:
            logger.error(f"extract_text_from_image parse_file error：{str(e)}")
            return ""  # 捕获parse_file异常，返回空字符串兜底
        if response.get("code") != 200:
            logger.error(f"extract_text_from_image response is not 200：{response.get('message')}")
            return ""
        md_content = response.get("data", {}).get("md_content", "")
        pattern = r'<div[^>]*>(?:[^<]*?<(?!/?div)[^<]*?)*?<img[^>]*src[^>]*>(?:<(?!/?div)[^<]*?)*?</div>'
        md_content = re.sub(pattern, '', md_content, flags=re.S)
        return md_content

    @log_time
    def extract_images_from_json(self, json_data, extract_image_content, image_dir):
        for item in json_data:
            block_label = item.get('block_label', '').lower()
            if any(img_type in block_label for img_type in ['image', 'chart', 'footer_image', 'header_image']):
                block_content = item.get('block_content', '')
                img_filename = os.path.basename(block_content) if block_content else ''
                if not img_filename:
                    logger.warning(f"warning：image block_content is empty: {item}")
                    continue
                image_path = os.path.abspath(os.path.join(image_dir, img_filename))
                if not os.path.exists(image_path):
                    logger.warning(f"warning：image does not exist. {img_filename} 在目录 {image_dir} 中不存在，跳过替换")
                    continue

                try:
                    download_link = upload_file_to_minio(
                        image_path
                    )

                    new_block_content = f'<img src="{download_link}" />'
                    item['block_content'] = new_block_content

                    if extract_image_content:
                        ocr_text = self.extract_text_from_image(image_path)
                        logger.info(f"image content extracted is: {ocr_text}")
                        if ocr_text and ocr_text.strip():
                            span_html = f'<span style="display: none;">{ocr_text.strip()}</span>'
                            item['block_content'] = f'<img src="{download_link}" />{span_html}'
                except Exception as e:
                    logger.error(
                        f"warning：upload images and replace content error. "
                        f"上传图片 {img_filename} 到 OSS 失败：{e}，跳过替换"
                    )
                    continue
        return json_data

    @log_time
    def extract_images_from_md(self, md_content, extract_image_content, image_dir):
        import urllib.parse

        def extract_base_url(url):
            """从完整URL中提取基础路径，例如从 https://example.com/path/file.jpg?param=value 提取 https://example.com/path/"""
            parsed_url = urllib.parse.urlparse(url)
            path_parts = parsed_url.path.rsplit('/', 1)
            base_path = path_parts[0] + '/' if len(path_parts) > 1 else parsed_url.path
            return f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}"

        img_pattern = r'<div[^>]*>.*?<img src="imgs/([^"]+)"[^>]*?>.*?</div>'
        matches = list(re.finditer(img_pattern, md_content))
        prefix_image_url = "https://obs-nmhhht6.cucloud.cn/doc-rag-public"

        for match in reversed(matches):
            img_filename = match.group(1)
            image_path = os.path.abspath(os.path.join(image_dir, img_filename))
            logger.info(f"extracting images done for file: {image_path}")
            if not os.path.exists(image_path):
                logger.warn(f"warning：image does not exist. {img_filename} 在目录 {image_dir} 中不存在，跳过替换")
                continue
            try:
                download_link = upload_file_to_minio(image_path)
                ocr_text = ""
                # OCR提取文字
                logger.info(f"extract_image_content is: {extract_image_content}")
                if extract_image_content:
                    ocr_text = self.extract_text_from_image(image_path)
                    filter_pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9\s]'
                    logger.info(rf"image content extracted is:: {ocr_text}")
                    ocr_text = re.sub(r'<[^>]+>', '', ocr_text)  # 过滤所有HTML标签（<div>、</div>等）
                    ocr_text = re.sub(r'[\n\r]', '', ocr_text)  # 过滤换行符\n、回车符\r
                    ocr_text = ocr_text.strip()  # 先去掉标签/换行后的首尾空格
                    ocr_text = re.sub(filter_pattern, "", ocr_text)
                new_img_tag = f'![{ocr_text}]({download_link})'
                md_content = md_content[:match.start()] + new_img_tag + md_content[match.end():]
                prefix_image_url = download_link
            except Exception as e:
                logger.error(
                    f"warning：upload images and replace content error. 上传图片 {img_filename} 到 MinIO 失败：{e}，跳过替换")
                continue
        return md_content,extract_base_url(prefix_image_url)

    @log_time
    def parse_file(self,
                   file_path: str,
                   return_json: bool = False):
        file_name = os.path.basename(file_path)
        _, file_ext = os.path.splitext(file_name)
        if(file_ext not in [".pdf", ".jpg", ".jpeg", ".png"]):
            logger.error(f"warning：file type is not supported. 文件类型 {file_ext} 不支持，仅支持 pdf、jpg、jpeg、png 格式")
            raise ValueError(f"File type {file_ext} is not supported. Only pdf, jpg, jpeg, png are supported.")
        try:
            with open(file_path, "rb") as f:
                # 构造文件上传参数（用Path获取文件名，兼容不同系统路径）
                files = {
                    "file": (file_name,  # 文件名（仅用于接口识别，不影响本地路径）
                             f,  # 文件二进制流
                             "application/pdf"  # MIME类型，明确是PDF文件
                             )
                }
                data = {
                    "return_json": str(return_json).lower()  # 将布尔值转换为小写字符串
                }
                # 发送POST请求（超时设为300秒，适配大文件处理）
                response = requests.post(self.base_url, files=files, data=data, timeout=300)
                response.raise_for_status()
                # 记录日志
                response_data = response.json()
                # logger.info(f"response is: {response_data}")
                return response_data
        except requests.HTTPError as e:
            logger.info(f"paddleocr request HTTPError：{e}")
            raise
        except requests.RequestException as e:
            logger.info(f"paddleocr request RequestException：{e}")
            raise
        except Exception as e:
            logger.info(f"paddleocr request exception: {e}")
            raise


    def post_process(self, extract_image,
                     extract_image_content,
                     file_name,
                     file_path,
                     return_json,
                     response):
        data = response.get("data", {})
        logger.info(f"data is: {data}")
        md_content = data.get("md_content", "")
        json_content = data.get("json_data", "")
        prefix_image_url = "https://obs-nmhhht6.cucloud.cn/doc-rag-public"
        save_images_res_to_local(file_name, data)
        if extract_image and md_content:
            logger.info(f"extracting images for file: {file_path}")
            md_content, prefix_image_url = self.extract_images_from_md(md_content, extract_image_content,"./data/images")
        if extract_image and return_json:
            logger.info(f"extracting json images for file: {file_path}")
            json_content = self.extract_images_from_json(json_content, extract_image_content, "./data/images")
        logger.info(f"extracting images done for file: {file_path}")
        md_content = extract_text_with_tables(md_content)
        return md_content, json_content, prefix_image_url
