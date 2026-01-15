"""
The Last 5% - Base Agent
Agent 基类
"""

from abc import ABC, abstractmethod
from typing import Any
import httpx
from openai import AsyncOpenAI
from backend.config import get_settings


class BaseAgent(ABC):
    """所有 Agent 的基类"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # 根据配置选择 LLM 提供商
        if self.settings.llm_provider == "deepseek" and self.settings.deepseek_api_key:
            # DeepSeek API (兼容 OpenAI SDK)
            self.client = AsyncOpenAI(
                api_key=self.settings.deepseek_api_key,
                base_url="https://api.deepseek.com"
            )
            self.model = "deepseek-chat"  # DeepSeek-V3
        elif self.settings.openai_api_key:
            # OpenAI API
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            self.model = "gpt-4o"
        else:
            self.client = None
            self.model = None
            
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 描述"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务"""
        pass
    
    async def call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """调用 LLM (支持 DeepSeek 和 OpenAI)"""
        if not self.client or not self.model:
            # 如果没有配置 API Key，返回模拟数据
            return self._get_mock_response()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return self._get_mock_response()
    
    def _get_mock_response(self) -> str:
        """返回模拟响应（用于演示）"""
        return "{}"
    
    async def close(self):
        """关闭资源"""
        await self.http_client.aclose()
