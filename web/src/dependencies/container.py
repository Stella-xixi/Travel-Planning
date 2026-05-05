"""Dependency injection container."""
from typing import Dict, Any, Callable


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._providers: Dict[str, Callable] = {}
        self._instances: Dict[str, Any] = {}

    def register(self, name: str, provider: Callable, singleton: bool = True) -> None:
        """Register a dependency provider."""
        self._providers[name] = (provider, singleton)

    def resolve(self, name: str) -> Any:
        """Resolve a dependency."""
        if name not in self._providers:
            raise ValueError(f"Dependency not found: {name}")

        provider, singleton = self._providers[name]

        if singleton and name in self._instances:
            return self._instances[name]

        instance = provider()
        if singleton:
            self._instances[name] = instance

        return instance


# Global container instance
_container: Container = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
        _setup_default_providers()
    return _container


def _setup_default_providers() -> None:
    """Setup default providers."""
    from .providers import (
        provide_session_repository,
        provide_session_service,
        provide_chat_service,
        provide_travel_planning_agent_runtime
    )

    container = get_container()
    container.register('SessionRepository', provide_session_repository)
    container.register('SessionService', provide_session_service)
    container.register('ChatService', provide_chat_service)
    container.register('TravelAgent', provide_travel_planning_agent_runtime)
