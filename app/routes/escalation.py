import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import escalation_manager
from app.models import ConversationMessage, EscalationTicket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/escalation", tags=["escalation"])


class EscalationRequest(BaseModel):
    customer_id: str
    conversation_history: List[ConversationMessage]
    escalation_reasons: List[str]
    escalation_score: float


class EscalationResponse(BaseModel):
    ticket: EscalationTicket
    notification: Dict[str, Any]


class TicketStatusUpdate(BaseModel):
    ticket_id: str
    status: str = Field(..., pattern="^(open|assigned|resolved)$")


@router.post("/create", response_model=EscalationResponse)
async def create_escalation(request: EscalationRequest) -> EscalationResponse:
    try:
        ticket = escalation_manager.create_escalation_ticket(
            customer_id=request.customer_id,
            conversation_history=request.conversation_history,
            escalation_reasons=request.escalation_reasons,
            escalation_score=request.escalation_score
        )
        
        notification = escalation_manager.get_escalation_notification(ticket)
        
        return EscalationResponse(
            ticket=ticket,
            notification=notification
        )
        
    except Exception as e:
        logger.error(f"Failed to create escalation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create escalation: {str(e)}")


@router.get("/check/{complexity_score}/{sentiment_score}")
async def check_escalation_needed(complexity_score: float, sentiment_score: float) -> Dict[str, Any]:
    should_escalate, reasons = escalation_manager.should_escalate(complexity_score, sentiment_score)
    
    return {
        "should_escalate": should_escalate,
        "reasons": reasons,
        "complexity_score": complexity_score,
        "sentiment_score": sentiment_score,
        "complexity_threshold": escalation_manager.complexity_threshold,
        "sentiment_threshold": escalation_manager.sentiment_threshold,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/customer/{customer_id}")
async def get_customer_escalations(customer_id: str) -> Dict[str, Any]:
    try:
        history = escalation_manager.get_customer_escalation_history(customer_id)
        return history
    except Exception as e:
        logger.error(f"Failed to retrieve customer escalations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve escalations: {str(e)}")


@router.get("/all")
async def get_all_escalations() -> Dict[str, Any]:
    try:
        return escalation_manager.get_all_escalations()
    except Exception as e:
        logger.error(f"Failed to retrieve all escalations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve escalations: {str(e)}")


@router.put("/ticket/status")
async def update_ticket_status(request: TicketStatusUpdate) -> Dict[str, Any]:
    try:
        success = escalation_manager.update_ticket_status(request.ticket_id, request.status)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Ticket {request.ticket_id} not found")
        
        return {
            "success": True,
            "ticket_id": request.ticket_id,
            "new_status": request.status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ticket status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update ticket status: {str(e)}")


@router.post("/manual")
async def create_manual_escalation(customer_id: str, reason: str = "Manual escalation requested") -> EscalationResponse:
    try:
        conversation_history = []
        
        manual_message = ConversationMessage(
            role="user",
            content=reason,
            complexity_score=1.0,
            sentiment_score=-0.8
        )
        conversation_history.append(manual_message)
        
        ticket = escalation_manager.create_escalation_ticket(
            customer_id=customer_id,
            conversation_history=conversation_history,
            escalation_reasons=["manual"],
            escalation_score=1.0
        )
        
        notification = escalation_manager.get_escalation_notification(ticket)
        
        return EscalationResponse(
            ticket=ticket,
            notification=notification
        )
        
    except Exception as e:
        logger.error(f"Failed to create manual escalation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create manual escalation: {str(e)}")


@router.get("/health")
async def escalation_health():
    return {
        "status": "healthy",
        "service": "escalation_manager",
        "total_customers": len(escalation_manager.crm_store),
        "total_tickets": sum(len(customer["tickets"]) for customer in escalation_manager.crm_store.values()),
        "timestamp": datetime.utcnow().isoformat()
    }