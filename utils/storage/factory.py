from typing import Optional

from .base import StorageBase
from .minio_storage import MinIOStorage
from .oss_storage import OSSStorage
from config import config
from utils.log_utils import setup_logger

logger = setup_logger(__name__, './logs/app.log')


class StorageFactory:
    """存储后端工厂"""

    _instance: Optional[StorageBase] = None

    @classmethod
    def get_storage(cls) -> StorageBase:
        """
        获取存储实例（单例）

        Returns:
            StorageBase: 存储实例
        """
        if cls._instance is None:
            cls._instance = cls._create_storage()
        return cls._instance

    @classmethod
    def _create_storage(cls) -> StorageBase:
        """
        根据环境变量创建存储实例

        Returns:
            StorageBase: 存储实例
        """
        oss_type = config.oss_type.lower()
        logger.info(f"Creating storage instance, OSS_TYPE: {oss_type}")

        if oss_type == 'minio':
            minio_config = {
                'address': config.minio_address,
                'access_key': config.minio_access_key,
                'secret_key': config.minio_secret_key,
                'default_bucket': config.minio_default_bucket,
                'use_custom': config.use_custom_minio,
                'bff_service': config.bff_service_minio,
            }
            return MinIOStorage(minio_config)

        elif oss_type == 'oss':
            oss_config = {
                'endpoint': config.oss_endpoint,
                'access_key': config.oss_access_key,
                'secret_key': config.oss_secret_key,
                'bucket': config.oss_bucket,
                'region': config.oss_region,
            }
            return OSSStorage(oss_config)

        else:
            raise ValueError(f"不支持的 OSS_TYPE: {oss_type}，可选值: minio, oss")

    @classmethod
    def reset(cls):
        """重置实例（用于测试）"""
        cls._instance = None
