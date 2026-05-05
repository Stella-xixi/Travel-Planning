"""
配置管理模块 (Configuration Manager)
支持 JSON 和 YAML 配置文件格式
"""

import json
import os
import re
import yaml
from typing import Dict, Any, List, Optional


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/llm_config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.models_config: Dict[str, Dict[str, Any]] = {}
        self.default_model_id: str = "gpt-4o-mini"

        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件，支持 YAML 和 JSON 格式"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file missing: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换环境变量占位符 ${VAR_NAME}
        content = self._replace_env_vars(content)

        if self.config_path.endswith(('.yaml', '.yml')):
            self.config = yaml.safe_load(content)
        else:
            self.config = json.loads(content)

        # 加载模型配置
        self.models_config = self.config.get('models', {})
        self.default_model_id = self.config.get('default_model', 'gpt-4o-mini')

    def _replace_env_vars(self, content: str) -> str:
        """替换环境变量占位符 ${VAR_NAME}"""
        pattern = r'\$\{([^}]+)\}'

        def replace(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name, '')
            return env_value if env_value else match.group(0)

        return re.sub(pattern, replace, content)

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持嵌套键如 'web.port'"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_city_info(self, city_name: str) -> Optional[Dict[str, Any]]:
        """获取城市信息"""
        return self.config.get('travel_knowledge', {}).get('cities', {}).get(city_name)

    def get_all_cities(self) -> List[str]:
        """获取所有城市列表"""
        return list(self.config.get('travel_knowledge', {}).get('cities', {}).keys())

    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        models = []
        for model_id, config in self.models_config.items():
            provider_type = config.get('provider', 'openai')
            model_name = config.get('model', model_id)
            display_name = config.get('name', model_id)
            models.append({
                'model_id': model_id,
                'name': display_name,
                'provider': provider_type,
                'model': model_name
            })
        return models

    def get_model_config(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """获取模型配置"""
        if model_id is None:
            model_id = self.default_model_id

        if model_id not in self.models_config:
            raise ValueError(f"模型不存在: {model_id}")

        return self.models_config[model_id]

    def get_default_model_id(self) -> str:
        """获取默认模型ID"""
        return self.default_model_id

    def get_default_model_config(self) -> Dict[str, Any]:
        """获取默认模型配置"""
        return self.get_model_config(self.default_model_id)

    @property
    def agent_config(self) -> Dict[str, Any]:
        """获取 Agent 配置"""
        return self.config.get('agent', {})

    @property
    def web_config(self) -> Dict[str, Any]:
        """获取 Web 服务配置"""
        return self.config.get('web', {})

    @property
    def grpc_config(self) -> Dict[str, Any]:
        """获取 gRPC 服务配置"""
        return self.config.get('grpc', {})
