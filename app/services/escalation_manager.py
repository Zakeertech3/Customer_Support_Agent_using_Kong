import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from app.models import ConversationMessage, EscalationTicket, SessionData

logger = logging.getLogger(__name__)


class EscalationManager:
    def __init__(self):
        self.complexity_threshold = 0.8
        self.sentiment_threshold = -0.5
        self.crm_store = {}
        
    def should_escalate(self, complexity_score: float, sentiment_score: float) -> Tuple[bool, List[str]]:
        reasons = []
        
        if complexity_score > self.complexity_threshold:
            reasons.append("complexity")
            
        if sentiment_score < self.sentiment_threshold:
            reasons.append("sentiment")
            
        return len(reasons) > 0, reasons
    
    def generate_escalation_summary(self, conversation_history: List[ConversationMessage], 
                                  escalation_reasons: List[str]) -> str:
        if not conversation_history:
            return "No conversation history available for escalation summary."
        
        user_messages = [msg for msg in conversation_history if msg.role == "user"]
        assistant_messages = [msg for msg in conversation_history if msg.role == "assistant"]
        
        summary_parts = []
        
        summary_parts.append(f"ESCALATION TRIGGERED: {', '.join(escalation_reasons).upper()}")
        summary_parts.append(f"Conversation started: {conversation_history[0].timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append(f"Total messages: {len(conversation_history)}")
        
        if user_messages:
            latest_user_msg = user_messages[-1]
            summary_parts.append(f"Latest customer query: \"{latest_user_msg.content[:200]}{'...' if len(latest_user_msg.content) > 200 else ''}\"")
            
            if latest_user_msg.complexity_score:
                summary_parts.append(f"Query complexity score: {latest_user_msg.complexity_score:.3f}")
            if latest_user_msg.sentiment_score:
                summary_parts.append(f"Sentiment score: {latest_user_msg.sentiment_score:.3f}")
        
        if assistant_messages:
            models_used = list(set([msg.model_used for msg in assistant_messages if msg.model_used]))
            if models_used:
                summary_parts.append(f"AI models used: {', '.join(models_used)}")
        
        key_issues = self._extract_key_issues(user_messages)
        if key_issues:
            summary_parts.append(f"Key issues identified: {key_issues}")
        
        return "\n".join(summary_parts)
    
    def _extract_key_issues(self, user_messages: List[ConversationMessage]) -> str:
        issue_keywords = {
            "technical": ["api", "integration", "error", "bug", "configuration", "setup"],
            "billing": ["payment", "charge", "invoice", "billing", "cost", "price"],
            "access": ["login", "password", "access", "permission", "authentication"],
            "performance": ["slow", "timeout", "performance", "speed", "latency"],
            "frustration": ["frustrated", "angry", "terrible", "awful", "unacceptable", "disappointed"]
        }
        
        detected_issues = []
        
        for message in user_messages:
            content_lower = message.content.lower()
            for category, keywords in issue_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    if category not in detected_issues:
                        detected_issues.append(category)
        
        return ", ".join(detected_issues) if detected_issues else "general inquiry"
    
    def create_escalation_ticket(self, customer_id: str, conversation_history: List[ConversationMessage],
                               escalation_reasons: List[str], escalation_score: float) -> EscalationTicket:
        summary = self.generate_escalation_summary(conversation_history, escalation_reasons)
        
        primary_reason = escalation_reasons[0] if escalation_reasons else "manual"
        
        priority = self._calculate_priority(escalation_score, escalation_reasons)
        
        ticket = EscalationTicket(
            customer_id=customer_id,
            reason=primary_reason,
            summary=summary,
            conversation_history=conversation_history.copy(),
            priority=priority,
            escalation_score=escalation_score
        )
        
        self._log_to_crm(ticket)
        
        logger.info(f"Escalation ticket created: {ticket.ticket_id} for customer {customer_id} "
                   f"with priority {priority} and reasons: {', '.join(escalation_reasons)}")
        
        return ticket
    
    def _calculate_priority(self, escalation_score: float, reasons: List[str]) -> str:
        if escalation_score >= 0.9 or "sentiment" in reasons:
            return "critical"
        elif escalation_score >= 0.8:
            return "high"
        elif escalation_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _log_to_crm(self, ticket: EscalationTicket) -> None:
        if ticket.customer_id not in self.crm_store:
            self.crm_store[ticket.customer_id] = {
                "customer_id": ticket.customer_id,
                "tickets": [],
                "total_escalations": 0,
                "last_escalation": None
            }
        
        self.crm_store[ticket.customer_id]["tickets"].append({
            "ticket_id": ticket.ticket_id,
            "created_at": ticket.created_at.isoformat(),
            "reason": ticket.reason,
            "priority": ticket.priority,
            "status": ticket.status,
            "summary": ticket.summary,
            "escalation_score": ticket.escalation_score
        })
        
        self.crm_store[ticket.customer_id]["total_escalations"] += 1
        self.crm_store[ticket.customer_id]["last_escalation"] = ticket.created_at.isoformat()
    
    def get_customer_escalation_history(self, customer_id: str) -> Dict[str, Any]:
        return self.crm_store.get(customer_id, {
            "customer_id": customer_id,
            "tickets": [],
            "total_escalations": 0,
            "last_escalation": None
        })
    
    def get_all_escalations(self) -> Dict[str, Any]:
        return self.crm_store
    
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        for customer_data in self.crm_store.values():
            for ticket in customer_data["tickets"]:
                if ticket["ticket_id"] == ticket_id:
                    ticket["status"] = status
                    logger.info(f"Ticket {ticket_id} status updated to {status}")
                    return True
        return False
    
    def get_escalation_notification(self, ticket: EscalationTicket) -> Dict[str, Any]:
        return {
            "type": "escalation",
            "ticket_id": ticket.ticket_id,
            "message": "Human agent requested - Your query has been escalated for specialized assistance",
            "priority": ticket.priority,
            "reason": ticket.reason,
            "created_at": ticket.created_at.isoformat(),
            "estimated_response_time": self._get_estimated_response_time(ticket.priority)
        }
    
    def _get_estimated_response_time(self, priority: str) -> str:
        response_times = {
            "critical": "within 15 minutes",
            "high": "within 1 hour", 
            "medium": "within 4 hours",
            "low": "within 24 hours"
        }
        return response_times.get(priority, "within 24 hours")


escalation_manager = EscalationManager()