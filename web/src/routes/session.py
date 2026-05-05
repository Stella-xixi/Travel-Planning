"""Session API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.session_service import SessionService
from ..dependencies.container import get_container

router = APIRouter()


class UpdateNameRequest(BaseModel):
    """Request model for updating session name."""
    name: str


class SetModelRequest(BaseModel):
    """Request model for setting session model."""
    model_id: str


def get_session_service() -> SessionService:
    """Get the session service from the container."""
    container = get_container()
    return container.resolve('SessionService')


@router.post("/session/new")
async def create_session(name: Optional[str] = None):
    """Create a new session."""
    service = get_session_service()
    result = await service.create_session(name=name)
    return result


@router.get("/sessions")
async def list_sessions(include_empty: bool = False):
    """List all sessions."""
    service = get_session_service()
    return await service.list_sessions(include_empty=include_empty)


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    service = get_session_service()
    result = await service.delete_session(session_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error'))
    return result


@router.put("/session/{session_id}/name")
async def update_session_name(session_id: str, request: UpdateNameRequest):
    """Update a session name."""
    service = get_session_service()
    result = await service.update_session_name(session_id, request.name)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error'))
    return result


@router.put("/session/{session_id}/model")
async def set_session_model(session_id: str, request: SetModelRequest):
    """Set the model for a session."""
    service = get_session_service()
    result = await service.update_session_model(session_id, request.model_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error'))
    return result


@router.get("/session/{session_id}/model")
async def get_session_model(session_id: str):
    """Get the model for a session."""
    service = get_session_service()
    result = await service.get_session_model(session_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error'))
    return result


@router.post("/clear/{session_id}")
async def clear_chat(session_id: str):
    """Clear chat messages for a session."""
    service = get_session_service()
    result = await service.clear_chat(session_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error'))
    return result
