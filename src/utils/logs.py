# -*- coding: utf-8 -*-
"""
日志工具
"""

import os
import json
import logging

from ..config import config

# 日志相关
MAX_LOGS_HISTORY = config.MAX_LOGS_HISTORY
execution_logs_history = []


def save_logs_to_file():
    """保存日志到文件"""
    try:
        log_path = os.path.join(os.path.dirname(__file__), "..", "..", "execution_logs.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(execution_logs_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger = logging.getLogger("ai_security")
        logger.error(f"保存日志到文件失败: {e}")


def setup_logger(name: str = "ai_security") -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
    
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
