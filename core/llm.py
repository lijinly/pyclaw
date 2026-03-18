"""
LLM 集成模块 —— 支持 OpenAI 兼容接口的异步调用
可替换为任何兼容 OpenAI API 的服务（如 DeepSeek、通义千问等）
"""
import asyncio
import json
import os
from typing import AsyncGenerator, Optional

import aiohttp


class LLMConfig:
    """LLM 配置"""
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens


class LLMClient:
    """异步 LLM 客户端"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        发送对话请求，返回完整回复文本。
        """
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": payload_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话，逐 token yield 文本片段。
        """
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": payload_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for raw_line in resp.content:
                    line = raw_line.decode("utf-8").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
