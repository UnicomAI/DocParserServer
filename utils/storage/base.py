from abc import ABC, abstractmethod
from typing import Optional


class StorageBase(ABC):
    """对象存储抽象基类"""

    @abstractmethod
    def upload_file(self, file_path: str, bucket_name: Optional[str] = None,
                    overwrite_file_name: Optional[str] = None) -> Optional[str]:
        """
        上传文件到对象存储

        Args:
            file_path: 本地文件路径
            bucket_name: 目标桶名称（可选，使用默认桶）
            overwrite_file_name: 覆盖文件名（可选）

        Returns:
            str: 文件下载链接，失败返回 None
        """
        pass

    @abstractmethod
    def get_download_url(self, object_name: str, bucket_name: Optional[str] = None) -> str:
        """
        获取文件下载链接

        Args:
            object_name: 对象名称
            bucket_name: 桶名称（可选）

        Returns:
            str: 下载链接
        """
        pass
