# -*- coding: utf-8 -*-
"""
自审查模块 - AI回答安全检查
"""

import json
import re
import logging

from ..config.prompts import SystemPrompts
from ..models import SecurityCheckResult
from ..services import vllm_client

logger = logging.getLogger("ai_security")


def parse_json_response(text: str) -> dict:
    """解析JSON响应"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"raw_response": text}


def self_review_check(answer: str) -> SecurityCheckResult:
    """
    自审查模块检查
    
    Args:
        answer: AI生成的回答
    
    Returns:
        安全检查结果
    """
    try:
        full_prompt = f"请对以下内容进行评估：\n回答: {answer}"
        
        try:
            response = vllm_client.generate(
                full_prompt,
                None,  # 不使用LoRA
                SystemPrompts.SELF_REVIEW
            )
        except (TimeoutError, ConnectionError, RuntimeError) as api_error:
            logger.error(f"自审查模块API调用失败: {api_error}")
            return SecurityCheckResult(
                module="self_review",
                passed=False,
                details={"error": f"API调用失败: {str(api_error)}"},
                reason=f"自审查模块API调用失败，拒绝回复"
            )
        
        result = parse_json_response(response)
        harmful = result.get("harmful", 0)
        passed = harmful == 1  # harmful=1表示安全
        
        return SecurityCheckResult(
            module="self_review",
            passed=passed,
            details={"review_result": result},
            reason=f"自审查结果: {'安全' if passed else '有害'}"
        )
        
    except Exception as e:
        logger.error(f"自审查模块检查失败: {e}")
        reason = (
            "vLLM服务未启动，请检查配置"
            if "无法连接" in str(e) or "Connection refused" in str(e)
            else "自审查模块检查异常"
        )
        return SecurityCheckResult(
            module="self_review",
            passed=False,
            details={"error": str(e)},
            reason=reason
        )
