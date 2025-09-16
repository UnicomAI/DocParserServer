import time
import functools
from utils.log_utils import setup_logger

# 假设日志已经配置好
logger = setup_logger(__name__, './logs/monitor.log')

def log_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"{func.__name__} took {elapsed_time:.2f} seconds to complete")
        return result
    return wrapper