from datetime import datetime
from typing import Optional, Literal, List
from uuid import uuid4
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: Literal["user", "assistant", "system"]
    content: str
    model_used: Optional[str] = None
    sentiment_score: Optional[float] = None
    complexity_score: Optional[float] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cached: bool = False
    thread_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EscalationTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Literal["complexity", "sentiment", "manual"]
    summary: str
    conversation_history: List[ConversationMessage]
    priority: Literal["low", "medium", "high", "critical"]
    status: Literal["open", "assigned", "resolved"] = "open"
    escalation_score: float

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionData(BaseModel):
    session_id: str
    customer_id: str
    created_at: datetime
    messages: List[ConversationMessage] = []
    escalation_tickets: List[EscalationTicket] = []
    total_tokens: int = 0
    total_cost: float = 0.0
    cache_hits: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }