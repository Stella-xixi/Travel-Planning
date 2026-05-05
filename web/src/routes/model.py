"""Model API routes."""
from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()

# 内存中的配置管理器实例
_config_manager: Any = None


def set_config_manager(config_manager):
    """设置配置管理器实例"""
    global _config_manager
    _config_manager = config_manager


@router.get("/models")
async def list_models():
    """List available models."""
    if _config_manager:
        # 从 ConfigManager 动态获取模型列表
        models = _config_manager.get_available_models()
        return {"success": True, "models": models}

    # 回退到默认模型列表
    return {
        "success": True,
        "models": [
            {
                "model_id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "provider": "openai"
            },
            {
                "model_id": "gpt-4o",
                "name": "GPT-4o",
                "provider": "openai"
            },
            {
                "model_id": "claude-3-5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "provider": "anthropic"
            }
        ]
    }


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get model details."""
    if _config_manager:
        try:
            model_config = _config_manager.get_model_config(model_id)
            return {
                "success": True,
                "model_id": model_id,
                "name": model_config.get('name', model_id),
                "provider": model_config.get('provider', 'unknown'),
                **model_config
            }
        except ValueError:
            pass

    # 回退到默认模型详情
    models = {
        "gpt-4o-mini": {"name": "GPT-4o Mini", "provider": "openai", "description": "高效快速的小型模型"},
        "gpt-4o": {"name": "GPT-4o", "provider": "openai", "description": "强大的多模态模型"},
        "claude-3-5-sonnet": {"name": "Claude 3.5 Sonnet", "provider": "anthropic", "description": "平衡性能与速度"},
    }

    if model_id not in models:
        return {"success": False, "error": "Model not found"}

    return {"success": True, "model_id": model_id, **models[model_id]}
