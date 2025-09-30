import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, message: str, error_type: str = "API_ERROR", status_code: int = None):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(self.message)


class ConnectionError(APIError):
    def __init__(self, message: str):
        super().__init__(message, "CONNECTION_ERROR")


class ValidationError(APIError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class NotFoundError(APIError):
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND_ERROR", 404)


@dataclass
class APIResponse:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    status_code: Optional[int] = None


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return APIResponse(success=True, data=data, status_code=response.status_code)
                except json.JSONDecodeError:
                    return APIResponse(success=True, data={"message": response.text}, status_code=response.status_code)
            
            elif response.status_code == 404:
                error_msg = f"Resource not found: {endpoint}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    pass
                return APIResponse(
                    success=False, 
                    error=error_msg, 
                    error_type="NOT_FOUND_ERROR",
                    status_code=response.status_code
                )
            
            elif response.status_code == 422:
                error_msg = "Validation error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    pass
                return APIResponse(
                    success=False, 
                    error=error_msg, 
                    error_type="VALIDATION_ERROR",
                    status_code=response.status_code
                )
            
            else:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                    error_type = error_data.get('error_type', 'API_ERROR')
                except:
                    error_type = 'API_ERROR'
                
                return APIResponse(
                    success=False, 
                    error=error_msg, 
                    error_type=error_type,
                    status_code=response.status_code
                )
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection failed to {self.base_url}. Please ensure the backend API is running."
            logger.error(f"Connection error: {e}")
            return APIResponse(
                success=False, 
                error=error_msg, 
                error_type="CONNECTION_ERROR"
            )
        
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(f"Timeout error: {e}")
            return APIResponse(
                success=False, 
                error=error_msg, 
                error_type="TIMEOUT_ERROR"
            )
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(f"Request error: {e}")
            return APIResponse(
                success=False, 
                error=error_msg, 
                error_type="REQUEST_ERROR"
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return APIResponse(
                success=False, 
                error=error_msg, 
                error_type="UNKNOWN_ERROR"
            )
    
    def health_check(self) -> APIResponse:
        return self._make_request('GET', '/health')
    
    def query(self, message: str, session_id: Optional[str] = None, customer_id: Optional[str] = None) -> APIResponse:
        payload = {
            "query": message,
            "session_id": session_id,
            "customer_id": customer_id
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self._make_request('POST', '/api/query', json=payload)
    
    def analyze_query(self, message: str, session_id: Optional[str] = None, customer_id: Optional[str] = None) -> APIResponse:
        payload = {
            "query": message,
            "session_id": session_id,
            "customer_id": customer_id
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self._make_request('POST', '/api/query/analyze', json=payload)
    
    def get_query_metrics(self) -> APIResponse:
        return self._make_request('GET', '/api/query/metrics')
    
    def get_cache_stats(self) -> APIResponse:
        return self._make_request('GET', '/api/query/cache/stats')
    
    def clear_cache(self) -> APIResponse:
        return self._make_request('POST', '/api/query/cache/clear')
    
    def create_session(self, customer_id: str, session_id: Optional[str] = None) -> APIResponse:
        payload = {
            "customer_id": customer_id,
            "session_id": session_id
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self._make_request('POST', '/api/session/create', json=payload)
    
    def get_session(self, session_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/session/{session_id}')
    
    def get_customer_sessions(self, customer_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/session/customer/{customer_id}')
    
    def export_session(self, session_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/session/{session_id}/export')
    
    def backup_sessions(self) -> APIResponse:
        return self._make_request('POST', '/api/session/backup')
    
    def restore_sessions(self) -> APIResponse:
        return self._make_request('POST', '/api/session/restore')
    
    def get_session_statistics(self) -> APIResponse:
        return self._make_request('GET', '/api/session/stats/overview')
    
    def delete_session(self, session_id: str) -> APIResponse:
        return self._make_request('DELETE', f'/api/session/{session_id}')
    
    def update_session(self, session_id: str, total_cost: Optional[float] = None, customer_id: Optional[str] = None) -> APIResponse:
        payload = {
            "total_cost": total_cost,
            "customer_id": customer_id
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        if not payload:
            return APIResponse(success=False, error="No valid fields provided for update", error_type="VALIDATION_ERROR")
        
        return self._make_request('PUT', f'/api/session/{session_id}', json=payload)
    
    def get_session_threads(self, session_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/session/{session_id}/threads')
    
    def get_conversation_thread(self, session_id: str, thread_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/session/{session_id}/thread/{thread_id}')
    
    def cleanup_old_sessions(self, days_old: int = 30) -> APIResponse:
        return self._make_request('POST', f'/api/session/cleanup?days_old={days_old}')
    
    def create_escalation(self, customer_id: str, conversation_history: List[Dict], escalation_reasons: List[str], escalation_score: float) -> APIResponse:
        payload = {
            "customer_id": customer_id,
            "conversation_history": conversation_history,
            "escalation_reasons": escalation_reasons,
            "escalation_score": escalation_score
        }
        
        return self._make_request('POST', '/api/escalation/create', json=payload)
    
    def check_escalation_needed(self, complexity_score: float, sentiment_score: float) -> APIResponse:
        return self._make_request('GET', f'/api/escalation/check/{complexity_score}/{sentiment_score}')
    
    def get_customer_escalations(self, customer_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/escalation/customer/{customer_id}')
    
    def get_all_escalations(self) -> APIResponse:
        return self._make_request('GET', '/api/escalation/all')
    
    def update_escalation_ticket_status(self, ticket_id: str, status: str) -> APIResponse:
        payload = {
            "ticket_id": ticket_id,
            "status": status
        }
        
        return self._make_request('PUT', '/api/escalation/ticket/status', json=payload)
    
    def create_manual_escalation(self, customer_id: str, reason: str = "Manual escalation requested") -> APIResponse:
        return self._make_request('POST', f'/api/escalation/manual?customer_id={customer_id}&reason={reason}')
    
    def log_crm_interaction(self, customer_id: str, query: str, response: str, **kwargs) -> APIResponse:
        payload = {
            "customer_id": customer_id,
            "query": query,
            "response": response,
            **kwargs
        }
        
        return self._make_request('POST', '/api/crm/interactions/log', json=payload)
    
    def get_customer_interactions(self, customer_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/crm/interactions/{customer_id}')
    
    def create_crm_ticket(self, ticket_data: Dict[str, Any]) -> APIResponse:
        return self._make_request('POST', '/api/crm/tickets', json=ticket_data)
    
    def get_all_crm_tickets(self, status: Optional[str] = None) -> APIResponse:
        endpoint = '/api/crm/tickets'
        if status:
            endpoint += f'?status={status}'
        return self._make_request('GET', endpoint)
    
    def get_crm_ticket(self, ticket_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/crm/tickets/{ticket_id}')
    
    def update_crm_ticket_status(self, ticket_id: str, status: str) -> APIResponse:
        payload = {"status": status}
        return self._make_request('PUT', f'/api/crm/tickets/{ticket_id}/status', json=payload)
    
    def get_customer_crm_tickets(self, customer_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/crm/tickets/customer/{customer_id}')
    
    def export_customer_crm_data(self, customer_id: str) -> APIResponse:
        return self._make_request('GET', f'/api/crm/export/customer/{customer_id}')
    
    def export_all_crm_data(self) -> APIResponse:
        return self._make_request('GET', '/api/crm/export/all')
    
    def get_crm_statistics(self) -> APIResponse:
        return self._make_request('GET', '/api/crm/statistics')
    
    def backup_crm_data(self) -> APIResponse:
        return self._make_request('POST', '/api/crm/backup')
    
    def get_performance_health(self) -> APIResponse:
        return self._make_request('GET', '/performance/health')
    
    def get_performance_alerts(self) -> APIResponse:
        return self._make_request('GET', '/performance/alerts')
    
    def run_performance_optimization(self) -> APIResponse:
        return self._make_request('GET', '/performance/optimize')
    
    def get_kong_performance(self) -> APIResponse:
        return self._make_request('GET', '/performance/kong')
    
    def get_optimization_history(self) -> APIResponse:
        return self._make_request('GET', '/performance/history')


class StreamlitAPIClient(APIClient):
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        super().__init__(base_url, timeout)
    
    def handle_response(self, response: APIResponse) -> Dict[str, Any]:
        if response.success:
            return response.data
        else:
            return {
                "error": True,
                "message": response.error,
                "error_type": response.error_type,
                "status_code": response.status_code
            }
    
    def query_with_error_handling(self, message: str, session_id: Optional[str] = None, customer_id: Optional[str] = None) -> Dict[str, Any]:
        response = self.query(message, session_id, customer_id)
        return self.handle_response(response)
    
    def get_session_with_error_handling(self, session_id: str) -> Dict[str, Any]:
        response = self.get_session(session_id)
        return self.handle_response(response)
    
    def create_session_with_error_handling(self, customer_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        response = self.create_session(customer_id, session_id)
        return self.handle_response(response)
    
    def export_session_with_error_handling(self, session_id: str) -> Dict[str, Any]:
        response = self.export_session(session_id)
        return self.handle_response(response)
    
    def get_metrics_with_error_handling(self) -> Dict[str, Any]:
        response = self.get_query_metrics()
        return self.handle_response(response)
    
    def get_escalations_with_error_handling(self, customer_id: str) -> Dict[str, Any]:
        response = self.get_customer_escalations(customer_id)
        return self.handle_response(response)
    
    def create_manual_escalation_with_error_handling(self, customer_id: str, reason: str = "Manual escalation requested") -> Dict[str, Any]:
        response = self.create_manual_escalation(customer_id, reason)
        return self.handle_response(response)
    
    def get_crm_data_with_error_handling(self, customer_id: str) -> Dict[str, Any]:
        response = self.export_customer_crm_data(customer_id)
        return self.handle_response(response)
    
    def get_performance_data_with_error_handling(self) -> Dict[str, Any]:
        health_response = self.get_performance_health()
        alerts_response = self.get_performance_alerts()
        kong_response = self.get_kong_performance()
        
        return {
            "health": self.handle_response(health_response),
            "alerts": self.handle_response(alerts_response),
            "kong": self.handle_response(kong_response)
        }