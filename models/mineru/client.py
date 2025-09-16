import json
import os
import requests
from utils.monitor_utils import log_time
from utils.log_utils import setup_logger

logger = setup_logger(__name__, './logs/client.log')

class MineruClient:
    def __init__(self, base_url):
        self.base_url = base_url

    @log_time
    def parse_file(self, file_path):
        endpoint = f"{self.base_url}"
        # modify if needed, please refer to mineru documentation: https://github.com/opendatalab/MinerU/blob/master/mineru/cli/fast_api.py async def parse_pdf
        payload = {
            "output_dir": "./output",
            "backend": "pipeline",
            "lang_list": "ch",
            "return_md": "true",
            "return_content_list": "True",
            "return_images": "True"
        }
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file_obj:
            files = [
                ("files", (file_name, file_obj, "application/pdf"))
            ]
            try:
                response = requests.post(endpoint, data=payload, files=files)
                response.raise_for_status()
                # 记录日志
                response_data = response.json()
                formatted_response = json.dumps(response_data, indent=4, ensure_ascii=False)
                logger.info(f"response is: {formatted_response}")
                return response_data
            except requests.HTTPError as e:
                logger.info(f"请求失败，状态码：{e.response.status_code}")
                raise
            except requests.RequestException as e:
                logger.info(f"请求异常：{e}")
                raise

