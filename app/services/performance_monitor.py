import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import httpx

from app.services.cache_service import performance_metrics, semantic_cache

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_thresholds = {
            'max_response_time_ms': 5000,
            'min_cache_hit_rate': 0.3,
            'max_error_rate': 0.1,
            'max_avg_response_time_ms': 2000
        }
        self.alerts: List[Dict[str, Any]] = []
    
    async def start_monitoring(self, interval_seconds: int = 60):
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Performance monitoring started with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        while self.monitoring_active:
            try:
                await self._check_performance_metrics()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _check_performance_metrics(self):
        try:
            recent_stats = performance_metrics.get_recent_metrics(5)
            summary_stats = performance_metrics.get_summary_stats()
            
            alerts_triggered = []
            
            if recent_stats['recent_avg_response_time_ms'] > self.alert_thresholds['max_avg_response_time_ms']:
                alerts_triggered.append({
                    'type': 'high_response_time',
                    'message': f"Average response time {recent_stats['recent_avg_response_time_ms']:.2f}ms exceeds threshold {self.alert_thresholds['max_avg_response_time_ms']}ms",
                    'value': recent_stats['recent_avg_response_time_ms'],
                    'threshold': self.alert_thresholds['max_avg_response_time_ms']
                })
            
            if recent_stats['recent_cache_hit_rate'] < self.alert_thresholds['min_cache_hit_rate']:
                alerts_triggered.append({
                    'type': 'low_cache_hit_rate',
                    'message': f"Cache hit rate {recent_stats['recent_cache_hit_rate']:.3f} below threshold {self.alert_thresholds['min_cache_hit_rate']:.3f}",
                    'value': recent_stats['recent_cache_hit_rate'],
                    'threshold': self.alert_thresholds['min_cache_hit_rate']
                })
            
            if recent_stats['recent_error_rate'] > self.alert_thresholds['max_error_rate']:
                alerts_triggered.append({
                    'type': 'high_error_rate',
                    'message': f"Error rate {recent_stats['recent_error_rate']:.3f} exceeds threshold {self.alert_thresholds['max_error_rate']:.3f}",
                    'value': recent_stats['recent_error_rate'],
                    'threshold': self.alert_thresholds['max_error_rate']
                })
            
            for alert in alerts_triggered:
                alert['timestamp'] = datetime.utcnow().isoformat()
                self.alerts.append(alert)
                logger.warning(f"Performance alert: {alert['message']}")
            
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-50:]
            
            await self._check_kong_health()
            
        except Exception as e:
            logger.error(f"Error checking performance metrics: {e}")
    
    async def _check_kong_health(self):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/status")
                if response.status_code != 200:
                    self.alerts.append({
                        'type': 'kong_health_check_failed',
                        'message': f"Kong health check failed with status {response.status_code}",
                        'timestamp': datetime.utcnow().isoformat()
                    })
        except Exception as e:
            self.alerts.append({
                'type': 'kong_connection_failed',
                'message': f"Kong connection failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def get_alerts(self, hours: int = 1) -> List[Dict[str, Any]]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def get_system_health(self) -> Dict[str, Any]:
        recent_stats = performance_metrics.get_recent_metrics(5)
        cache_stats = semantic_cache.get_stats()
        recent_alerts = self.get_alerts(1)
        
        health_score = 100
        
        if recent_stats['recent_avg_response_time_ms'] > self.alert_thresholds['max_avg_response_time_ms']:
            health_score -= 20
        
        if recent_stats['recent_cache_hit_rate'] < self.alert_thresholds['min_cache_hit_rate']:
            health_score -= 15
        
        if recent_stats['recent_error_rate'] > self.alert_thresholds['max_error_rate']:
            health_score -= 25
        
        if len(recent_alerts) > 5:
            health_score -= 10
        
        health_status = "excellent" if health_score >= 90 else \
                      "good" if health_score >= 70 else \
                      "fair" if health_score >= 50 else "poor"
        
        return {
            'health_score': max(0, health_score),
            'health_status': health_status,
            'recent_alerts_count': len(recent_alerts),
            'cache_efficiency': cache_stats['active_entries'] / cache_stats['cache_size_limit'],
            'monitoring_active': self.monitoring_active,
            'timestamp': datetime.utcnow().isoformat()
        }

@asynccontextmanager
async def performance_context(operation_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        performance_metrics.record_response_time(operation_name, duration_ms)

class ResponseTimeOptimizer:
    @staticmethod
    async def optimize_query_processing():
        cache_stats = semantic_cache.get_stats()
        
        if cache_stats['active_entries'] < cache_stats['cache_size_limit'] * 0.8:
            return {
                'action': 'increase_cache_size',
                'recommendation': 'Cache utilization is low, consider increasing similarity threshold'
            }
        
        recent_stats = performance_metrics.get_recent_metrics(10)
        
        if recent_stats['recent_cache_hit_rate'] < 0.3:
            return {
                'action': 'adjust_similarity_threshold',
                'recommendation': 'Low cache hit rate, consider lowering similarity threshold to 0.80'
            }
        
        if recent_stats['recent_avg_response_time_ms'] > 2000:
            return {
                'action': 'optimize_model_selection',
                'recommendation': 'High response times, consider using faster models for simple queries'
            }
        
        return {
            'action': 'no_optimization_needed',
            'recommendation': 'System performance is within acceptable parameters'
        }

performance_monitor = PerformanceMonitor()
response_optimizer = ResponseTimeOptimizer()