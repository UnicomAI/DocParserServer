from typing import Dict, Callable, Any

from models.mineru.client import MineruClient
from models.paddleocrvl.client import PaddleOCRVLClient


def init_mineru_client(address: str) -> MineruClient:
    """Mineru模型的Client初始化策略"""
    return MineruClient(address)

def init_paddleocrvl_client(address: str) -> PaddleOCRVLClient:
    """paddleocrvl模型的Client初始化策略（示例）"""
    return PaddleOCRVLClient("http://localhost:5000/file_parse")

CLIENT_STRATEGIES: Dict[str, Callable[[str], Any]] = {
    "mineru": init_mineru_client,
    "paddleocrvl": init_paddleocrvl_client

}