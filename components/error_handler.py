import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import logging
import time
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FallbackStrategy(Enum):
    RETRY = "retry"
    FALLBACK_SERVICE = "fallback_service"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAIL_FAST = "fail_fast"


class ErrorContext:
    def __init__(self, operation: str, component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.operation = operation
        self.component = component
        self.severity = severity
        self.timestamp = datetime.utcnow()
        self.retry_count = 0
        self.fallback_used = False


class ErrorHandler:
    _error_counts = {}
    _fallback_history = []
    
    @staticmethod
    def display_error(error_data: Dict[str, Any], context: str = "Operation"):
        error_type = error_data.get("error_type", "UNKNOWN_ERROR")
        message = error_data.get("message", "An unknown error occurred")
        status_code = error_data.get("status_code")
        fallback_used = error_data.get("fallback_used", False)
        retry_count = error_data.get("retry_count", 0)
        
        ErrorHandler._track_error(error_type, context)
        
        if error_type == "KONG_GATEWAY_ERROR":
            st.error(f"🌉 Kong Gateway Error: {message}")
            if fallback_used:
                st.info("✅ Automatically switched to direct API connection")
            else:
                st.warning("⚠️ Kong Gateway unavailable - some features may be limited")
            
            with st.expander("🔧 Kong Gateway Troubleshooting"):
                st.markdown("""
                **Kong Gateway Issues:**
                1. Check if Kong is running: `docker ps | grep kong`
                2. Verify Kong admin API: http://localhost:8001/status
                3. Check Kong proxy: http://localhost:8000
                4. Review Kong configuration and plugins
                5. Check Docker network connectivity
                """)
        
        elif error_type == "LLM_API_ERROR":
            st.error(f"🤖 AI Model Error: {message}")
            if fallback_used:
                st.info("✅ Switched to fallback model for continued service")
            if retry_count > 0:
                st.caption(f"Retried {retry_count} times")
            
            with st.expander("🔧 AI Model Troubleshooting"):
                st.markdown("""
                **AI Model Issues:**
                1. Check Groq API key configuration
                2. Verify model availability and quotas
                3. Check network connectivity to Groq API
                4. Review rate limiting settings
                """)
        
        elif error_type == "CACHE_ERROR":
            st.warning(f"💾 Cache Error: {message}")
            st.info("Continuing without cache - responses may be slower")
            
        elif error_type == "SENTIMENT_ANALYSIS_ERROR":
            st.warning(f"😐 Sentiment Analysis Error: {message}")
            st.info("Using neutral sentiment for this query")
            
        elif error_type == "CONNECTION_ERROR":
            st.error(f"🔌 Connection Error: {message}")
            st.info("💡 Please ensure the backend API is running on http://localhost:8080")
            
            with st.expander("🔧 Connection Troubleshooting"):
                st.markdown("""
                **Common solutions:**
                1. Check if the FastAPI backend is running: `python main.py`
                2. Verify the backend is accessible at http://localhost:8080
                3. Check your network connection
                4. Ensure no firewall is blocking the connection
                5. Try restarting the backend service
                """)
                
                if st.button("🔄 Retry Connection"):
                    st.rerun()
        
        elif error_type == "VALIDATION_ERROR":
            st.error(f"📝 Validation Error: {message}")
            st.warning("Please check your input and try again")
        
        elif error_type == "NOT_FOUND_ERROR":
            st.error(f"🔍 Not Found: {message}")
            st.info("The requested resource could not be found")
        
        elif error_type == "TIMEOUT_ERROR":
            st.error(f"⏱️ Timeout Error: {message}")
            st.warning("The request took too long to complete. Please try again.")
            if retry_count > 0:
                st.caption(f"Retried {retry_count} times")
        
        elif error_type == "RATE_LIMIT_ERROR":
            st.error(f"🚦 Rate Limit Error: {message}")
            st.warning("Too many requests. Please wait before trying again.")
            
        elif error_type == "API_ERROR":
            st.error(f"⚠️ API Error: {message}")
            if status_code:
                st.caption(f"Status Code: {status_code}")
        
        else:
            st.error(f"❌ {context} Failed: {message}")
            if status_code:
                st.caption(f"Status Code: {status_code}")
        
        if fallback_used:
            st.success("🔄 Fallback system activated - service continues with reduced functionality")
        
        logger.error(f"{context} failed: {error_type} - {message} (retry_count: {retry_count}, fallback_used: {fallback_used})")
    
    @staticmethod
    def _track_error(error_type: str, context: str):
        key = f"{error_type}:{context}"
        ErrorHandler._error_counts[key] = ErrorHandler._error_counts.get(key, 0) + 1
        
        if ErrorHandler._error_counts[key] > 5:
            logger.warning(f"High error frequency detected: {key} occurred {ErrorHandler._error_counts[key]} times")
    
    @staticmethod
    def get_error_statistics() -> Dict[str, Any]:
        return {
            "error_counts": ErrorHandler._error_counts.copy(),
            "fallback_history": ErrorHandler._fallback_history[-10:],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def handle_api_response(response_data: Dict[str, Any], success_message: Optional[str] = None, context: str = "Operation") -> bool:
        if response_data.get("error"):
            ErrorHandler.display_error(response_data, context)
            return False
        else:
            if success_message:
                st.success(success_message)
            return True
    
    @staticmethod
    def with_error_handling(func, *args, context: str = "Operation", success_message: Optional[str] = None, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            if isinstance(result, dict) and result.get("error"):
                ErrorHandler.display_error(result, context)
                return None
            else:
                if success_message:
                    st.success(success_message)
                return result
                
        except Exception as e:
            error_data = {
                "error_type": "EXCEPTION_ERROR",
                "message": str(e)
            }
            ErrorHandler.display_error(error_data, context)
            logger.exception(f"Exception in {context}: {e}")
            return None
    
    @staticmethod
    def display_connection_status(api_client):
        try:
            health_response = api_client.health_check()
            
            if health_response.success:
                st.success("🟢 Backend API Connected")
                return True
            else:
                st.error("🔴 Backend API Disconnected")
                ErrorHandler.display_error({
                    "error_type": health_response.error_type,
                    "message": health_response.error
                }, "API Health Check")
                return False
                
        except Exception as e:
            st.error("🔴 Backend API Connection Failed")
            st.error(f"Exception: {str(e)}")
            return False
    
    @staticmethod
    def safe_api_call(api_client, method_name: str, *args, context: str = None, max_retries: int = 3, **kwargs):
        context = context or f"API call to {method_name}"
        
        for attempt in range(max_retries + 1):
            try:
                method = getattr(api_client, method_name)
                response = method(*args, **kwargs)
                
                if hasattr(response, 'success'):
                    if response.success:
                        return response.data
                    else:
                        if attempt < max_retries and ErrorHandler._should_retry(response.error_type):
                            time.sleep(2 ** attempt)
                            continue
                        
                        ErrorHandler.display_error({
                            "error_type": response.error_type,
                            "message": response.error,
                            "status_code": response.status_code,
                            "retry_count": attempt
                        }, context)
                        return None
                else:
                    if response.get("error"):
                        if attempt < max_retries and ErrorHandler._should_retry(response.get("error_type", "UNKNOWN")):
                            time.sleep(2 ** attempt)
                            continue
                        
                        response["retry_count"] = attempt
                        ErrorHandler.display_error(response, context)
                        return None
                    else:
                        return response
                        
            except AttributeError:
                st.error(f"❌ API method '{method_name}' not found")
                return None
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                
                ErrorHandler.display_error({
                    "error_type": "EXCEPTION_ERROR",
                    "message": str(e),
                    "retry_count": attempt
                }, context)
                return None
        
        return None
    
    @staticmethod
    def _should_retry(error_type: str) -> bool:
        retryable_errors = {
            "CONNECTION_ERROR",
            "TIMEOUT_ERROR", 
            "RATE_LIMIT_ERROR",
            "KONG_GATEWAY_ERROR",
            "LLM_API_ERROR"
        }
        return error_type in retryable_errors
    
    @staticmethod
    def with_fallback(primary_func: Callable, fallback_func: Callable, context: str = "Operation", **kwargs):
        try:
            result = primary_func(**kwargs)
            if result is not None:
                return result
        except Exception as e:
            logger.warning(f"Primary function failed in {context}: {e}")
        
        try:
            logger.info(f"Attempting fallback for {context}")
            result = fallback_func(**kwargs)
            
            ErrorHandler._fallback_history.append({
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "fallback_used": True
            })
            
            if result is not None:
                st.info(f"✅ Fallback successful for {context}")
                return result
        except Exception as e:
            logger.error(f"Fallback also failed in {context}: {e}")
        
        ErrorHandler.display_error({
            "error_type": "FALLBACK_FAILED",
            "message": f"Both primary and fallback methods failed for {context}",
            "fallback_used": True
        }, context)
        return None


def display_error_message(error_msg: str, error_type: str = "ERROR"):
    ErrorHandler.display_error({
        "error_type": error_type,
        "message": error_msg
    })


def handle_api_error(response_data: Dict[str, Any], context: str = "API Operation") -> bool:
    return ErrorHandler.handle_api_response(response_data, context=context)