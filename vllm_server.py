# -*- coding: utf-8 -*-
# Copyright 2024.
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""
vLLM OpenAI兼容API服务
提供与OpenAI Chat Completions API兼容的接口
"""

import time
import uuid

import uvicorn
from fastapi import FastAPI, HTTPException
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from src.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ResponseMessage,
    UsageInfo
)


# ==============================================================================
# 模型配置
# ==============================================================================

# 基础模型路径
BASE_MODEL_PATH = "/root/autodl-tmp/base_models/Qwen2.5-7B-Instruct"

# LoRA适配器配置
LORA_ADAPTERS = {
    "classify": {
        "name": "classify",
        "path": "/root/autodl-tmp/v10/checkpoint600",
        "id": 1
    },
    "china": {
        "name": "china", 
        "path": "/root/autodl-tmp/lora_adapters/china",
        "id": 2
    }
}


# ==============================================================================
# 初始化模型
# ==============================================================================

print("正在初始化 vLLM 引擎...")

llm = LLM(
    model=BASE_MODEL_PATH,
    enable_lora=True,
    trust_remote_code=True,
)

# 注册LoRA适配器
lora_requests = {}
for name, config in LORA_ADAPTERS.items():
    lora_requests[name] = LoRARequest(
        lora_name=config["name"],
        lora_path=config["path"],
        lora_int_id=config["id"]
    )

print("vLLM 引擎初始化完成。")


# ==============================================================================
# FastAPI应用
# ==============================================================================

app = FastAPI(
    title="vLLM OpenAI-Compatible API",
    description="使用vLLM提供与OpenAI Chat Completions API兼容接口的服务",
    version="1.0.0"
)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    处理聊天补全请求，兼容OpenAI API格式
    
    - model='classify': 使用classify LoRA
    - model='china': 使用china LoRA  
    - 其他: 使用基础模型
    """
    if request.stream:
        raise HTTPException(status_code=400, detail="流式传输当前不受支持。")
    
    tokenizer = llm.get_tokenizer()
    
    try:
        prompt = tokenizer.apply_chat_template(
            conversation=[msg.dict() for msg in request.messages],
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"转换聊天模板时出错: {e}")
    
    # 选择LoRA适配器
    lora_request = lora_requests.get(request.model)
    
    if lora_request:
        print(f"请求命中LoRA规则: 使用LoRA '{lora_request.lora_name}'")
    else:
        print(f"请求的model ('{request.model}') 未匹配任何LoRA规则，使用基础模型。")
    
    # 生成回复
    sampling_params = SamplingParams(
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
    )
    
    outputs = llm.generate(prompt, sampling_params, lora_request=lora_request)
    output = outputs[0]
    
    response_content = output.outputs[0].text
    completion_tokens = len(output.outputs[0].token_ids)
    finish_reason = output.outputs[0].finish_reason
    prompt_tokens = len(output.prompt_token_ids)
    
    # 构建响应
    response_message = ResponseMessage(role="assistant", content=response_content)
    choice = ChatCompletionChoice(index=0, message=response_message, finish_reason=finish_reason)
    usage = UsageInfo(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    
    return ChatCompletionResponse(model=request.model, choices=[choice], usage=usage)


@app.get("/")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "vLLM API"}


# ==============================================================================
# 启动服务
# ==============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6007)
