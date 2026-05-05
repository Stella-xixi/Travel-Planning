"""
pydantic Settings 模块
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # Agent 配置
    agent_name: str = "TravelAssistantAgent"
    agent_max_steps: int = 10
    agent_max_reasoning_depth: int = 5

    # LLM 配置
    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # 记忆配置
    memory_max_working: int = 10
    memory_max_long_term: int = 50

    # gRPC 配置
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051

    # Web 配置
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    web_debug: bool = True

    class Config:
        env_prefix = "SHUAI_TRAVEL_"
