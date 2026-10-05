# -*- coding: utf-8 -*-
"""
Pydantic 数据模型定义
"""

import time
import uuid
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field


# ============== 聊天相关模型 ==============

class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    user_id: Optional[str] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


# ============== OpenAI兼容API模型 ==============

class ChatCompletionRequest(BaseModel):
    """OpenAI格式的聊天完成请求"""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False


class UsageInfo(BaseModel):
    """Token使用信息"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ResponseMessage(BaseModel):
    """响应消息"""
    role: Literal["assistant"]
    content: str


class ChatCompletionChoice(BaseModel):
    """聊天完成选项"""
    index: int
    message: ResponseMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponse(BaseModel):
    """OpenAI格式的聊天完成响应"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo


# ============== 安全检查模型 ==============

class SecurityCheckResult(BaseModel):
    """安全检查结果"""
    module: str
    passed: bool
    details: Dict[str, Any]
    reason: Optional[str] = None


class SecurityCheckResponse(BaseModel):
    """安全检查响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


# ============== 日志快照模型 ==============

class SnapshotRequest(BaseModel):
    """快照请求"""
    name: str
