"""Session storage abstraction and implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os


class SessionStorage(ABC):
    """Abstract base class for session storage."""

    @abstractmethod
    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data."""
        pass

    @abstractmethod
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    async def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all sessions."""
        pass

    @abstractmethod
    async def cleanup(self, max_age_seconds: int) -> int:
        """Clean up expired sessions."""
        pass


class MemorySessionStorage(SessionStorage):
    """In-memory session storage for development."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        data['last_active'] = datetime.now().isoformat()
        self._sessions[session_id] = data

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_all(self) -> Dict[str, Dict[str, Any]]:
        return self._sessions.copy()

    async def cleanup(self, max_age_seconds: int) -> int:
        current_time = datetime.now()
        expired_ids = []

        for session_id, data in self._sessions.items():
            last_active = datetime.fromisoformat(data['last_active'])
            if (current_time - last_active).total_seconds() > max_age_seconds:
                expired_ids.append(session_id)

        for session_id in expired_ids:
            del self._sessions[session_id]

        return len(expired_ids)


class FileSessionStorage(SessionStorage):
    """File-based session storage for persistence."""

    def __init__(self, file_path: str = "data/sessions.json"):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self._file_path = file_path
        self._sessions: Dict[str, Dict[str, Any]] = self._load_from_file()

    def _load_from_file(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_to_file(self) -> None:
        with open(self._file_path, 'w', encoding='utf-8') as f:
            json.dump(self._sessions, f, indent=2, ensure_ascii=False)

    async def save(self, session_id: str, data: Dict[str, Any]) -> None:
        data['last_active'] = datetime.now().isoformat()
        self._sessions[session_id] = data
        self._save_to_file()

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_to_file()
            return True
        return False

    async def list_all(self) -> Dict[str, Dict[str, Any]]:
        return self._sessions.copy()

    async def cleanup(self, max_age_seconds: int) -> int:
        current_time = datetime.now()
        expired_ids = []

        for session_id, data in self._sessions.items():
            last_active = datetime.fromisoformat(data['last_active'])
            if (current_time - last_active).total_seconds() > max_age_seconds:
                expired_ids.append(session_id)

        for session_id in expired_ids:
            del self._sessions[session_id]

        if expired_ids:
            self._save_to_file()

        return len(expired_ids)
