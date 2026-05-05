"""Shared API types."""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class APIResponse(BaseModel):
    """Standard API response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    limit: int = 20


class PaginatedResponse(BaseModel):
    """Paginated response."""
    items: List[Any]
    total: int
    page: int
    limit: int
    has_more: bool
