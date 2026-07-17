import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from utils.storage.factory import StorageFactory
from utils.storage.base import StorageBase
from utils.storage.minio_storage import MinIOStorage
from utils.storage.oss_storage import OSSStorage


class TestStorageFactory:
    """StorageFactory 测试类"""

    def setup_method(self):
        """每个测试方法前重置实例"""
        StorageFactory.reset()

    def test_create_minio_storage(self):
        """测试创建 MinIO 存储实例"""
        with patch('utils.storage.factory.config') as mock_config:
            mock_config.oss_type = 'minio'
            mock_config.minio_address = 'localhost:9000'
            mock_config.minio_access_key = 'test_access'
            mock_config.minio_secret_key = 'test_secret'
            mock_config.minio_default_bucket = 'test-bucket'
            mock_config.use_custom_minio = False
            mock_config.bff_service_minio = 'http://test:8080/api'

            storage = StorageFactory.get_storage()

            assert isinstance(storage, MinIOStorage)
            assert storage.address == 'localhost:9000'
            assert storage.default_bucket == 'test-bucket'

    def test_create_oss_storage(self):
        """测试创建 OSS 存储实例"""
        with patch('utils.storage.factory.config') as mock_config:
            mock_config.oss_type = 'oss'
            mock_config.oss_endpoint = 'oss.example.com'
            mock_config.oss_access_key = 'test_access_key'
            mock_config.oss_secret_key = 'test_secret_key'
            mock_config.oss_bucket = 'test-bucket'

            storage = StorageFactory.get_storage()

            assert isinstance(storage, OSSStorage)
            assert storage.endpoint == 'oss.example.com'
            assert storage.bucket == 'test-bucket'

    def test_unsupported_storage_type(self):
        """测试不支持的存储类型"""
        with patch('utils.storage.factory.config') as mock_config:
            mock_config.oss_type = 'unsupported'

            with pytest.raises(ValueError, match="不支持的 OSS_TYPE"):
                StorageFactory.get_storage()

    def test_singleton_pattern(self):
        """测试单例模式"""
        with patch('utils.storage.factory.config') as mock_config:
            mock_config.oss_type = 'minio'
            mock_config.minio_address = 'localhost:9000'
            mock_config.minio_access_key = 'test_access'
            mock_config.minio_secret_key = 'test_secret'
            mock_config.minio_default_bucket = 'test-bucket'
            mock_config.use_custom_minio = False
            mock_config.bff_service_minio = 'http://test:8080/api'

            storage1 = StorageFactory.get_storage()
            storage2 = StorageFactory.get_storage()

            assert storage1 is storage2

    def test_reset(self):
        """测试重置实例"""
        with patch('utils.storage.factory.config') as mock_config:
            mock_config.oss_type = 'minio'
            mock_config.minio_address = 'localhost:9000'
            mock_config.minio_access_key = 'test_access'
            mock_config.minio_secret_key = 'test_secret'
            mock_config.minio_default_bucket = 'test-bucket'
            mock_config.use_custom_minio = False
            mock_config.bff_service_minio = 'http://test:8080/api'

            storage1 = StorageFactory.get_storage()
            StorageFactory.reset()
            storage2 = StorageFactory.get_storage()

            assert storage1 is not storage2


class TestMinIOStorage:
    """MinIOStorage 测试类"""

    def test_init(self):
        """测试初始化"""
        config = {
            'address': 'localhost:9000',
            'access_key': 'test_access',
            'secret_key': 'test_secret',
            'default_bucket': 'test-bucket',
            'use_custom': True,
            'bff_service': 'http://test:8080/api'
        }

        with patch('utils.storage.minio_storage.Minio') as mock_minio:
            storage = MinIOStorage(config)

            assert storage.address == 'localhost:9000'
            assert storage.default_bucket == 'test-bucket'
            assert storage.use_custom is True
            mock_minio.assert_called_once()

    def test_get_download_url_custom(self):
        """测试自定义 MinIO 下载链接"""
        config = {
            'address': 'localhost:9000',
            'access_key': 'test_access',
            'secret_key': 'test_secret',
            'default_bucket': 'test-bucket',
            'use_custom': True,
            'bff_service': 'http://test:8080/api'
        }

        with patch('utils.storage.minio_storage.Minio'):
            storage = MinIOStorage(config)
            url = storage.get_download_url('test.jpg')

            assert url == 'http://localhost:9000/test-bucket/test.jpg'

    def test_get_download_url_bff(self):
        """测试 BFF 服务下载链接"""
        config = {
            'address': 'localhost:9000',
            'access_key': 'test_access',
            'secret_key': 'test_secret',
            'default_bucket': 'test-bucket',
            'use_custom': False,
            'bff_service': 'http://test:8080/api'
        }

        with patch('utils.storage.minio_storage.Minio'):
            with patch('utils.storage.minio_storage.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = {'data': {'webBaseUrl': 'http://cdn.example.com/'}}
                mock_get.return_value = mock_response

                storage = MinIOStorage(config)
                url = storage.get_download_url('test.jpg')

                assert url == 'http://cdn.example.com/test-bucket/test.jpg'


class TestOSSStorage:
    """OSSStorage 测试类"""

    def test_init(self):
        """测试初始化"""
        config = {
            'endpoint': 'oss.example.com',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'bucket': 'test-bucket'
        }

        with patch('utils.storage.oss_storage.boto3.client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.head_bucket.return_value = {}

            storage = OSSStorage(config)

            assert storage.endpoint == 'https://oss.example.com'
            assert storage.bucket == 'test-bucket'
            mock_client.assert_called_once()

    def test_upload_file_success(self):
        """测试上传文件成功"""
        config = {
            'endpoint': 'oss.example.com',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'bucket': 'test-bucket'
        }

        with patch('utils.storage.oss_storage.boto3.client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.head_bucket.return_value = {}
            mock_client_instance.put_object.return_value = {}
            mock_client_instance.generate_presigned_url.return_value = 'https://oss.example.com/test-bucket/test.jpg?signature=xxx'

            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value = MagicMock()

                    storage = OSSStorage(config)
                    result = storage.upload_file('/tmp/test.jpg')

                    assert result is not None
                    mock_client_instance.put_object.assert_called_once()

    def test_upload_file_not_found(self):
        """测试文件不存在"""
        config = {
            'endpoint': 'oss.example.com',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'bucket': 'test-bucket'
        }

        with patch('utils.storage.oss_storage.boto3.client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.head_bucket.return_value = {}

            with patch('os.path.exists', return_value=False):
                storage = OSSStorage(config)
                result = storage.upload_file('/tmp/not_exist.jpg')

                assert result is None

    def test_get_download_url(self):
        """测试获取下载链接"""
        config = {
            'endpoint': 'oss.example.com',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'bucket': 'test-bucket'
        }

        with patch('utils.storage.oss_storage.boto3.client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.head_bucket.return_value = {}
            mock_client_instance.generate_presigned_url.return_value = 'https://oss.example.com/test-bucket/test.jpg?X-Amz-Signature=xxx'

            storage = OSSStorage(config)
            url = storage.get_download_url('test.jpg')

            assert 'test.jpg' in url
            mock_client_instance.generate_presigned_url.assert_called_once_with(
                'get_object',
                Params={'Bucket': 'test-bucket', 'Key': 'test.jpg'},
                ExpiresIn=3600 * 24 * 7
            )
