"""Dependency providers."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'agent', 'src'))

from ..repositories.session_repository_impl import SessionRepositoryImpl
from ..services.session_service import SessionService
from ..services.chat_service import ChatService
from ..storage.session_storage import MemorySessionStorage


def provide_session_repository() -> SessionRepositoryImpl:
    """Provide session repository."""
    storage = MemorySessionStorage()
    return SessionRepositoryImpl(storage)


def provide_session_service() -> SessionService:
    """Provide session service."""
    repository = provide_session_repository()
    return SessionService(repository)


def provide_chat_service() -> ChatService:
    """Provide chat service."""
    repository = provide_session_repository()
    return ChatService(repository)


def provide_travel_planning_agent_runtime():
    """Provide travel agent (connects to backend gRPC service)."""
    from core.travel_planning_agent_runtime import ReActTravelAgent
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'agent', 'config', 'llm_config.yaml')
    return ReActTravelAgent(config_path=config_path)
