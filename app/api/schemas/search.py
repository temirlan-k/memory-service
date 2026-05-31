from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = 10


class SearchResult(BaseModel):
    content: str
    score: float
    session_id: str
    timestamp: datetime
    metadata: dict = {}


class SearchResponse(BaseModel):
    results: list[SearchResult]
