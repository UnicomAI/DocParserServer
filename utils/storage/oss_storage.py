import os
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from .base import StorageBase
from utils.log_utils import setup_logger

logger = setup_logger(__name__, './logs/app.log')

# 连接超时设置（秒）
OSS_CONNECT_TIMEOUT = int(os.getenv("OSS_CONNECT_TIMEOUT", "10"))
OSS_READ_TIMEOUT = int(os.getenv("OSS_READ_TIMEOUT", "30"))


class OSSStorage(StorageBase):
    """通用 S3 协议存储后端实现（支持华为 OBS、阿里云 OSS、MinIO 等）"""

    def __init__(self, config: dict):
        self.endpoint = config.get('endpoint', '')
        self.access_key = config.get('access_key')
        self.secret_key = config.get('secret_key')
        self.bucket = config.get('bucket')
        self.region = config.get('region', '')

        # 自动添加 https:// 前缀（如果未指定协议）
        if self.endpoint and not self.endpoint.startswith(('http://', 'https://')):
            self.endpoint = f"https://{self.endpoint}"

        logger.info(f"OSS endpoint: {self.endpoint}")
        logger.info(f"OSS bucket: {self.bucket}")
        if self.region:
            logger.info(f"OSS region: {self.region}")
        logger.info(f"OSS connect_timeout: {OSS_CONNECT_TIMEOUT}s, read_timeout: {OSS_READ_TIMEOUT}s")

        # 创建 S3 兼容客户端
        self.client = self._create_client()

        # 验证连接
        self._verify_connection()

    def _create_client(self):
        """创建 S3 兼容客户端"""
        client_kwargs = {
            'service_name': 's3',
            'endpoint_url': self.endpoint,
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
            'config': boto3.session.Config(
                connect_timeout=OSS_CONNECT_TIMEOUT,
                read_timeout=OSS_READ_TIMEOUT,
                signature_version='s3v4'
            )
        }

        # region 有值则添加
        if self.region:
            client_kwargs['region_name'] = self.region

        # 禁用 SSL 证书验证（某些私有云环境需要）
        # 可以通过环境变量控制
        verify_ssl = os.getenv("OSS_VERIFY_SSL", "true").lower() == "true"
        if not verify_ssl:
            client_kwargs['verify'] = False

        return boto3.client(**client_kwargs)

    def _verify_connection(self):
        """验证 OSS 连接是否正常"""
        try:
            # 尝试访问 bucket 来验证连接
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"OSS 连接验证成功: bucket '{self.bucket}' 可访问")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchBucket':
                logger.error(f"OSS 连接验证失败: bucket '{self.bucket}' 不存在")
            elif error_code == '403' or error_code == 'AccessDenied':
                logger.error(f"OSS 连接验证失败: AccessKey 无权限访问 bucket '{self.bucket}'")
            else:
                logger.error(f"OSS 连接验证失败: {e}")
            raise
        except Exception as e:
            logger.error(f"OSS 连接验证失败: {e}")
            raise

    def upload_file(self, file_path: str, bucket_name: Optional[str] = None,
                    overwrite_file_name: Optional[str] = None) -> Optional[str]:
        """
        上传文件到 OSS

        Args:
            file_path: 本地文件路径
            bucket_name: 目标桶名称（可选，暂不支持切换桶）
            overwrite_file_name: 覆盖文件名（可选）

        Returns:
            str: 文件下载链接，失败返回 None
        """
        try:
            original_filename = os.path.basename(file_path)
            file_extension = os.path.splitext(original_filename)[1]
            if overwrite_file_name:
                object_name = overwrite_file_name + file_extension
            else:
                object_name = original_filename

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"File '{file_path}' does not exist.")
                return None

            # 上传文件到 OSS
            with open(file_path, 'rb') as f:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=object_name,
                    Body=f
                )

            logger.info(f"File '{object_name}' uploaded to OSS bucket '{self.bucket}'")

            # 获取下载链接
            download_url = self.get_download_url(object_name)
            logger.info(f"File uploaded successfully, download link: {download_url}")
            return download_url

        except ClientError as e:
            logger.error(f"OSS error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading file to OSS: {e}")
            return None

    def get_download_url(self, object_name: str, bucket_name: Optional[str] = None,
                         expires: int = 3600 * 24 * 7) -> str:
        """
        获取文件下载链接（公开 URL，永不过期）

        公共读写桶无需签名，直接拼接公开访问地址。
        保留 expires 参数以兼容外部调用，但不再使用。

        Args:
            object_name: 对象名称
            bucket_name: 桶名称（可选，暂不支持切换桶）
            expires: 已弃用，保留参数兼容性

        Returns:
            str: 公开下载链接
        """
        # 公共桶：拼接公开 URL，无有效期限制
        # 格式: {endpoint}/{bucket}/{object_name}
        return f"{self.endpoint}/{self.bucket}/{object_name}"
