import os

import requests
from minio import Minio, S3Error
from utils.log_utils import setup_logger
logger = setup_logger(__name__, './logs/app.log')

bucket_name = os.getenv("MINIO_DEFAULT_BUCKET", "rag-public")
bff_service_minio = os.getenv("BFF_SERVICE_MINIO", "http://bff-service:6668/v1/api/deploy/info") #http://192.168.0.21:6668/v1/api/deploy/info

MINIO_ADDRESS = os.getenv("MINIO_ADDRESS")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
if MINIO_ADDRESS is None or MINIO_ACCESS_KEY is None or MINIO_SECRET_KEY is None:
    MINIO_ADDRESS = "minio-wanwu:9000" #192.168.0.21:9000
    MINIO_ACCESS_KEY = "root"
    MINIO_SECRET_KEY = "your_sk"

logger.info(f"minio address: {MINIO_ADDRESS}")
logger.info(f"minio access key: {MINIO_ACCESS_KEY}")
logger.info(f"minio secret key: {MINIO_SECRET_KEY}")
minio_client = Minio(
    MINIO_ADDRESS,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def upload_file_to_minio(file_path, overwrite_file_name=None):
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
            minio_client.put_object(bucket_name, file_name, file_data, file_stat.st_size)

        logger.info(f"File '{file_name}' uploaded to Minio bucket '{bucket_name}'")

        response = requests.get(bff_service_minio)
        response_data = response.json()
        endpoint = response_data['data']['webBaseUrl']
        # http://192.168.0.21:8081/minio/download/api/
        download_link = f"{endpoint}{bucket_name}/{file_name}"
        logger.info(f"File uploaded successfully, download link: {download_link}")
        return download_link
    except S3Error as e:
        logger.error(f"MinIO error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading file to MinIO: {e}")
        return None