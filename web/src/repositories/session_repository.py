"""Session repository interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SessionRepository(ABC):
    """Session repository interface."""

    @abstractmethod
    async def create(self, session_data: Dict[str, Any]) -> str:
        """Create a new session."""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        pass

    @abstractmethod
    async def update(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Update a session."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    async def list_all(self, include_empty: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        pass

    @abstractmethod
    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """Clean up expired sessions."""
        pass
