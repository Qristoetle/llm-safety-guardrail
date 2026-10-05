# -*- coding: utf-8 -*-
"""
敏感词模块 - 敏感词检测
"""

import sys
import os
import logging

from ..models import SecurityCheckResult

logger = logging.getLogger("ai_security")

# 添加敏感词模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'program', 'sensitive'))

# 导入敏感词检测模块
try:
    from sensitive_optimized import detect_sensitive_words_summary
except ImportError:
    def detect_sensitive_words_summary(text):
        return {}


def sensitive_words_check(message: str) -> SecurityCheckResult:
    """
    敏感词模块检查
    
    Args:
        message: 用户输入
    
    Returns:
        安全检查结果
    """
    try:
        summary = detect_sensitive_words_summary(message)
        passed = len(summary) == 0
        sensitive_words = list(summary.keys())
        
        warning_message = ""
        if sensitive_words:
            warning_message = f"请注意，下面这段话中出现了这些敏感词{sensitive_words}，请注意回答的合理合法性:"
        
        return SecurityCheckResult(
            module="sensitive_words",
            passed=passed,
            details={
                "sensitive_words": sensitive_words,
                "summary": summary,
                "warning_message": warning_message
            },
            reason=f"检测到{len(sensitive_words)}个敏感词" if sensitive_words else "未检测到敏感词"
        )
        
    except Exception as e:
        logger.error(f"敏感词模块检查失败: {e}")
        return SecurityCheckResult(
            module="sensitive_words",
            passed=False,
            details={"error": str(e)},
            reason="敏感词模块检查异常"
        )
