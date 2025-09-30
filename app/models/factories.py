from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from .conversation import ConversationMessage, EscalationTicket, SessionData


class ModelFactory:
    @staticmethod
    def create_message(
        role: str,
        content: str,
        model_used: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        complexity_score: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cached: bool = False
    ) -> ConversationMessage:
        return ConversationMessage(
            role=role,
            content=content,
            model_used=model_used,
            sentiment_score=sentiment_score,
            complexity_score=complexity_score,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            cached=cached
        )
    
    @staticmethod
    def create_escalation_ticket(
        customer_id: str,
        reason: str,
        summary: str,
        conversation_history: List[ConversationMessage],
        priority: str = "medium",
        escalation_score: float = 0.0
    ) -> EscalationTicket:
        return EscalationTicket(
            customer_id=customer_id,
            reason=reason,
            summary=summary,
            conversation_history=conversation_history,
            priority=priority,
            escalation_score=escalation_score
        )
    
    @staticmethod
    def create_session(
        customer_id: str,
        session_id: Optional[str] = None
    ) -> SessionData:
        if session_id is None:
            session_id = str(uuid4())
        
        return SessionData(
            session_id=session_id,
            customer_id=customer_id,
            created_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_user_message(content: str) -> ConversationMessage:
        return ModelFactory.create_message(role="user", content=content)
    
    @staticmethod
    def create_assistant_message(
        content: str,
        model_used: str,
        sentiment_score: Optional[float] = None,
        complexity_score: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cached: bool = False
    ) -> ConversationMessage:
        return ModelFactory.create_message(
            role="assistant",
            content=content,
            model_used=model_used,
            sentiment_score=sentiment_score,
            complexity_score=complexity_score,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            cached=cached
        )
    
    @staticmethod
    def create_system_message(content: str) -> ConversationMessage:
        return ModelFactory.create_message(role="system", content=content)