import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from app.services.cache_service import semantic_cache, performance_metrics

logger = logging.getLogger(__name__)

class KongPerformanceOptimizer:
    def __init__(self):
        self.kong_admin_url = "http://localhost:8001"
        self.kong_proxy_url = "http://localhost:8000"
        self.optimization_history: List[Dict[str, Any]] = []
        
    async def check_kong_performance(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = time.time()
                
                status_response = await client.get(f"{self.kong_admin_url}/status")
                kong_response_time = (time.time() - start_time) * 1000
                
                if status_response.status_code != 200:
                    return {
                        "status": "unhealthy",
                        "kong_available": False,
                        "error": f"Kong status check failed: {status_response.status_code}"
                    }
                
                status_data = status_response.json()
                
                plugins_response = await client.get(f"{self.kong_admin_url}/plugins")
                plugins_data = plugins_response.json() if plugins_response.status_code == 200 else {"data": []}
                
                ai_plugins = [p for p in plugins_data.get("data", []) if "ai-" in p.get("name", "")]
                
                return {
                    "status": "healthy",
                    "kong_available": True,
                    "kong_response_time_ms": kong_response_time,
                    "server_stats": status_data.get("server", {}),
                    "database_stats": status_data.get("database", {}),
                    "ai_plugins_count": len(ai_plugins),
                    "ai_plugins": [p["name"] for p in ai_plugins],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Kong performance check failed: {e}")
            return {
                "status": "error",
                "kong_available": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def optimize_cache_settings(self) -> Dict[str, Any]:
        cache_stats = semantic_cache.get_stats()
        recent_metrics = performance_metrics.get_recent_metrics(10)
        
        optimization_actions = []
        
        current_threshold = cache_stats['similarity_threshold']
        cache_hit_rate = recent_metrics.get('recent_cache_hit_rate', 0)
        avg_response_time = recent_metrics.get('recent_avg_response_time_ms', 0)
        
        if cache_hit_rate < 0.3 and current_threshold > 0.75:
            new_threshold = max(0.75, current_threshold - 0.05)
            semantic_cache.similarity_threshold = new_threshold
            optimization_actions.append({
                "action": "lowered_similarity_threshold",
                "old_value": current_threshold,
                "new_value": new_threshold,
                "reason": f"Low cache hit rate ({cache_hit_rate:.3f})"
            })
        
        elif cache_hit_rate > 0.7 and avg_response_time > 1000 and current_threshold < 0.90:
            new_threshold = min(0.90, current_threshold + 0.02)
            semantic_cache.similarity_threshold = new_threshold
            optimization_actions.append({
                "action": "raised_similarity_threshold",
                "old_value": current_threshold,
                "new_value": new_threshold,
                "reason": f"High cache hit rate ({cache_hit_rate:.3f}) but slow responses"
            })
        
        cache_utilization = cache_stats['active_entries'] / cache_stats['cache_size_limit']
        if cache_utilization > 0.9:
            semantic_cache.max_cache_size = min(2000, cache_stats['cache_size_limit'] + 200)
            optimization_actions.append({
                "action": "increased_cache_size",
                "old_value": cache_stats['cache_size_limit'],
                "new_value": semantic_cache.max_cache_size,
                "reason": f"High cache utilization ({cache_utilization:.3f})"
            })
        
        optimization_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats_before": cache_stats,
            "recent_metrics": recent_metrics,
            "optimizations_applied": optimization_actions,
            "cache_stats_after": semantic_cache.get_stats()
        }
        
        self.optimization_history.append(optimization_result)
        
        if len(self.optimization_history) > 50:
            self.optimization_history = self.optimization_history[-25:]
        
        return optimization_result
    
    async def optimize_kong_routing(self) -> Dict[str, Any]:
        try:
            summary_stats = performance_metrics.get_summary_stats()
            model_usage = summary_stats.get('model_usage_counts', {})
            
            recommendations = []
            
            total_requests = sum(model_usage.values()) if model_usage else 0
            
            if total_requests > 0:
                simple_model_usage = model_usage.get('llama-3.3-70b-versatile', 0) / total_requests
                complex_model_usage = model_usage.get('openai/gpt-oss-120b', 0) / total_requests
                fallback_usage = model_usage.get('llama-3.1-8b-instant', 0) / total_requests
                
                if fallback_usage > 0.2:
                    recommendations.append({
                        "type": "high_fallback_usage",
                        "message": f"High fallback model usage ({fallback_usage:.1%}). Check Kong Gateway connectivity.",
                        "priority": "high"
                    })
                
                if simple_model_usage < 0.3:
                    recommendations.append({
                        "type": "low_simple_model_usage",
                        "message": f"Low simple model usage ({simple_model_usage:.1%}). Consider adjusting complexity thresholds.",
                        "priority": "medium"
                    })
                
                if complex_model_usage > 0.6:
                    recommendations.append({
                        "type": "high_complex_model_usage",
                        "message": f"High complex model usage ({complex_model_usage:.1%}). This may increase costs.",
                        "priority": "medium"
                    })
            
            avg_response_time = summary_stats.get('avg_response_time_ms', 0)
            if avg_response_time > 2000:
                recommendations.append({
                    "type": "slow_response_times",
                    "message": f"Average response time is {avg_response_time:.0f}ms. Consider optimizing model selection.",
                    "priority": "high"
                })
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "model_usage_analysis": {
                    "total_requests": total_requests,
                    "simple_model_percentage": simple_model_usage * 100 if total_requests > 0 else 0,
                    "complex_model_percentage": complex_model_usage * 100 if total_requests > 0 else 0,
                    "fallback_percentage": fallback_usage * 100 if total_requests > 0 else 0
                },
                "performance_analysis": {
                    "avg_response_time_ms": avg_response_time,
                    "cache_hit_rate": summary_stats.get('cache_hit_rate', 0),
                    "error_rate": summary_stats.get('error_rate', 0)
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Kong routing optimization failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "recommendations": []
            }
    
    async def run_performance_optimization(self) -> Dict[str, Any]:
        kong_health = await self.check_kong_performance()
        cache_optimization = await self.optimize_cache_settings()
        routing_optimization = await self.optimize_kong_routing()
        
        overall_health_score = 100
        
        if not kong_health.get('kong_available', False):
            overall_health_score -= 30
        
        if kong_health.get('kong_response_time_ms', 0) > 1000:
            overall_health_score -= 15
        
        cache_hit_rate = cache_optimization.get('recent_metrics', {}).get('recent_cache_hit_rate', 0)
        if cache_hit_rate < 0.3:
            overall_health_score -= 20
        
        high_priority_recommendations = [
            r for r in routing_optimization.get('recommendations', [])
            if r.get('priority') == 'high'
        ]
        overall_health_score -= len(high_priority_recommendations) * 10
        
        optimization_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health_score": max(0, overall_health_score),
            "kong_health": kong_health,
            "cache_optimization": cache_optimization,
            "routing_optimization": routing_optimization,
            "optimizations_applied": len(cache_optimization.get('optimizations_applied', [])),
            "recommendations_count": len(routing_optimization.get('recommendations', []))
        }
        
        logger.info(f"Performance optimization completed. Health score: {overall_health_score}/100")
        
        return optimization_summary
    
    def get_optimization_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            opt for opt in self.optimization_history
            if datetime.fromisoformat(opt['timestamp']) > cutoff_time
        ]

class PerformanceScheduler:
    def __init__(self, optimizer: KongPerformanceOptimizer):
        self.optimizer = optimizer
        self.scheduler_active = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
    async def start_scheduled_optimization(self, interval_minutes: int = 15):
        if self.scheduler_active:
            logger.warning("Performance scheduler already active")
            return
        
        self.scheduler_active = True
        self.scheduler_task = asyncio.create_task(
            self._optimization_loop(interval_minutes * 60)
        )
        logger.info(f"Performance optimization scheduler started (every {interval_minutes} minutes)")
    
    async def stop_scheduled_optimization(self):
        if not self.scheduler_active:
            return
        
        self.scheduler_active = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance optimization scheduler stopped")
    
    async def _optimization_loop(self, interval_seconds: int):
        while self.scheduler_active:
            try:
                await self.optimizer.run_performance_optimization()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(interval_seconds)

kong_optimizer = KongPerformanceOptimizer()
performance_scheduler = PerformanceScheduler(kong_optimizer)