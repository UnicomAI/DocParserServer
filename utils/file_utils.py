import base64
import os
import re
import requests
import yaml

from utils.log_utils import setup_logger
from utils.minio_utils import upload_file_to_minio

logger = setup_logger(__name__, './logs/app.log')

data_dirs = ['./data/raw', './data/processed']

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
object_storage_config = config["object_storage"]

def upload_to_oss(file_path, bucket_name, access_token):
    """
    上传文件到OSS
    :param file_path: 本地文件路径
    :param bucket_name: OSS桶名称
    :param access_token: 访问令牌
    :return: OSS下载链接
    """
    url = "https://maas-api.ai-yuanjing.com/openapi/v1/external/upload"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    files = {
        "file": open(file_path, "rb")
    }
    data = {"bucketname": bucket_name}
    response = requests.post(url, headers=headers, files=files, data=data, verify=False)
    if response.status_code == 200:
        return response.json().get("download_link")
    else:
        logger.error(f"Failed to upload file to OSS: {response.text}")
        return None

def fulfill_image_title(md_content, n = 3):
    lines = md_content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        # 检查是否是图片链接
        match = re.match(r'!\[\]\((.*?)\)', line)
        if match:
            image_link = match.group(1)
            description = f"image"
            # 查看接下来的 N 行
            for j in range(1, n + 1):
                if i + j < len(lines):
                    next_line = lines[i + j].strip().lower()
                    if next_line.startswith('图') or next_line.startswith('figure'):
                        description = lines[i + j].strip()
                        break
            line = f'![{description}]({image_link})'
        new_lines.append(line)
        i += 1
    processed_md_content = '\n'.join(new_lines)
    return processed_md_content

def extract_images_from_md(md_content, image_dir):
    # 提取图片
    logger.info(f"extracting images from md content. image_dir: {image_dir}")
    if not os.path.exists(image_dir):
        return md_content
    md_content = fulfill_image_title(md_content)
    # 提取所有图片链接
    image_links = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
    # md_content = re.sub(r'!\[Figure\]\(figures/', '![image](figures/', md_content)
    for image_link in image_links:
        if image_link.startswith("images/"):
            image_path = os.path.join(os.path.dirname(image_dir), image_link)
            logger.info(f"extracting images from md content. image_path: {image_path}")
            if os.path.exists(image_path):
                # 上传图片到 OS
                download_link = upload_file_to_minio(image_path)
                if download_link:
                    md_content = md_content.replace(image_link, download_link)
                else:
                    logger.info(f"Failed to upload image: {image_path}")
            else:
                logger.info(f"Image file not found: {image_path}")
    print(f"md_content: {md_content}")
    return md_content

def save_file_url_to_local(file_link, file_name):
    """
    保存文件到指定目录，如果文件名冲突，直接覆盖同名文件。

    :param file_name: 文件名，已校验确保有值
    :param file_link: 文件链接，已校验确保有值
    :return: 保存后的文件路径
    """
    # 确保保存目录存在
    if not os.path.exists(data_dirs[0]):
        os.makedirs(data_dirs[0])
    # 优先使用文件链接下载文件
    file_path = os.path.join(data_dirs[0], file_name)
    try:
        response = requests.get(file_link, timeout=300)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
    except requests.RequestException as e:
        raise Exception(f"Failed to download file from link: {e}")
    return file_path


def save_file_to_local(file, file_name):
    """
    保存文件到指定目录，如果文件名冲突，直接覆盖同名文件。
    :param file: 文件对象，已校验确保有值
    :param file_name: 文件名，已校验确保有值
    :return: 保存后的文件路径
    """
    # 确保保存目录存在
    if not os.path.exists(data_dirs[0]):
        os.makedirs(data_dirs[0])

    # 保存文件到指定路径
    file_path = os.path.join(data_dirs[0], file_name)
    try:
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file.read())
    except Exception as e:
        raise Exception(f"Failed to save file: {e}")

    return file_path

def save_images_res_to_local(file_name, results):
    # 定义保存图片的目标目录
    output_dir = "./data/images"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename, base64_data in results["images"].items():
        # 分离 Base64 数据的头部（例如 "data:image/jpeg;base64,"）
        base64_data = base64_data.split(",", 1)[1]
        # 解码 Base64 数据
        image_data = base64.b64decode(base64_data)
        # 构造保存路径
        save_path = os.path.join(output_dir, filename)
        # 保存图片到本地
        with open(save_path, "wb") as image_file:
            image_file.write(image_data)