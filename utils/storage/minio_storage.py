import os
from typing import Optional

import requests
from minio import Minio, S3Error

from .base import StorageBase
from utils.log_utils import setup_logger

logger = setup_logger(__name__, './logs/app.log')


class MinIOStorage(StorageBase):
    """MinIO SDK 实现的存储后端"""

    def __init__(self, config: dict):
        self.address = config.get('address')
        self.access_key = config.get('access_key')
        self.secret_key = config.get('secret_key')
        self.default_bucket = config.get('default_bucket')
        self.use_custom = config.get('use_custom', False)
        self.bff_service = config.get('bff_service')

        logger.info(f"MinIO address: {self.address}")
        logger.info(f"MinIO access key: {self.access_key}")

        self.client = Minio(
            self.address,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )

    def upload_file(self, file_path: str, bucket_name: Optional[str] = None,
                    overwrite_file_name: Optional[str] = None) -> Optional[str]:
        """
        上传文件到 MinIO

        Args:
            file_path: 本地文件路径
            bucket_name: 目标桶名称（可选，使用默认桶）
            overwrite_file_name: 覆盖文件名（可选）

        Returns:
            str: 文件下载链接，失败返回 None
        """
        target_bucket = bucket_name or self.default_bucket

        try:
            original_filename = os.path.basename(file_path)
            file_extension = os.path.splitext(original_filename)[1]
            if overwrite_file_name:
                file_name = overwrite_file_name + file_extension
            else:
                file_name = original_filename

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"File '{file_path}' does not exist.")
                return None

            # 获取文件大小
            file_stat = os.stat(file_path)

            # 上传文件到 MinIO
            with open(file_path, "rb") as file_data:
                self.client.put_object(target_bucket, file_name, file_data, file_stat.st_size)

            logger.info(f"File '{file_name}' uploaded to MinIO bucket '{target_bucket}'")

            download_link = self.get_download_url(file_name, target_bucket)
            logger.info(f"File uploaded successfully, download link: {download_link}")
            return download_link

        except S3Error as e:
            logger.error(f"MinIO error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            return None

    def get_download_url(self, object_name: str, bucket_name: Optional[str] = None) -> str:
        """
        获取文件下载链接

        Args:
            object_name: 对象名称
            bucket_name: 桶名称（可选）

        Returns:
            str: 下载链接
        """
        target_bucket = bucket_name or self.default_bucket

        if self.use_custom:
            endpoint = self.address
            return f"http://{endpoint}/{target_bucket}/{object_name}"
        else:
            response = requests.get(self.bff_service)
            response_data = response.json()
            endpoint = response_data['data']['webBaseUrl'].rstrip('/')
            return f"{endpoint}/{target_bucket}/{object_name}"
