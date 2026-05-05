"""Session application service."""
from typing import Dict, Any, List
from ..repositories.session_repository import SessionRepository


class SessionService:
    """Application service for session operations."""

    def __init__(self, repository: SessionRepository):
        self._repository = repository

    async def create_session(self, name: str = None) -> Dict[str, Any]:
        """Create a new session."""
        session_id = await self._repository.create({
            'name': name or f"新会话",
        })
        return {
            'success': True,
            'session_id': session_id,
            'name': name or "新会话"
        }

    async def list_sessions(self, include_empty: bool = False) -> Dict[str, Any]:
        """List all sessions."""
        sessions = await self._repository.list_all(include_empty=include_empty)
        return {
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        }

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session."""
        result = await self._repository.delete(session_id)
        if result:
            return {'success': True}
        return {'success': False, 'error': '会话不存在'}

    async def update_session_name(self, session_id: str, name: str) -> Dict[str, Any]:
        """Update session name."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        await self._repository.update(session_id, {'name': name})
        return {'success': True, 'name': name}

    async def update_session_model(self, session_id: str, model_id: str) -> Dict[str, Any]:
        """Update session model."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        await self._repository.update(session_id, {'model_id': model_id})
        return {'success': True, 'model_id': model_id}

    async def get_session_model(self, session_id: str) -> Dict[str, Any]:
        """Get session model."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        return {
            'success': True,
            'model_id': session.get('model_id', 'gpt-4o-mini')
        }

    async def clear_chat(self, session_id: str) -> Dict[str, Any]:
        """Clear chat messages for a session."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        await self._repository.update(session_id, {
            'messages': [],
            'message_count': 0
        })
        return {'success': True}

    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session info."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        return {
            'success': True,
            'session': session
        }
