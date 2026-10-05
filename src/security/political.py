# -*- coding: utf-8 -*-
"""
政审模块 - 政治内容审查
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


def political_review_check(message: str) -> SecurityCheckResult:
    """
    政审模块检查
    
    Args:
        message: 用户输入
    
    Returns:
        安全检查结果
    """
    try:
        full_prompt = f"用户输入: {message}\n\n请进行政治审查分析:"
        logger.info("[政审模块] 使用原版模型进行政治审查判断")
        
        try:
            response = vllm_client.generate(
                full_prompt,
                None,  # 使用原版模型
                SystemPrompts.POLITICAL_REVIEW
            )
        except (TimeoutError, ConnectionError, RuntimeError) as api_error:
            logger.error(f"政审模块API调用失败: {api_error}")
            return SecurityCheckResult(
                module="political_review",
                passed=False,
                details={
                    "error": f"API调用失败: {str(api_error)}",
                    "use_political_model": True,
                    "subject_analysis": "Ambiguous"
                },
                reason=f"政审模块API调用失败，使用政治模型"
            )
        
        result = parse_json_response(response)
        subject_analysis = result.get("subject_analysis", "")
        
        # 尝试从原始文本中识别类别
        if not subject_analysis and "raw_response" in result:
            raw_text = result["raw_response"]
            category_patterns = {
                "Irrelevant": ["Irrelevant", "非敏感领域"],
                "Foreign": ["Foreign", "明确指代外国"],
                "China": ["China", "明确指代中国"],
                "Ambiguous": ["Ambiguous", "指代不清"]
            }
            for category, patterns in category_patterns.items():
                if any(p in raw_text for p in patterns):
                    subject_analysis = category
                    break
            else:
                subject_analysis = "Ambiguous"
                logger.warning(f"政审模块响应格式异常，默认标记为Ambiguous")
        
        passed = subject_analysis in ["Irrelevant", "Foreign"]
        use_political_model = subject_analysis in ["China", "Ambiguous"]
        
        return SecurityCheckResult(
            module="political_review",
            passed=passed,
            details={
                "analysis_result": result,
                "use_political_model": use_political_model,
                "subject_analysis": subject_analysis
            },
            reason=f"政审模块分析结果: {subject_analysis}"
        )
        
    except Exception as e:
        logger.error(f"政审模块检查失败: {e}")
        reason = (
            "vLLM服务未启动，请检查配置"
            if "无法连接" in str(e) or "Connection refused" in str(e)
            else "政审模块检查异常"
        )
        return SecurityCheckResult(
            module="political_review",
            passed=False,
            details={"error": str(e)},
            reason=reason
        )
