import os
import sys
import argparse
from minio import Minio, S3Error
# 添加项目根目录到Python路径（确保能导入config）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.log_utils import setup_logger
from config import config

# 初始化日志
logger = setup_logger("minio_test", "./logs/test.log")


def test_minio_upload(file_path):
    """测试MinIO文件上传功能"""
    try:
        # 从配置获取MinIO参数
        bucket_name = config.minio_default_bucket
        minio_address = config.minio_address
        access_key = config.minio_access_key
        secret_key = config.minio_secret_key

        # 打印配置信息（便于调试）
        logger.info("测试MinIO上传配置:")
        logger.info(f"MinIO地址: {minio_address}")
        logger.info(f"Bucket名称: {bucket_name}")
        logger.info(f"访问密钥: {access_key}")
        logger.info(f"访问sk: {secret_key}")

        # 验证文件存在性
        if not os.path.exists(file_path):
            logger.error(f"测试文件不存在: {file_path}")
            return False

        # 初始化MinIO客户端
        minio_client = Minio(
            minio_address,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

        # 检查Bucket是否存在，不存在则创建
        if not minio_client.bucket_exists(bucket_name):
            logger.warning(f"Bucket {bucket_name} 不存在，尝试创建...")
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket {bucket_name} 创建成功")

        # 准备上传参数
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 执行上传（核心测试代码）
        logger.info(f"开始上传文件: {file_path} (大小: {file_size} bytes)")
        with open(file_path, "rb") as file_data:
            result = minio_client.put_object(
                bucket_name,
                file_name,
                file_data,
                file_size
            )

        logger.info(f"文件上传成功! 版本ID: {result.version_id}")
        logger.info(f"存储路径: {bucket_name}/{file_name}")
        return True

    except S3Error as e:
        logger.error(f"MinIO服务错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"上传失败: {str(e)}", exc_info=True)
    return False


if __name__ == "__main__":
    # 解析命令行参数（接收本地文件路径）
    # 执行测试
    success = test_minio_upload("/app/DocParserServer-main/test.png")

    # 终端输出结果（便于直接查看）
    if success:
        print("✅ 文件上传测试成功")
    else:
        print("❌ 文件上传测试失败，请查看日志获取详情")
        sys.exit(1)
