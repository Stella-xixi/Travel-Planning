"""Chat application service."""
from typing import Dict, Any, AsyncGenerator
from ..repositories.session_repository import SessionRepository


class ChatService:
    """Application service for chat operations."""

    def __init__(self, repository: SessionRepository):
        self._repository = repository

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        reasoning: str = None
    ) -> Dict[str, Any]:
        """Save a message to a session."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}

        message = {
            'role': role,
            'content': content,
            'reasoning': reasoning,
            'timestamp': self._get_timestamp(),
        }

        messages = session.get('messages', [])
        messages.append(message)
        session['messages'] = messages
        session['message_count'] = len(messages)
        session['last_active'] = self._get_timestamp()

        await self._repository.update(session_id, session)
        return {'success': True}

    async def get_messages(self, session_id: str) -> Dict[str, Any]:
        """Get all messages for a session."""
        session = await self._repository.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在', 'messages': []}

        messages = session.get('messages', [])
        return {'success': True, 'messages': messages}

    def _get_timestamp(self) -> str:
        """Get current timestamp in local format."""
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S')

    async def cleanup_expired_sessions(self, max_age_seconds: int = 86400) -> int:
        """Clean up expired sessions."""
        return await self._repository.cleanup_expired(max_age_seconds)

    async def generate_chat_stream(
        self,
        session_id: str,
        message: str,
        agent
    ) -> AsyncGenerator[str, None]:
        """Generate chat response stream."""
        import json

        # Ensure session exists
        if not session_id:
            result = await self.create_session_for_chat()
            session_id = result['session_id']
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

        # Save user message
        await self.save_message(session_id, 'user', message)

        # Yield reasoning_start event
        yield f"data: {json.dumps({'type': 'reasoning_start'})}\n\n"

        # Process message with agent
        result = await agent.process(message)

        # Yield reasoning content
        if result.get('reasoning'):
            reasoning_text = result.get('reasoning', {}).get('text', '')
            yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': reasoning_text})}\n\n"

        # Yield reasoning_end event
        yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"

        # Yield answer_start event
        yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"

        # Get answer
        answer = result.get('answer', '')

        # Stream answer chunks
        for char in answer:
            yield f"data: {json.dumps({'type': 'chunk', 'content': char})}\n\n"

        # Save assistant message
        await self.save_message(session_id, 'assistant', answer, result.get('reasoning', {}).get('text', ''))

        # Yield done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def create_session_for_chat(self) -> Dict[str, Any]:
        """Create a new session for chat."""
        from datetime import datetime
        now = datetime.now().isoformat()
        session_id = str(uuid.uuid4())

        session = {
            'session_id': session_id,
            'created_at': now,
            'last_active': now,
            'message_count': 0,
            'name': f"会话 {now[:10]}",
            'model_id': 'gpt-4o-mini',
            'messages': [],
            'user_preferences': {},
        }

        await self._repository.create(session)
        return {'success': True, 'session_id': session_id}
