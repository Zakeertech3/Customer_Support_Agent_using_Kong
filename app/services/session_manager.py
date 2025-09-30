import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.models import SessionData, ConversationMessage, EscalationTicket

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, auto_backup_interval: int = 300):
        self.sessions: Dict[str, SessionData] = {}
        self.backup_file = "sessions_backup.json"
        self.auto_backup_interval = auto_backup_interval
        self._backup_thread = None
        self._stop_backup = False
        self._lock = threading.Lock()
        
        self.restore_sessions_from_file()
        self._start_auto_backup()
        
    def create_session(self, customer_id: str, session_id: Optional[str] = None) -> SessionData:
        with self._lock:
            if not session_id:
                session_id = str(uuid4())
                
            session = SessionData(
                session_id=session_id,
                customer_id=customer_id,
                created_at=datetime.utcnow()
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created new session {session_id} for customer {customer_id}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            return self.sessions.get(session_id)
    
    def add_message_to_session(self, session_id: str, message: ConversationMessage) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
            
        session.messages.append(message)
        
        if message.tokens_used:
            session.total_tokens += message.tokens_used
            
        if message.cached:
            session.cache_hits += 1
            
        logger.debug(f"Added message to session {session_id}")
        return True
    
    def add_escalation_to_session(self, session_id: str, ticket: EscalationTicket) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
            
        session.escalation_tickets.append(ticket)
        logger.info(f"Added escalation ticket {ticket.ticket_id} to session {session_id}")
        return True
    
    def get_session_messages(self, session_id: str) -> List[ConversationMessage]:
        session = self.sessions.get(session_id)
        return session.messages if session else []
    
    def get_customer_sessions(self, customer_id: str) -> List[SessionData]:
        return [session for session in self.sessions.values() if session.customer_id == customer_id]
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
            
        return {
            "session_id": session.session_id,
            "customer_id": session.customer_id,
            "created_at": session.created_at.isoformat(),
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
                for msg in session.messages
            ],
            "escalation_tickets": [
                {
                    "ticket_id": ticket.ticket_id,
                    "created_at": ticket.created_at.isoformat(),
                    "reason": ticket.reason,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "summary": ticket.summary,
                    "escalation_score": ticket.escalation_score
                }
                for ticket in session.escalation_tickets
            ],
            "total_tokens": session.total_tokens,
            "total_cost": session.total_cost,
            "cache_hits": session.cache_hits
        }
    
    def backup_sessions_to_file(self) -> bool:
        try:
            backup_data = {}
            for session_id, session in self.sessions.items():
                backup_data[session_id] = self.export_session_data(session_id)
            
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backed up {len(self.sessions)} sessions to {self.backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup sessions: {str(e)}", exc_info=True)
            return False
    
    def restore_sessions_from_file(self) -> bool:
        try:
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            for session_id, session_data in backup_data.items():
                if session_data:
                    session = SessionData(
                        session_id=session_data["session_id"],
                        customer_id=session_data["customer_id"],
                        created_at=datetime.fromisoformat(session_data["created_at"]),
                        total_tokens=session_data.get("total_tokens", 0),
                        total_cost=session_data.get("total_cost", 0.0),
                        cache_hits=session_data.get("cache_hits", 0)
                    )
                    
                    for msg_data in session_data.get("messages", []):
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
                        session.messages.append(message)
                    
                    self.sessions[session_id] = session
                    restored_count += 1
            
            logger.info(f"Restored {restored_count} sessions from {self.backup_file}")
            return True
            
        except FileNotFoundError:
            logger.info(f"No backup file found at {self.backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore sessions: {str(e)}", exc_info=True)
            return False
    
    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found for deletion")
                return False
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for update")
                return False
            
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
                    logger.debug(f"Updated session {session_id} field {key}")
            
            return True
    
    def get_conversation_thread(self, session_id: str, thread_id: Optional[str] = None) -> List[ConversationMessage]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        if thread_id:
            return [msg for msg in session.messages if getattr(msg, 'thread_id', None) == thread_id]
        else:
            return session.messages
    
    def add_message_with_threading(self, session_id: str, message: ConversationMessage, parent_message_id: Optional[str] = None) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
        
        if parent_message_id:
            parent_msg = next((msg for msg in session.messages if msg.id == parent_message_id), None)
            if parent_msg:
                message.thread_id = getattr(parent_msg, 'thread_id', parent_msg.id)
            else:
                message.thread_id = message.id
        else:
            message.thread_id = message.id
        
        session.messages.append(message)
        
        if message.tokens_used:
            session.total_tokens += message.tokens_used
            
        if message.cached:
            session.cache_hits += 1
            
        logger.debug(f"Added threaded message to session {session_id}")
        return True
    
    def get_session_threads(self, session_id: str) -> Dict[str, List[ConversationMessage]]:
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        threads = {}
        for message in session.messages:
            thread_id = getattr(message, 'thread_id', message.id)
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(message)
        
        return threads
    
    def clear_old_sessions(self, days_old: int = 30) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        sessions_to_delete = []
        
        for session_id, session in self.sessions.items():
            if session.created_at < cutoff_date:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            del self.sessions[session_id]
        
        logger.info(f"Cleared {len(sessions_to_delete)} old sessions")
        return len(sessions_to_delete)
    
    def get_session_statistics(self) -> Dict[str, Any]:
        total_sessions = len(self.sessions)
        total_messages = sum(len(session.messages) for session in self.sessions.values())
        total_escalations = sum(len(session.escalation_tickets) for session in self.sessions.values())
        total_tokens = sum(session.total_tokens for session in self.sessions.values())
        total_cache_hits = sum(session.cache_hits for session in self.sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_escalations": total_escalations,
            "total_tokens": total_tokens,
            "total_cache_hits": total_cache_hits,
            "cache_hit_rate": total_cache_hits / total_messages if total_messages > 0 else 0.0
        }
    
    def _start_auto_backup(self):
        if self.auto_backup_interval > 0:
            self._backup_thread = threading.Thread(target=self._auto_backup_worker, daemon=True)
            self._backup_thread.start()
            logger.info(f"Started auto-backup thread with {self.auto_backup_interval}s interval")
    
    def _auto_backup_worker(self):
        while not self._stop_backup:
            time.sleep(self.auto_backup_interval)
            if not self._stop_backup:
                with self._lock:
                    self.backup_sessions_to_file()
    
    def stop_auto_backup(self):
        self._stop_backup = True
        if self._backup_thread and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=5)
            logger.info("Stopped auto-backup thread")
    
    def __del__(self):
        self.stop_auto_backup()
        with self._lock:
            self.backup_sessions_to_file()


session_manager = SessionManager()