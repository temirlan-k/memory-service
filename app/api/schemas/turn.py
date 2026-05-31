from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    name: Optional[str] = None

class TurnRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    messages: list[Message] = Field(min_length=1)
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

class TurnResponse(BaseModel):
    id: str