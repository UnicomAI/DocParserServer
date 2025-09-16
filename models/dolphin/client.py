import requests
import json


class DolphinClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def parse_file(self, file_content):
        # 全局加载模型（启动时加载一次）
        # config = OmegaConf.load("config/Dolphin.yaml")
        # model = DOLPHIN(config)
        return "comming soon"