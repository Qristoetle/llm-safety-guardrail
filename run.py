#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI安全审查系统 - 生产环境启动脚本
"""

import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.config import config


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 启动AI安全审查系统后端服务 (生产模式)")
    print("=" * 50)
    print(f"🌐 地址: http://{config.HOST}:{config.PORT}")
    print(f"🤖 vLLM服务: {config.VLLM_BASE_URL}")
    print("=" * 50)
    
    uvicorn.run(
        "src.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info",
        limit_concurrency=100,
        limit_max_requests=1000,
        timeout_keep_alive=5,
        workers=1,
        access_log=True
    )


if __name__ == "__main__":
    main()
