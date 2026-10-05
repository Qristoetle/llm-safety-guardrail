# -*- coding: utf-8 -*-
"""
聊天路由
"""

import time
import logging
from typing import Optional

from fastapi import APIRouter, Body

from ..config import config
from ..config.responses import RefuseResponses
from ..models import ChatResponse, SecurityCheckResult
from ..services.vllm_client import vllm_client
from ..services.purification import purification_service
from ..security import (
    doorkeeper_check,
    political_review_check,
    sensitive_words_check,
    self_review_check
)
from ..utils.logs import execution_logs_history, MAX_LOGS_HISTORY, save_logs_to_file

router = APIRouter()
logger = logging.getLogger("ai_security")

# 超时配置
TOTAL_TIMEOUT = config.TOTAL_TIMEOUT
SAFETY_MARGIN = config.SAFETY_MARGIN


@router.post("/chat")
async def chat_endpoint(
    text: str = Body(..., embed=True),
    user_id: Optional[str] = None,
    model: Optional[str] = None
):
    """
    完整的AI对话接口
    """
    total_start_time = time.time()
    execution_log = {
        "user_id": user_id or "anonymous",
        "input": text,
        "modules": [],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    
    def check_timeout():
        return time.time() - total_start_time >= (TOTAL_TIMEOUT - SAFETY_MARGIN)
    
    def handle_timeout():
        execution_log["total_time"] = f"{time.time() - total_start_time:.3f}秒"
        execution_log["final_status"] = "总超时拦截"
        execution_log["refuse_answer"] = RefuseResponses.DEFAULT
        _save_log(execution_log)
        return {"success": False, "message": "请求处理超时", "data": RefuseResponses.DEFAULT}
    
    try:
        message = text
        user_id_value = user_id or "anonymous"
        
        # 1. 门卫模块检查
        if check_timeout():
            return handle_timeout()
        
        doorkeeper_start = time.time()
        logger.info("[工作流] 开始门卫模块检查")
        doorkeeper_result = doorkeeper_check(message)
        doorkeeper_time = time.time() - doorkeeper_start
        
        logger.info(f"[门卫模块] 检查完成 - {doorkeeper_result.reason}，耗时: {doorkeeper_time:.3f}秒")
        execution_log["modules"].append(_format_module_log("门卫模块", doorkeeper_result, doorkeeper_time))
        
        if not doorkeeper_result.passed:
            execution_log["total_time"] = f"{time.time() - total_start_time:.3f}秒"
            execution_log["final_status"] = "被门卫模块拒绝"
            execution_log["refuse_answer"] = RefuseResponses.DEFAULT
            _save_log(execution_log)
            logger.warning(f"[会话结束] 被门卫模块拒绝 - 用户: {user_id_value}")
            return {"success": False, "message": "内容被门卫模块拒绝", "data": RefuseResponses.DEFAULT}
        
        # 2. 政审模块检查
        if check_timeout():
            return handle_timeout()
        
        political_start = time.time()
        logger.info("[工作流] 开始政审模块检查")
        political_result = political_review_check(message)
        political_time = time.time() - political_start
        
        logger.info(f"[政审模块] 检查结果: {'通过' if political_result.passed else '拒绝'}，耗时: {political_time:.3f}秒")
        execution_log["modules"].append(_format_module_log("政审模块", political_result, political_time))
        
        # 3. 敏感词模块检查
        if check_timeout():
            return handle_timeout()
        
        sensitive_start = time.time()
        logger.info("[工作流] 开始敏感词模块检查")
        sensitive_result = sensitive_words_check(message)
        sensitive_time = time.time() - sensitive_start
        
        logger.info(f"[敏感词模块] 检查结果，耗时: {sensitive_time:.3f}秒")
        execution_log["modules"].append(_format_module_log("敏感词模块", sensitive_result, sensitive_time))
        
        # 4. 构建最终用户输入
        final_user_input = message
        warning_message = sensitive_result.details.get("warning_message", "")
        if warning_message:
            final_user_input = warning_message + "\n" + message
        
        # 5. 生成回答
        if check_timeout():
            return handle_timeout()
        
        answer_start_time = time.time()
        logger.info("[工作流] 开始生成回答")
        
        use_political_model = political_result.details.get("use_political_model", False)
        if model:
            lora_to_use = config.LORA_ADAPTERS.get(model, model)
        else:
            lora_to_use = config.LORA_ADAPTERS.get("china") if use_political_model else None
        
        try:
            answer = vllm_client.generate(final_user_input, lora=lora_to_use)
        except (TimeoutError, ConnectionError, RuntimeError) as api_error:
            answer_time = time.time() - answer_start_time
            logger.error(f"[生成回答] API调用失败: {api_error}")
            execution_log["modules"].append({
                "name": "回复模块",
                "status": "失败",
                "time": f"{answer_time:.3f}秒",
                "details": {"error": str(api_error)},
                "reason": f"API调用失败"
            })
            execution_log["total_time"] = f"{time.time() - total_start_time:.3f}秒"
            execution_log["final_status"] = "API调用失败"
            execution_log["refuse_answer"] = RefuseResponses.DEFAULT
            _save_log(execution_log)
            return {"success": False, "message": "生成回答失败", "data": RefuseResponses.DEFAULT}
        
        answer_time = time.time() - answer_start_time
        logger.info(f"[生成回答] 回答长度: {len(answer)}，耗时: {answer_time:.3f}秒")
        
        execution_log["modules"].append({
            "name": "回复模块",
            "status": "完成",
            "time": f"{answer_time:.3f}秒",
            "details": {
                "model_used": model or ("china" if use_political_model else "原版"),
                "answer_length": len(answer)
            },
            "reason": f"使用{'政治版模型' if use_political_model else '原版模型'}生成回答"
        })
        
        # 6. 自审查模块检查
        if check_timeout():
            return handle_timeout()
        
        self_review_start_time = time.time()
        logger.info("[工作流] 开始自审查模块检查")
        self_review_result = self_review_check(answer)
        self_review_time = time.time() - self_review_start_time
        
        logger.info(f"[自审查模块] 检查结果: {'通过' if self_review_result.passed else '拒绝'}，耗时: {self_review_time:.3f}秒")
        execution_log["modules"].append(_format_module_log("自审查模块", self_review_result, self_review_time))
        
        if not self_review_result.passed:
            execution_log["total_time"] = f"{time.time() - total_start_time:.3f}秒"
            execution_log["final_status"] = "被自审查模块拒绝"
            execution_log["rejected_answer"] = answer
            execution_log["refuse_answer"] = RefuseResponses.DEFAULT
            _save_log(execution_log)
            logger.warning(f"[会话结束] AI回答被自审查模块拒绝")
            return {"success": False, "message": "AI回答被自审查模块拒绝", "data": RefuseResponses.DEFAULT}
        
        # 7. 数据净化模块处理
        if check_timeout():
            return handle_timeout()
        
        purification_start_time = time.time()
        logger.info("[工作流] 开始数据净化模块处理")
        purification_result = purification_service.purify(answer)
        purification_time = time.time() - purification_start_time
        
        final_answer = purification_result.details.get("purified_answer", answer)
        is_changed = purification_result.details.get("is_changed", False)
        
        logger.info(f"[数据净化模块] 处理完成，耗时: {purification_time:.3f}秒，是否有变化: {is_changed}")
        execution_log["modules"].append(_format_module_log("数据净化模块", purification_result, purification_time))
        
        # 所有检查通过，返回成功响应
        total_time = time.time() - total_start_time
        execution_log["total_time"] = f"{total_time:.3f}秒"
        execution_log["final_status"] = "成功"
        execution_log["answer"] = final_answer
        if final_answer != answer:
            execution_log["original_answer"] = answer
        
        _save_log(execution_log)
        logger.info(f"[会话结束] 处理成功 - 用户: {user_id_value}，总耗时: {total_time:.3f}秒")
        return {"success": True, "message": "处理成功", "data": final_answer}
        
    except Exception as e:
        total_time = time.time() - total_start_time
        logger.error(f"[会话结束] 处理聊天请求时出错: {e}")
        execution_log["total_time"] = f"{total_time:.3f}秒"
        execution_log["final_status"] = "错误"
        execution_log["error"] = str(e)
        execution_log["refuse_answer"] = RefuseResponses.DEFAULT
        _save_log(execution_log)
        return {"success": False, "message": "处理请求时发生错误", "data": RefuseResponses.DEFAULT}


@router.post("/v1/chat")
async def v1_chat_endpoint(
    text: str = Body(..., embed=True),
    user_id: Optional[str] = None,
    model: Optional[str] = None
):
    """简化版AI对话接口 - 只返回 {"data": "回答内容"}"""
    try:
        result = await chat_endpoint(text=text, user_id=user_id, model=model)
        if isinstance(result, dict):
            data = result.get("data")
            return {"data": data or RefuseResponses.DEFAULT}
        return {"data": RefuseResponses.DEFAULT}
    except Exception as e:
        logger.error(f"[/v1/chat] 处理请求时出错: {e}")
        return {"data": "抱歉，服务暂时不可用，请稍后再试"}


@router.post("/chat/plain")
async def chat_plain(
    text: str = Body(...),
    user_id: Optional[str] = None,
    model: Optional[str] = None
):
    """处理纯文本输入的聊天接口"""
    return await chat_endpoint(text=text, user_id=user_id, model=model)


def _format_module_log(name: str, result: SecurityCheckResult, duration: float) -> dict:
    """格式化模块日志"""
    return {
        "name": name,
        "status": "通过" if result.passed else "拒绝",
        "time": f"{duration:.3f}秒",
        "details": result.details,
        "reason": result.reason
    }


def _save_log(execution_log: dict):
    """保存执行日志"""
    execution_logs_history.append(execution_log.copy())
    if len(execution_logs_history) > MAX_LOGS_HISTORY:
        execution_logs_history.pop(0)
    save_logs_to_file()
