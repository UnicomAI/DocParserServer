from dataclasses import dataclass
import os


class SingletonMeta(type):
    """单例模式的元类，确保类只有一个实例"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # 首次调用时创建实例
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class AppConfig(metaclass=SingletonMeta):
    """应用配置类，集中管理所有环境变量"""
    # 服务相关配置
    model_type: str = os.getenv("MODEL_TYPE", "mineru") #mineru, paddleocrvl
    model_address: str = os.getenv("MODEL_ADDRESS", "http://127.0.0.1:8000/file_parse")
    doc_parser_server_port: int = int(os.getenv("DOC_PARSER_SERVER_PORT", 8083))

    # 文件转换服务配置
    stirling_address: str = os.getenv("STIRLING_ADDRESS", "http://localhost:8080/api/v1/convert/file/pdf")

    # MinIO存储服务配置
    # 是否使用自定义MinIO服务，若为true则address配置为http://ip:port，否则为minio-wanwu:9000
    use_custom_minio: bool = os.getenv("USE_CUSTOM_MINIO", "false").strip().lower() == "true"
    minio_default_bucket: str = os.getenv("MINIO_DEFAULT_BUCKET", "rag-public")
    bff_service_minio: str = os.getenv("BFF_SERVICE_MINIO", "http://bff-service:6668/v1/api/deploy/info")
    minio_address: str = os.getenv("MINIO_ADDRESS", "minio-wanwu:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "root")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "your_sk")

config = AppConfig()