from typing import Optional
from pydantic import BaseModel


class RecallRequest(BaseModel):
    query: str
    session_id: str
    user_id: Optional[str] = None
    max_tokens: int = 1024


class Citation(BaseModel):
    turn_id: str
    score: float
    snippet: str


class RecallResponse(BaseModel):
    context: str
    citations: list[Citation]
