import contextvars
import os
import logging
import uuid
from logging.handlers import RotatingFileHandler

trace_id_var = contextvars.ContextVar('trace_id', default=None)

def setup_logger(name, log_file, level=logging.INFO):
    """设置日志记录器"""
    if not os.path.exists('./logs'):
        os.makedirs('./logs')

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 核心优化：如果 logger 已有处理器，直接返回（避免重复添加）
    if logger.handlers:
        return logger

    # 创建 RotatingFileHandler
    file_handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
    file_handler.setLevel(level)

    # 创建 StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(trace_id)s - %(message)s ')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.addFilter(TraceIDFilter())

    return logger

class TraceIDFilter(logging.Filter):
    """日志过滤器，用于从上下文中获取 trace_id"""
    def filter(self, record):
        trace_id = trace_id_var.get()
        record.trace_id = trace_id if trace_id else "N/A"
        return True

def set_trace_id(trace_id):
    """设置 trace_id"""
    trace_id_var.set(trace_id)

def get_trace_id():
    return trace_id_var.get() or "N/A"

def clear_trace_id():
    """清除 trace_id"""
    trace_id_var.set(None)