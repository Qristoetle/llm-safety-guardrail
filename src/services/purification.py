# -*- coding: utf-8 -*-
"""
数据净化服务
"""

import logging
from typing import Optional

import requests

from ..config import config
from ..config.prompts import SystemPrompts
from ..models import SecurityCheckResult

logger = logging.getLogger("ai_security")


class DataPurificationService:
    """数据净化服务"""
    
    def __init__(self):
        """初始化服务"""
        self.api_url = config.DATA_PURIFICATION_API_URL
        self.api_key = config.DATA_PURIFICATION_API_KEY
        self.model = config.DATA_PURIFICATION_MODEL
        self.timeout = 5
        self.max_retries = 1
    
    def purify(self, answer: str) -> SecurityCheckResult:
        """
        对回答进行净化处理
        
        Args:
            answer: 原始回答
            
        Returns:
            净化结果
        """
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"[数据净化模块] 第 {attempt} 次重试")
                
                prompt = SystemPrompts.DATA_PURIFICATION.format(answer=answer)
                
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4096
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                purified_answer = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                
                if not purified_answer:
                    logger.warning("[数据净化模块] 未能获取有效的净化结果")
                    purified_answer = answer
                
                is_changed = purified_answer != answer
                
                return SecurityCheckResult(
                    module="data_purification",
                    passed=True,
                    details={
                        "purified_answer": purified_answer,
                        "original_answer": answer if is_changed else None,
                        "is_changed": is_changed,
                        "model_used": self.model,
                        "attempts": attempt + 1
                    },
                    reason=f"数据净化完成，内容{'已优化' if is_changed else '无需修改'}"
                )
                
            except requests.exceptions.Timeout:
                logger.warning(f"[数据净化模块] 请求超时 (尝试 {attempt + 1})")
                if attempt >= self.max_retries:
                    return self._fallback_result(answer, f"请求超时（已重试{self.max_retries}次）")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[数据净化模块] 请求失败: {e}")
                if attempt >= self.max_retries:
                    return self._fallback_result(answer, f"请求失败: {str(e)}")
                    
            except Exception as e:
                logger.error(f"[数据净化模块] 处理异常: {e}")
                if attempt >= self.max_retries:
                    return self._fallback_result(answer, f"处理异常: {str(e)}")
        
        return self._fallback_result(answer, "未知错误")
    
    def _fallback_result(self, answer: str, error: str) -> SecurityCheckResult:
        """返回降级结果"""
        return SecurityCheckResult(
            module="data_purification",
            passed=True,
            details={
                "purified_answer": answer,
                "error": error,
                "is_changed": False
            },
            reason=f"数据净化失败，返回原始回答"
        )


# 全局服务实例
purification_service = DataPurificationService()
