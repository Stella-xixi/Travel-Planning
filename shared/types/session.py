"""Shared session types."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class SessionCreateRequest(BaseModel):
    """Session create request."""
    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response."""
    success: bool
    session_id: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None


class SessionListResponse(BaseModel):
    """Session list response."""
    success: bool
    sessions: List[Dict[str, Any]]
    total: int


class SessionUpdateRequest(BaseModel):
    """Session update request."""
    name: Optional[str] = None
    model_id: Optional[str] = None


__all__ = [
    'SessionCreateRequest',
    'SessionResponse',
    'SessionListResponse',
    'SessionUpdateRequest'
]
