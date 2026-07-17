from typing import Dict, Callable, Any

from models.mineru.client import MineruClient


def init_mineru_client(address: str) -> MineruClient:
    """Mineru模型的Client初始化策略"""
    return MineruClient(address)


def init_paddleocrvl_client(address: str) -> Any:
    """paddleocrvl模型的Client初始化策略（惰性加载）"""
    from models.paddleocrvl.client import PaddleOCRVLClient
    return PaddleOCRVLClient("http://localhost:5000/file_parse")


CLIENT_STRATEGIES: Dict[str, Callable[[str], Any]] = {
    "mineru": init_mineru_client,
    "paddleocrvl": init_paddleocrvl_client
}