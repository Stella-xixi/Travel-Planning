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
        self.travel_knowledge: Dict[str, Any] = {}

        self._check_config_files()
        self._load_config()
        self._init_travel_knowledge()

    def _check_config_files(self) -> None:
        # 优先查找 YAML 文件
        yaml_path = self.config_path
        json_path = self.config_path.replace('.yaml', '.json').replace('.yml', '.json')

        # 如果指定的是 yaml 文件但不存在，尝试 json
        if self.config_path.endswith(('.yaml', '.yml')) and not os.path.exists(yaml_path):
            if os.path.exists(json_path):
                self.config_path = json_path
                return

        if not os.path.exists(self.config_path):
            error_msg = (
                f"Configuration file missing: {self.config_path}\n\n"
                f"Please create configuration file before starting the application:\n"
                f"  1. Copy config/llm_config.yaml.example to config/llm_config.yaml\n"
                f"  2. Update the API keys in the configuration\n\n"
                f"Refer to README.md for detailed instructions."
            )
            raise FileNotFoundError(error_msg)

    def _load_config(self) -> None:
        """加载配置文件，支持 YAML 和 JSON 格式"""
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

        # 检查是否有模型配置
        if not self.models_config:
            raise ValueError(
                f"No models configured in {self.config_path}\n"
                f"Please add at least one model configuration."
            )

    def _replace_env_vars(self, content: str) -> str:
        """替换环境变量占位符 ${VAR_NAME}"""
        pattern = r'\$\{([^}]+)\}'

        def replace(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name, '')
            return env_value if env_value else match.group(0)

        return re.sub(pattern, replace, content)

    def _init_travel_knowledge(self) -> None:
        """初始化旅游知识数据"""
        self.travel_knowledge = {
            "cities": {
                "北京": {
                    "region": "华北",
                    "tags": ["历史文化", "首都", "古建筑"],
                    "best_season": ["春季", "秋季"],
                    "avg_budget_per_day": 500,
                    "recommended_days": 4,
                    "attractions": [
                        {"name": "故宫", "type": "历史遗迹", "duration": 4, "ticket": 60},
                        {"name": "长城", "type": "历史遗迹", "duration": 6, "ticket": 40},
                        {"name": "天坛", "type": "历史遗迹", "duration": 3, "ticket": 15},
                        {"name": "颐和园", "type": "园林", "duration": 4, "ticket": 30}
                    ]
                },
                "上海": {
                    "region": "华东",
                    "tags": ["现代都市", "购物", "美食"],
                    "best_season": ["春季", "秋季"],
                    "avg_budget_per_day": 600,
                    "recommended_days": 3,
                    "attractions": [
                        {"name": "外滩", "type": "城市景观", "duration": 3, "ticket": 0},
                        {"name": "东方明珠", "type": "地标建筑", "duration": 2, "ticket": 180},
                        {"name": "迪士尼乐园", "type": "主题乐园", "duration": 8, "ticket": 399},
                        {"name": "豫园", "type": "园林", "duration": 2, "ticket": 40}
                    ]
                },
                "杭州": {
                    "region": "华东",
                    "tags": ["自然风光", "人文历史", "休闲"],
                    "best_season": ["春季", "秋季"],
                    "avg_budget_per_day": 400,
                    "recommended_days": 3,
                    "attractions": [
                        {"name": "西湖", "type": "自然风光", "duration": 4, "ticket": 0},
                        {"name": "灵隐寺", "type": "宗教文化", "duration": 3, "ticket": 45},
                        {"name": "千岛湖", "type": "自然风光", "duration": 6, "ticket": 150},
                        {"name": "宋城", "type": "主题乐园", "duration": 4, "ticket": 310}
                    ]
                },
                "成都": {
                    "region": "西南",
                    "tags": ["美食", "休闲", "熊猫"],
                    "best_season": ["春季", "秋季"],
                    "avg_budget_per_day": 350,
                    "recommended_days": 4,
                    "attractions": [
                        {"name": "大熊猫繁育研究基地", "type": "动物园", "duration": 4, "ticket": 55},
                        {"name": "宽窄巷子", "type": "历史街区", "duration": 3, "ticket": 0},
                        {"name": "武侯祠", "type": "历史遗迹", "duration": 2, "ticket": 50},
                        {"name": "都江堰", "type": "历史遗迹", "duration": 5, "ticket": 80}
                    ]
                },
                "西安": {
                    "region": "西北",
                    "tags": ["历史文化", "古都", "美食"],
                    "best_season": ["春季", "秋季"],
                    "avg_budget_per_day": 400,
                    "recommended_days": 4,
                    "attractions": [
                        {"name": "兵马俑", "type": "历史遗迹", "duration": 4, "ticket": 120},
                        {"name": "大雁塔", "type": "历史遗迹", "duration": 2, "ticket": 50},
                        {"name": "古城墙", "type": "历史遗迹", "duration": 3, "ticket": 54},
                        {"name": "华清宫", "type": "历史遗迹", "duration": 3, "ticket": 120}
                    ]
                },
                "厦门": {
                    "region": "华南",
                    "tags": ["海滨", "休闲", "文艺"],
                    "best_season": ["春季", "秋季", "冬季"],
                    "avg_budget_per_day": 450,
                    "recommended_days": 3,
                    "attractions": [
                        {"name": "鼓浪屿", "type": "海岛", "duration": 6, "ticket": 0},
                        {"name": "南普陀寺", "type": "宗教文化", "duration": 2, "ticket": 0},
                        {"name": "曾厝垵", "type": "历史街区", "duration": 3, "ticket": 0},
                        {"name": "环岛路", "type": "城市景观", "duration": 3, "ticket": 0}
                    ]
                },
                "呼和浩特": {
                    "region": "内蒙古",
                    "tags": ["草原", "历史文化", "美食", "民族风情"],
                    "best_season": ["夏季", "秋季"],
                    "avg_budget_per_day": 350,
                    "recommended_days": 3,
                    "attractions": [
                        {"name": "大召寺", "type": "宗教文化", "duration": 2, "ticket": 35},
                        {"name": "内蒙古博物馆", "type": "博物馆", "duration": 2, "ticket": 0},
                        {"name": "昭君墓", "type": "历史遗迹", "duration": 2, "ticket": 65},
                        {"name": "敕勒川草原", "type": "自然风光", "duration": 4, "ticket": 0}
                    ]
                },
                "呼伦贝尔": {
                    "region": "内蒙古",
                    "tags": ["草原", "自然风光", "民族风情", "美食"],
                    "best_season": ["夏季", "秋季"],
                    "avg_budget_per_day": 450,
                    "recommended_days": 4,
                    "attractions": [
                        {"name": "呼伦贝尔大草原", "type": "自然风光", "duration": 6, "ticket": 0},
                        {"name": "额尔古纳湿地", "type": "自然风光", "duration": 4, "ticket": 65},
                        {"name": "满洲里国门", "type": "历史遗迹", "duration": 2, "ticket": 80},
                        {"name": "套娃广场", "type": "主题广场", "duration": 2, "ticket": 0}
                    ]
                },
                "包头": {
                    "region": "内蒙古",
                    "tags": ["草原", "工业", "美食"],
                    "best_season": ["夏季", "秋季"],
                    "avg_budget_per_day": 300,
                    "recommended_days": 2,
                    "attractions": [
                        {"name": "赛罕塔拉公园", "type": "自然风光", "duration": 3, "ticket": 0},
                        {"name": "北方兵器城", "type": "工业旅游", "duration": 2, "ticket": 50},
                        {"name": "五当召", "type": "宗教文化", "duration": 3, "ticket": 60}
                    ]
                }
            },

            "interest_tags": {
                "历史文化": ["北京", "西安", "洛阳", "南京"],
                "自然风光": ["杭州", "桂林", "张家界", "九寨沟", "呼伦贝尔"],
                "现代都市": ["上海", "深圳", "广州", "香港"],
                "美食": ["成都", "重庆", "广州", "西安", "呼和浩特", "呼伦贝尔"],
                "海滨度假": ["三亚", "厦门", "青岛", "大连"],
                "休闲养生": ["杭州", "成都", "丽江", "大理"],
                "草原风光": ["呼伦贝尔", "呼和浩特", "包头"],
                "民族风情": ["呼和浩特", "呼伦贝尔", "大理", "丽江"]
            }
        }

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
        return self.travel_knowledge['cities'].get(city_name)

    def search_cities_by_tag(self, tag: str) -> List[str]:
        """根据标签搜索城市"""
        return self.travel_knowledge['interest_tags'].get(tag, [])

    def get_all_cities(self) -> List[str]:
        """获取所有城市列表"""
        return list(self.travel_knowledge['cities'].keys())

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
