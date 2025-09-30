import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import asyncio
from functools import wraps

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
        self.error_details = {}


class SystemErrorHandler:
    def __init__(self):
        self.error_counts = {}
        self.fallback_history = []
        self.circuit_breakers = {}
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 1
        }
    
    def record_error(self, error_type: str, component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Dict[str, Any] = None):
        key = f"{component}:{error_type}"
        
        if key not in self.error_counts:
            self.error_counts[key] = {
                'count': 0,
                'first_occurrence': datetime.utcnow(),
                'last_occurrence': datetime.utcnow(),
                'severity': severity,
                'details': []
            }
        
        self.error_counts[key]['count'] += 1
        self.error_counts[key]['last_occurrence'] = datetime.utcnow()
        
        if details:
            self.error_counts[key]['details'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'details': details
            })
        
        if self.error_counts[key]['count'] >= self.error_thresholds[severity]:
            self._trigger_circuit_breaker(component, error_type, severity)
        
        logger.error(f"Error recorded: {error_type} in {component} (count: {self.error_counts[key]['count']})")
    
    def _trigger_circuit_breaker(self, component: str, error_type: str, severity: ErrorSeverity):
        key = f"{component}:{error_type}"
        
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = {
                'state': 'OPEN',
                'opened_at': datetime.utcnow(),
                'failure_count': self.error_counts[key]['count'],
                'severity': severity
            }
            
            logger.critical(f"Circuit breaker OPENED for {component}:{error_type} due to {severity.value} severity errors")
    
    def is_circuit_open(self, component: str, error_type: str) -> bool:
        key = f"{component}:{error_type}"
        
        if key not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[key]
        
        if breaker['state'] == 'OPEN':
            time_since_open = datetime.utcnow() - breaker['opened_at']
            
            if time_since_open > timedelta(minutes=5):
                breaker['state'] = 'HALF_OPEN'
                logger.info(f"Circuit breaker moved to HALF_OPEN for {component}:{error_type}")
                return False
            
            return True
        
        return False
    
    def record_success(self, component: str, error_type: str):
        key = f"{component}:{error_type}"
        
        if key in self.circuit_breakers:
            breaker = self.circuit_breakers[key]
            
            if breaker['state'] == 'HALF_OPEN':
                breaker['state'] = 'CLOSED'
                logger.info(f"Circuit breaker CLOSED for {component}:{error_type}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        return {
            'error_counts': {k: v for k, v in self.error_counts.items()},
            'circuit_breakers': {k: v for k, v in self.circuit_breakers.items()},
            'fallback_history': self.fallback_history[-20:],
            'timestamp': datetime.utcnow().isoformat()
        }


def with_error_handling(
    component: str,
    operation: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    fallback_func: Optional[Callable] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_context = ErrorContext(operation, component, severity)
            
            for attempt in range(max_retries + 1):
                try:
                    if system_error_handler.is_circuit_open(component, operation):
                        logger.warning(f"Circuit breaker open for {component}:{operation}, using fallback")
                        if fallback_func:
                            return await fallback_func(*args, **kwargs)
                        raise Exception(f"Circuit breaker open for {component}:{operation}")
                    
                    result = await func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Operation {operation} recovered after {attempt} retries")
                    
                    system_error_handler.record_success(component, operation)
                    return result
                
                except Exception as e:
                    error_context.retry_count = attempt
                    error_context.error_details = {'error': str(e), 'attempt': attempt}
                    
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {operation}, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    system_error_handler.record_error(operation, component, severity, error_context.error_details)
                    
                    if fallback_func:
                        logger.info(f"Using fallback for {operation} after {max_retries} failures")
                        error_context.fallback_used = True
                        system_error_handler.fallback_history.append({
                            'component': component,
                            'operation': operation,
                            'timestamp': datetime.utcnow().isoformat(),
                            'retry_count': attempt
                        })
                        return await fallback_func(*args, **kwargs)
                    
                    raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_context = ErrorContext(operation, component, severity)
            
            for attempt in range(max_retries + 1):
                try:
                    if system_error_handler.is_circuit_open(component, operation):
                        logger.warning(f"Circuit breaker open for {component}:{operation}, using fallback")
                        if fallback_func:
                            return fallback_func(*args, **kwargs)
                        raise Exception(f"Circuit breaker open for {component}:{operation}")
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Operation {operation} recovered after {attempt} retries")
                    
                    system_error_handler.record_success(component, operation)
                    return result
                
                except Exception as e:
                    error_context.retry_count = attempt
                    error_context.error_details = {'error': str(e), 'attempt': attempt}
                    
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {operation}, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                        continue
                    
                    system_error_handler.record_error(operation, component, severity, error_context.error_details)
                    
                    if fallback_func:
                        logger.info(f"Using fallback for {operation} after {max_retries} failures")
                        error_context.fallback_used = True
                        system_error_handler.fallback_history.append({
                            'component': component,
                            'operation': operation,
                            'timestamp': datetime.utcnow().isoformat(),
                            'retry_count': attempt
                        })
                        return fallback_func(*args, **kwargs)
                    
                    raise e
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def create_fallback_response(query: str, error_type: str = "general") -> str:
    fallback_responses = {
        "kong_gateway": "I'm currently experiencing connectivity issues with our AI gateway. Your request is being processed through our backup system, which may take slightly longer.",
        "llm_api": "I'm having trouble connecting to our AI models right now. Let me try to help you with a basic response, or you can try again in a moment.",
        "cache": "Our response caching system is temporarily unavailable, so responses may be slower than usual.",
        "sentiment": "I'm unable to analyze the sentiment of your message right now, but I'll do my best to help you.",
        "complexity": "I'm having trouble analyzing your query complexity, so I'll route it to our most capable model to ensure you get the best response.",
        "general": "I'm experiencing some technical difficulties, but I'm still here to help. Your request may take a bit longer to process."
    }
    
    return fallback_responses.get(error_type, fallback_responses["general"])


system_error_handler = SystemErrorHandler()