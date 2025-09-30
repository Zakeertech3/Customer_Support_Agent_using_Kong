import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.models import ConversationMessage, EscalationTicket, SessionData

logger = logging.getLogger(__name__)


class CRMService:
    def __init__(self):
        self.customer_interactions: Dict[str, List[Dict[str, Any]]] = {}
        self.tickets: Dict[str, EscalationTicket] = {}
        self.backup_file = "crm_backup.json"
        
        self.restore_from_backup()
    
    def log_interaction(self, customer_id: str, query: str, response: str, 
                       sentiment_score: Optional[float] = None, 
                       model_used: Optional[str] = None,
                       response_time_ms: Optional[int] = None,
                       tokens_used: Optional[int] = None,
                       complexity_score: Optional[float] = None,
                       session_id: Optional[str] = None) -> str:
        
        interaction_id = str(uuid4())
        interaction = {
            "interaction_id": interaction_id,
            "customer_id": customer_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "sentiment_score": sentiment_score,
            "model_used": model_used,
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used,
            "complexity_score": complexity_score
        }
        
        if customer_id not in self.customer_interactions:
            self.customer_interactions[customer_id] = []
        
        self.customer_interactions[customer_id].append(interaction)
        
        logger.info(f"Logged interaction {interaction_id} for customer {customer_id}")
        return interaction_id
    
    def create_ticket(self, ticket: EscalationTicket) -> str:
        self.tickets[ticket.ticket_id] = ticket
        
        self.log_interaction(
            customer_id=ticket.customer_id,
            query=f"Escalation: {ticket.reason}",
            response=f"Ticket created: {ticket.ticket_id}",
            session_id=None
        )
        
        logger.info(f"Created CRM ticket {ticket.ticket_id} for customer {ticket.customer_id}")
        return ticket.ticket_id
    
    def get_ticket(self, ticket_id: str) -> Optional[EscalationTicket]:
        return self.tickets.get(ticket_id)
    
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        if ticket_id in self.tickets:
            self.tickets[ticket_id].status = status
            logger.info(f"Updated ticket {ticket_id} status to {status}")
            return True
        return False
    
    def get_customer_interactions(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.customer_interactions.get(customer_id, [])
    
    def get_customer_tickets(self, customer_id: str) -> List[EscalationTicket]:
        return [ticket for ticket in self.tickets.values() if ticket.customer_id == customer_id]
    
    def get_all_tickets(self, status_filter: Optional[str] = None) -> List[EscalationTicket]:
        tickets = list(self.tickets.values())
        if status_filter:
            tickets = [t for t in tickets if t.status == status_filter]
        return sorted(tickets, key=lambda x: x.created_at, reverse=True)
    
    def export_customer_data(self, customer_id: str) -> Dict[str, Any]:
        interactions = self.get_customer_interactions(customer_id)
        tickets = self.get_customer_tickets(customer_id)
        
        return {
            "customer_id": customer_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_interactions": len(interactions),
            "total_tickets": len(tickets),
            "interactions": interactions,
            "tickets": [
                {
                    "ticket_id": ticket.ticket_id,
                    "created_at": ticket.created_at.isoformat(),
                    "reason": ticket.reason,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "summary": ticket.summary,
                    "escalation_score": ticket.escalation_score,
                    "conversation_history": [
                        {
                            "id": msg.id,
                            "timestamp": msg.timestamp.isoformat(),
                            "role": msg.role,
                            "content": msg.content,
                            "model_used": msg.model_used,
                            "sentiment_score": msg.sentiment_score,
                            "complexity_score": msg.complexity_score
                        }
                        for msg in ticket.conversation_history
                    ]
                }
                for ticket in tickets
            ]
        }
    
    def export_all_data(self) -> Dict[str, Any]:
        all_customers = set(self.customer_interactions.keys())
        all_customers.update(ticket.customer_id for ticket in self.tickets.values())
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_customers": len(all_customers),
            "total_interactions": sum(len(interactions) for interactions in self.customer_interactions.values()),
            "total_tickets": len(self.tickets),
            "customers": {
                customer_id: self.export_customer_data(customer_id)
                for customer_id in all_customers
            }
        }
    
    def get_interaction_statistics(self) -> Dict[str, Any]:
        total_interactions = sum(len(interactions) for interactions in self.customer_interactions.values())
        total_customers = len(self.customer_interactions)
        
        sentiment_scores = []
        complexity_scores = []
        response_times = []
        token_usage = []
        
        for interactions in self.customer_interactions.values():
            for interaction in interactions:
                if interaction.get("sentiment_score") is not None:
                    sentiment_scores.append(interaction["sentiment_score"])
                if interaction.get("complexity_score") is not None:
                    complexity_scores.append(interaction["complexity_score"])
                if interaction.get("response_time_ms") is not None:
                    response_times.append(interaction["response_time_ms"])
                if interaction.get("tokens_used") is not None:
                    token_usage.append(interaction["tokens_used"])
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_tokens = sum(token_usage)
        
        ticket_stats = {
            "total_tickets": len(self.tickets),
            "open_tickets": len([t for t in self.tickets.values() if t.status == "open"]),
            "resolved_tickets": len([t for t in self.tickets.values() if t.status == "resolved"]),
            "high_priority_tickets": len([t for t in self.tickets.values() if t.priority in ["high", "critical"]])
        }
        
        return {
            "interactions": {
                "total_interactions": total_interactions,
                "total_customers": total_customers,
                "avg_sentiment_score": round(avg_sentiment, 3),
                "avg_complexity_score": round(avg_complexity, 3),
                "avg_response_time_ms": round(avg_response_time, 2),
                "total_tokens_used": total_tokens
            },
            "tickets": ticket_stats
        }
    
    def backup_to_file(self) -> bool:
        try:
            backup_data = {
                "customer_interactions": self.customer_interactions,
                "tickets": {
                    ticket_id: {
                        "ticket_id": ticket.ticket_id,
                        "customer_id": ticket.customer_id,
                        "created_at": ticket.created_at.isoformat(),
                        "reason": ticket.reason,
                        "summary": ticket.summary,
                        "priority": ticket.priority,
                        "status": ticket.status,
                        "escalation_score": ticket.escalation_score,
                        "conversation_history": [
                            {
                                "id": msg.id,
                                "timestamp": msg.timestamp.isoformat(),
                                "role": msg.role,
                                "content": msg.content,
                                "model_used": msg.model_used,
                                "sentiment_score": msg.sentiment_score,
                                "complexity_score": msg.complexity_score,
                                "response_time_ms": msg.response_time_ms,
                                "tokens_used": msg.tokens_used,
                                "cached": msg.cached,
                                "thread_id": msg.thread_id
                            }
                            for msg in ticket.conversation_history
                        ]
                    }
                    for ticket_id, ticket in self.tickets.items()
                }
            }
            
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backed up CRM data to {self.backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup CRM data: {str(e)}", exc_info=True)
            return False
    
    def restore_from_backup(self) -> bool:
        try:
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
            
            self.customer_interactions = backup_data.get("customer_interactions", {})
            
            tickets_data = backup_data.get("tickets", {})
            for ticket_id, ticket_data in tickets_data.items():
                conversation_history = []
                for msg_data in ticket_data.get("conversation_history", []):
                    message = ConversationMessage(
                        id=msg_data["id"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        role=msg_data["role"],
                        content=msg_data["content"],
                        model_used=msg_data.get("model_used"),
                        sentiment_score=msg_data.get("sentiment_score"),
                        complexity_score=msg_data.get("complexity_score"),
                        response_time_ms=msg_data.get("response_time_ms"),
                        tokens_used=msg_data.get("tokens_used"),
                        cached=msg_data.get("cached", False),
                        thread_id=msg_data.get("thread_id")
                    )
                    conversation_history.append(message)
                
                ticket = EscalationTicket(
                    ticket_id=ticket_data["ticket_id"],
                    customer_id=ticket_data["customer_id"],
                    created_at=datetime.fromisoformat(ticket_data["created_at"]),
                    reason=ticket_data["reason"],
                    summary=ticket_data["summary"],
                    priority=ticket_data["priority"],
                    status=ticket_data["status"],
                    escalation_score=ticket_data["escalation_score"],
                    conversation_history=conversation_history
                )
                self.tickets[ticket_id] = ticket
            
            logger.info(f"Restored CRM data from {self.backup_file}")
            return True
            
        except FileNotFoundError:
            logger.info(f"No CRM backup file found at {self.backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore CRM data: {str(e)}", exc_info=True)
            return False


crm_service = CRMService()