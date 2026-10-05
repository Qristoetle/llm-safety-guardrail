# -*- coding: utf-8 -*-
"""Application configuration; service credentials come from the environment."""

import os
from typing import Dict


class Config:
    HOST = "0.0.0.0"
    PORT = 6006
    DEBUG = True

    VLLM_BASE_URL = "http://127.0.0.1:6007"
    VLLM_TIMEOUT = 60
    VLLM_MAX_RETRIES = 5
    VLLM_RETRY_DELAY = 1
    VLLM_RETRY_BACKOFF = 1.0

    LORA_ADAPTERS: Dict[str, str] = {
        "classify": "classify",
        "china": "china",
    }

    SENSITIVE_WORDS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "program", "sensitive", "中文互联网敏感词.txt",
    )

    SECURITY_CHECK_ENABLED = True
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]

    DATA_PURIFICATION_MODEL = "gemini-2.5-flash"
    DATA_PURIFICATION_API_KEY = os.environ.get("DATA_PURIFICATION_API_KEY", "")
    DATA_PURIFICATION_API_URL = "https://api.yourapi.cn/v1/chat/completions"
    DATA_PURIFICATION_BAK_MODEL = "gemini-2.5-pro"
    DATA_PURIFICATION_API_BAK_URL = "https://api.yourapi.cn/v1/chat/completions"
    DATA_PURIFICATION_API_BAK_KEY = os.environ.get("DATA_PURIFICATION_API_BAK_KEY", "")
    DATA_PURIFICATION_TIMEOUT = 15

    TOTAL_TIMEOUT = 60
    SAFETY_MARGIN = 2
    MAX_LOGS_HISTORY = 1000
    SNAPSHOT_DIR = "snapshots"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config(env: str = "development") -> Config:
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)()


config = Config()
