"""Session repository implementation."""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from .session_repository import SessionRepository
from ..storage.session_storage import SessionStorage


class SessionRepositoryImpl(SessionRepository):
    """Implementation of SessionRepository using SessionStorage."""

    def __init__(self, storage: SessionStorage):
        self._storage = storage

    async def create(self, session_data: Dict[str, Any]) -> str:
        session_id = session_data.get('session_id', str(uuid.uuid4()))
        now = datetime.now().isoformat()

        session = {
            'session_id': session_id,
            'created_at': now,
            'last_active': now,
            'message_count': 0,
            'name': session_data.get('name'),
            'model_id': session_data.get('model_id', 'gpt-4o-mini'),
            'messages': session_data.get('messages', []),
            'user_preferences': session_data.get('user_preferences', {}),
        }

        await self._storage.save(session_id, session)
        return session_id

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self._storage.load(session_id)

    async def update(self, session_id: str, session_data: Dict[str, Any]) -> None:
        existing = await self._storage.load(session_id)
        if existing:
            session_data['last_active'] = datetime.now().isoformat()
            session_data['session_id'] = session_id
            session_data['created_at'] = existing.get('created_at')
            await self._storage.save(session_id, session_data)

    async def delete(self, session_id: str) -> bool:
        return await self._storage.delete(session_id)

    async def list_all(self, include_empty: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        sessions = await self._storage.list_all()
        one_hour_ago = datetime.now().timestamp() - 3600

        result = []
        for session_data in sessions.values():
            last_active = datetime.fromisoformat(session_data['last_active']).timestamp()

            if include_empty:
                result.append(session_data)
            elif session_data.get('message_count', 0) > 0 or last_active > one_hour_ago:
                result.append(session_data)

        result.sort(key=lambda x: x['last_active'], reverse=True)
        return result[:limit]

    async def cleanup_expired(self, max_age_seconds: int) -> int:
        return await self._storage.cleanup(max_age_seconds)
