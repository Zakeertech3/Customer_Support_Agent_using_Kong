from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services import crm_service
from app.models import EscalationTicket

router = APIRouter(prefix="/api/crm", tags=["CRM"])


class InteractionLogRequest(BaseModel):
    customer_id: str
    query: str
    response: str
    sentiment_score: Optional[float] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    complexity_score: Optional[float] = None
    session_id: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    status: str


@router.post("/interactions/log")
async def log_interaction(request: InteractionLogRequest) -> Dict[str, str]:
    interaction_id = crm_service.log_interaction(
        customer_id=request.customer_id,
        query=request.query,
        response=request.response,
        sentiment_score=request.sentiment_score,
        model_used=request.model_used,
        response_time_ms=request.response_time_ms,
        tokens_used=request.tokens_used,
        complexity_score=request.complexity_score,
        session_id=request.session_id
    )
    
    return {"interaction_id": interaction_id, "status": "logged"}


@router.get("/interactions/{customer_id}")
async def get_customer_interactions(customer_id: str) -> List[Dict[str, Any]]:
    interactions = crm_service.get_customer_interactions(customer_id)
    return interactions


@router.post("/tickets")
async def create_ticket(ticket: EscalationTicket) -> Dict[str, str]:
    ticket_id = crm_service.create_ticket(ticket)
    return {"ticket_id": ticket_id, "status": "created"}


@router.get("/tickets")
async def get_all_tickets(status: Optional[str] = Query(None)) -> List[EscalationTicket]:
    tickets = crm_service.get_all_tickets(status_filter=status)
    return tickets


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str) -> EscalationTicket:
    ticket = crm_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, update: TicketStatusUpdate) -> Dict[str, str]:
    success = crm_service.update_ticket_status(ticket_id, update.status)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"ticket_id": ticket_id, "status": update.status}


@router.get("/tickets/customer/{customer_id}")
async def get_customer_tickets(customer_id: str) -> List[EscalationTicket]:
    tickets = crm_service.get_customer_tickets(customer_id)
    return tickets


@router.get("/export/customer/{customer_id}")
async def export_customer_data(customer_id: str) -> Dict[str, Any]:
    data = crm_service.export_customer_data(customer_id)
    return data


@router.get("/export/all")
async def export_all_data() -> Dict[str, Any]:
    data = crm_service.export_all_data()
    return data


@router.get("/statistics")
async def get_crm_statistics() -> Dict[str, Any]:
    stats = crm_service.get_interaction_statistics()
    return stats


@router.post("/backup")
async def backup_crm_data() -> Dict[str, str]:
    success = crm_service.backup_to_file()
    if success:
        return {"status": "backup_completed"}
    else:
        raise HTTPException(status_code=500, detail="Backup failed")