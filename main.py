#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI安全审查系统 - 主入口
"""

import uvicorn
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config import config


def main():
    """主函数"""
    env = os.getenv("ENVIRONMENT", "development")
    
    print("=" * 50)
    print("🚀 启动AI安全审查系统后端服务")
    print("=" * 50)
    print(f"📊 环境: {env}")
    print(f"🌐 地址: http://{config.HOST}:{config.PORT}")
    print(f"🔧 调试模式: {config.DEBUG}")
    print(f"🤖 vLLM服务: {config.VLLM_BASE_URL}")
    print("=" * 50)
    
    uvicorn.run(
        "src.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
