"""
The Last 5% - Configuration Management
配置管理模块
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = "sk-9b672e99df8b4a6a84f7e1b67941f672"  # DeepSeek API
    firecrawl_api_key: str = ""
    
    # LLM Provider: "deepseek" or "openai"
    llm_provider: str = "deepseek"
    
    # Server Config
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Agent Config
    max_reviews_to_analyze: int = 100
    review_sources: list[str] = [
        "smzdm",      # 什么值得买
        "zhihu",      # 知乎
        "bilibili",   # B站
        "v2ex",       # V2EX
        "jd",         # 京东
        "taobao",     # 淘宝
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
