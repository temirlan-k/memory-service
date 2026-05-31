from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MemoryResponse(BaseModel):
    id: str
    type: str
    key: str
    value: str
    confidence: float
    source_session: str
    source_turn: str
    active: bool
    supersedes: Optional[str]
    created_at: datetime
    updated_at: datetime


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse]
