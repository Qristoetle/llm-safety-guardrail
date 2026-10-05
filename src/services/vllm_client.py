# -*- coding: utf-8 -*-
"""
vLLM API客户端
"""

import json
import time
import logging
from typing import Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter

from ..config import config

logger = logging.getLogger("ai_security")


class VLLMClient:
    """vLLM API客户端"""
    
    def __init__(self):
        """初始化客户端"""
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({'Connection': 'close'})
        
        self.base_url = config.VLLM_BASE_URL
        self.api_url = f"{self.base_url}/v1/chat/completions"
    
    def close(self):
        """关闭客户端连接"""
        self.session.close()
    
    def generate(
        self,
        prompt: str,
        lora: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        调用vLLM API生成回复
        
        Args:
            prompt: 用户提示词
            lora: LoRA适配器名称
            system_prompt: 系统提示词
            
        Returns:
            生成的文本内容
        """
        model_to_use = lora or "default"
        
        logger.info(
            f"调用vLLM API - model: {model_to_use}, "
            f"系统提示词长度: {len(system_prompt or '')}, "
            f"用户提示词长度: {len(prompt)}"
        )
        
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": prompt}
            ]
        }
        
        headers = {"Content-Type": "application/json"}
        
        # 重试配置
        max_retries = 1
        retry_delay = 0.3
        max_total_time = 50
        single_request_timeout = 25
        
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            elapsed_time = time.time() - start_time
            
            if elapsed_time >= max_total_time:
                logger.error(f"vLLM API调用已超过总时间限制 {max_total_time}秒")
                raise TimeoutError(f"vLLM服务调用超时（总时间超过{max_total_time}秒）")
            
            try:
                if attempt > 0:
                    logger.info(f"vLLM API重试 {attempt}/{max_retries}")
                
                response = self.session.post(
                    self.api_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=min(max_total_time - elapsed_time, single_request_timeout)
                )
                
                try:
                    response.raise_for_status()
                    response_data = response.json()
                    content = response_data["choices"][0]["message"]["content"]
                finally:
                    response.close()
                
                total_time = time.time() - start_time
                logger.info(f"vLLM API调用成功 - 耗时: {total_time:.2f}秒")
                return content
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"vLLM API超时 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries and (time.time() - start_time) < max_total_time:
                    time.sleep(retry_delay)
                else:
                    raise TimeoutError(f"vLLM服务响应超时: {e}")
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"vLLM API连接失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries and (time.time() - start_time) < max_total_time:
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(f"vLLM服务连接失败: {e}")
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') else 500
                logger.error(f"vLLM API返回HTTP错误 {status_code}: {e}")
                
                if status_code >= 500 and attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"vLLM服务返回错误({status_code}): {e}")
                    
            except Exception as e:
                logger.error(f"vLLM API调用未知错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"vLLM服务调用失败: {e}")
        
        raise RuntimeError("vLLM服务调用失败")


# 全局客户端实例
vllm_client = VLLMClient()
