# -*- coding: utf-8 -*-
"""
AI安全审查系统 - 应用入口
"""

import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import config
from .config.responses import RefuseResponses
from .routes import chat_router, logs_router, health_router
from .services.vllm_client import vllm_client
from .utils.logs import setup_logger

# 设置日志
logger = setup_logger()

# 创建FastAPI应用
app = FastAPI(
    title="AI安全审查系统",
    description="集成门卫、政审、敏感词、自审查等核心安全模块的AI对话系统",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)


# 添加请求超时中间件
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """请求超时中间件 - 防止请求处理时间过长"""
    try:
        return await asyncio.wait_for(call_next(request), timeout=55.0)
    except asyncio.TimeoutError:
        logger.error(f"[中间件] 请求超时（55秒） - URL: {request.url}")
        
        if request.url.path == "/v1/chat":
            return JSONResponse(
                status_code=200,
                content={"data": RefuseResponses.DEFAULT}
            )
        else:
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "请求处理超时", "data": RefuseResponses.DEFAULT}
            )


# 添加应用生命周期事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在关闭应用,清理连接...")
    vllm_client.close()
    logger.info("连接已关闭")


# 注册路由
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(logs_router)
