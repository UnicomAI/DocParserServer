import os
import requests

from utils.monitor_utils import log_time
from config import config

from utils.log_utils import setup_logger
logger = setup_logger(__name__, './logs/app.log')

def convert_to_pdf(file_path):
    if file_path.endswith(".pdf"):
        return file_path
    elif file_path.endswith((".docx", ".doc", ".ppt", "pptx")):
        return libreoffice_to_pdf(file_path)
    else:
        return file_path

@log_time
def libreoffice_to_pdf(file_path):
    """
    调用文件转换接口，将docx文件转换为PDF

    参数:
        file_path: 本地docx文件的路径（如 './ez_formula.docx'）

    返回:
        pdf目录/抛出异常
    """
    file_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)
    file_name_without_ext, file_ext = os.path.splitext(file_name)
    pdf_file_path = os.path.join(file_dir, f"{file_name_without_ext}.pdf")
    url = config.stirling_address
    headers = {
        "accept": "*/*"
        # 注意：Content-Type 不需要手动设置，requests会自动处理为 multipart/form-data
    }
    files = {
        "fileInput": (
            file_name,
            open(file_path, "rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # MIME类型
        )
    }

    try:
        # 发送POST请求
        response = requests.post(
            url=url,
            headers=headers,
            files=files
        )

        # 检查响应状态码
        response.raise_for_status()  # 若状态码为4xx/5xx，会抛出HTTPError
        with open(pdf_file_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        logger.info(f"convert_to_pdf 成功转换 {file_path} 为 {pdf_file_path}")
        os.remove(file_path)
        return pdf_file_path

    except requests.exceptions.HTTPError as e:
        logger.error(f"convert_to_pdf HTTP请求错误: {e}")
        return file_path
    except requests.exceptions.RequestException as e:
        logger.error(f"convert_to_pdf 请求发生错误: {e}")
        return file_path
    except Exception as e:
        logger.error(f"convert_to_pdf 未知错误: {e}")
        return file_path
    finally:
        # 确保文件流关闭
        if 'files' in locals() and files['fileInput'][1].closed is False:
            files['fileInput'][1].close()


# if __name__ == "__main__":
#     file = r"/root/test.docx"
#     convert_to_pdf(file)