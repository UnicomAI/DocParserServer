import os
import re

import requests

from models.paddleocrvl.table_process_utils import extract_text_with_tables
from utils.file_utils import save_images_res_to_local, upload_to_oss
from utils.log_utils import setup_logger
from utils.monitor_utils import log_time
from config import config as app_config

logger = setup_logger(__name__, './logs/client.log')


def extract_images_from_md(md_content, image_dir):
    img_pattern = r'<img src="imgs/([^"]+)"'
    matches = list(re.finditer(img_pattern, md_content))

    for match in reversed(matches):
        # match.group(0)：匹配到的完整字符串（如 <img src="imgs/xxx.jpg">）
        # match.group(1)：捕获组1的内容（即图片文件名，如 img_in_image_box_447_254_747_368.jpg）
        img_filename = match.group(1)
        # 构造本地图片完整路径
        image_path = os.path.abspath(os.path.join(image_dir, img_filename))

        # 图片不存在：跳过替换
        if not os.path.exists(image_path):
            logger.warn(f"warning：image does not exist. {img_filename} 在目录 {image_dir} 中不存在，跳过替换")
            continue

        # 上传 MinIO 并替换链接
        try:
            download_link = upload_to_oss(image_path, app_config.minio_default_bucket, app_config.minio_secret_key)
            # 构造新的 img 标签
            new_img_tag = f'<img src="{download_link}"'
            # 替换原内容：用新标签替换 match 匹配到的字符串
            md_content = md_content[:match.start()] + new_img_tag + md_content[match.end():]
        except Exception as e:
            logger.error(f"warning：upload images and replace content error. 上传图片 {img_filename} 到 MinIO 失败：{e}，跳过替换")
            continue
    return md_content

class PaddleOCRVLClient:
    def __init__(self, base_url):
        self.base_url = base_url

    @log_time
    def parse_file(self, file_path):
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
                # 发送POST请求（超时设为300秒，适配大文件处理）
                response = requests.post(self.base_url, files=files, timeout=300)
                response.raise_for_status()
                # 记录日志
                response_data = response.json()
                logger.info(f"response is: {response_data}")
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


    def post_process(self, extract_image, file_name, file_path, response):
        data = response.get("data", {})
        md_content = data.get("md_content", "")
        save_images_res_to_local(file_name, data)
        if extract_image and md_content:
            logger.info(f"extracting images for file: {file_path}")
            md_content = extract_images_from_md(md_content,"./data/images")
        md_content = extract_text_with_tables(md_content)
        return md_content
