# -*- coding: utf-8 -*-
"""
健康检查路由
"""

import os
import json
import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..config import config
from ..services.vllm_client import vllm_client

router = APIRouter()
logger = logging.getLogger("ai_security")


@router.get("/")
async def root():
    """根路径 - 返回日志查看器页面"""
    try:
        log_viewer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "static", "log_viewer.html")
        with open(log_viewer_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"读取日志查看器页面失败: {e}")
        return {"message": "AI安全审查系统后端服务运行中", "version": "2.0.0"}


@router.get("/api")
async def api_root():
    """API根路径"""
    return {"message": "AI安全审查系统后端服务运行中", "version": "2.0.0"}


@router.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        test_payload = {
            "model": "classify",
            "messages": [{"role": "user", "content": "健康检查"}]
        }
        
        import requests
        response = requests.post(
            f"{config.VLLM_BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_payload),
            timeout=5
        )
        vllm_status = "healthy" if response.status_code == 200 else "unhealthy"
        response.close()
    except Exception as e:
        vllm_status = "unreachable"
        logger.warning(f"vLLM服务连接失败: {e}")
    
    return {
        "status": "healthy",
        "vllm_service": vllm_status,
        "vllm_base_url": config.VLLM_BASE_URL,
        "vllm_endpoint": f"{config.VLLM_BASE_URL}/v1/chat/completions",
        "modules": ["doorkeeper", "political_review", "sensitive_words", "response", "self_review", "data_purification"]
    }
