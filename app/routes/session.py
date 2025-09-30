import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import session_manager
from app.models import SessionData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/health")
async def session_health():
    return {
        "status": "healthy",
        "service": "session_manager",
        "active_sessions": len(session_manager.sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


class CreateSessionRequest(BaseModel):
    customer_id: str
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    session: SessionData


@router.post("/create", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    try:
        session = session_manager.create_session(
            customer_id=request.customer_id,
            session_id=request.session_id
        )
        
        return SessionResponse(session=session)
        
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return SessionResponse(session=session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.get("/customer/{customer_id}")
async def get_customer_sessions(customer_id: str) -> Dict[str, Any]:
    try:
        sessions = session_manager.get_customer_sessions(customer_id)
        
        return {
            "customer_id": customer_id,
            "total_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "message_count": len(session.messages),
                    "escalation_count": len(session.escalation_tickets),
                    "total_tokens": session.total_tokens,
                    "cache_hits": session.cache_hits
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve customer sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customer sessions: {str(e)}")


@router.get("/{session_id}/export")
async def export_session(session_id: str) -> Dict[str, Any]:
    try:
        session_data = session_manager.export_session_data(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")


@router.post("/backup")
async def backup_sessions() -> Dict[str, Any]:
    try:
        success = session_manager.backup_sessions_to_file()
        
        return {
            "success": success,
            "message": "Sessions backed up successfully" if success else "Backup failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to backup sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to backup sessions: {str(e)}")


@router.post("/restore")
async def restore_sessions() -> Dict[str, Any]:
    try:
        success = session_manager.restore_sessions_from_file()
        
        return {
            "success": success,
            "message": "Sessions restored successfully" if success else "Restore failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to restore sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to restore sessions: {str(e)}")


@router.get("/stats/overview")
async def get_session_statistics() -> Dict[str, Any]:
    try:
        stats = session_manager.get_session_statistics()
        stats["timestamp"] = datetime.utcnow().isoformat()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get session statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session statistics: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


class UpdateSessionRequest(BaseModel):
    total_cost: Optional[float] = None
    customer_id: Optional[str] = None


@router.put("/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest) -> Dict[str, Any]:
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")
        
        success = session_manager.update_session(session_id, **update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} updated successfully",
            "updated_fields": list(update_data.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.get("/{session_id}/threads")
async def get_session_threads(session_id: str) -> Dict[str, Any]:
    try:
        threads = session_manager.get_session_threads(session_id)
        
        if not threads:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "session_id": session_id,
            "thread_count": len(threads),
            "threads": {
                thread_id: [
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
                    for msg in messages
                ]
                for thread_id, messages in threads.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session threads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session threads: {str(e)}")


@router.get("/{session_id}/thread/{thread_id}")
async def get_conversation_thread(session_id: str, thread_id: str) -> Dict[str, Any]:
    try:
        messages = session_manager.get_conversation_thread(session_id, thread_id)
        
        if not messages:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found in session {session_id}")
        
        return {
            "session_id": session_id,
            "thread_id": thread_id,
            "message_count": len(messages),
            "messages": [
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
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get conversation thread: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_sessions(days_old: int = 30) -> Dict[str, Any]:
    try:
        deleted_count = session_manager.clear_old_sessions(days_old)
        
        return {
            "success": True,
            "deleted_sessions": deleted_count,
            "days_old": days_old,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old sessions: {str(e)}")