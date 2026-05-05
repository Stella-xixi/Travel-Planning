"""Shared message types."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Message(BaseModel):
    """Chat message."""
    role: str
    content: str
    timestamp: Optional[str] = None
    reasoning: Optional[str] = None


class Session(BaseModel):
    """Chat session."""
    session_id: str
    name: Optional[str] = None
    model_id: str = "gpt-4o-mini"
    message_count: int = 0
    messages: List[Message] = []
    created_at: Optional[str] = None
    last_active: Optional[str] = None
    user_preferences: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    """Chat request."""
    message: str
    session_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """Chat response."""
    success: bool
    answer: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class StreamChunk(BaseModel):
    """Stream chunk for SSE."""
    chunk_type: str  # "session_id", "reasoning_start", "reasoning_chunk", "reasoning_end", "answer_start", "chunk", "done", "error"
    content: str
    is_last: bool = False


class CityInfo(BaseModel):
    """City information."""
    id: str
    name: str
    region: str
    tags: List[str]
    description: Optional[str] = None
    attractions: List[Dict[str, Any]] = []
    avg_budget_per_day: int = 0
    best_seasons: List[str] = []


class ModelInfo(BaseModel):
    """Model information."""
    model_id: str
    name: str
    provider: str
    description: Optional[str] = None
