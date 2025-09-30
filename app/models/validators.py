from typing import Dict, Any, List
from datetime import datetime
from .conversation import ConversationMessage, EscalationTicket, SessionData


class ModelValidator:
    @staticmethod
    def validate_sentiment_score(score: float) -> bool:
        return -1.0 <= score <= 1.0
    
    @staticmethod
    def validate_complexity_score(score: float) -> bool:
        return 0.0 <= score <= 1.0
    
    @staticmethod
    def validate_message_role(role: str) -> bool:
        return role in ["user", "assistant", "system"]
    
    @staticmethod
    def validate_escalation_reason(reason: str) -> bool:
        return reason in ["complexity", "sentiment", "manual"]
    
    @staticmethod
    def validate_priority_level(priority: str) -> bool:
        return priority in ["low", "medium", "high", "critical"]
    
    @staticmethod
    def validate_ticket_status(status: str) -> bool:
        return status in ["open", "assigned", "resolved"]


class ModelSerializer:
    @staticmethod
    def serialize_message(message: ConversationMessage) -> Dict[str, Any]:
        return {
            "id": message.id,
            "timestamp": message.timestamp.isoformat(),
            "role": message.role,
            "content": message.content,
            "model_used": message.model_used,
            "sentiment_score": message.sentiment_score,
            "complexity_score": message.complexity_score,
            "response_time_ms": message.response_time_ms,
            "tokens_used": message.tokens_used,
            "cached": message.cached
        }
    
    @staticmethod
    def serialize_ticket(ticket: EscalationTicket) -> Dict[str, Any]:
        return {
            "ticket_id": ticket.ticket_id,
            "customer_id": ticket.customer_id,
            "created_at": ticket.created_at.isoformat(),
            "reason": ticket.reason,
            "summary": ticket.summary,
            "conversation_history": [
                ModelSerializer.serialize_message(msg) for msg in ticket.conversation_history
            ],
            "priority": ticket.priority,
            "status": ticket.status,
            "escalation_score": ticket.escalation_score
        }
    
    @staticmethod
    def serialize_session(session: SessionData) -> Dict[str, Any]:
        return {
            "session_id": session.session_id,
            "customer_id": session.customer_id,
            "created_at": session.created_at.isoformat(),
            "messages": [
                ModelSerializer.serialize_message(msg) for msg in session.messages
            ],
            "escalation_tickets": [
                ModelSerializer.serialize_ticket(ticket) for ticket in session.escalation_tickets
            ],
            "total_tokens": session.total_tokens,
            "total_cost": session.total_cost,
            "cache_hits": session.cache_hits
        }
    
    @staticmethod
    def deserialize_message(data: Dict[str, Any]) -> ConversationMessage:
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return ConversationMessage(**data)
    
    @staticmethod
    def deserialize_ticket(data: Dict[str, Any]) -> EscalationTicket:
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        data["conversation_history"] = [
            ModelSerializer.deserialize_message(msg_data) 
            for msg_data in data["conversation_history"]
        ]
        return EscalationTicket(**data)
    
    @staticmethod
    def deserialize_session(data: Dict[str, Any]) -> SessionData:
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        data["messages"] = [
            ModelSerializer.deserialize_message(msg_data) 
            for msg_data in data["messages"]
        ]
        
        data["escalation_tickets"] = [
            ModelSerializer.deserialize_ticket(ticket_data) 
            for ticket_data in data["escalation_tickets"]
        ]
        return SessionData(**data)