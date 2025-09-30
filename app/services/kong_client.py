import httpx
import json
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime


class KongServiceConfig(BaseModel):
    name: str
    url: str
    protocol: str = "https"
    host: str
    port: int = 443
    path: str


class KongRouteConfig(BaseModel):
    name: str
    service: str
    paths: List[str]
    methods: List[str]


class KongPluginConfig(BaseModel):
    name: str
    service: Optional[str] = None
    route: Optional[str] = None
    config: Dict[str, Any]


class KongHealthStatus(BaseModel):
    status: str
    database: Dict[str, Any]
    server: Dict[str, Any]
    plugins: Dict[str, Any]


class KongMetrics(BaseModel):
    total_requests: int
    cache_hits: int
    cache_misses: int
    avg_response_time: float
    error_rate: float
    timestamp: datetime


class KongClient:
    def __init__(self, admin_url: str = "http://localhost:8001"):
        self.admin_url = admin_url
        self.client = httpx.Client(timeout=30.0)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.admin_url}/status")
            return response.status_code == 200
        except Exception:
            return False

    async def get_services(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.admin_url}/services")
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception:
            return []

    async def get_routes(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.admin_url}/routes")
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception:
            return []

    async def get_plugins(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.admin_url}/plugins")
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception:
            return []

    async def create_service(self, service: KongServiceConfig) -> Dict[str, Any]:
        try:
            response = await self.client.post(
                f"{self.admin_url}/services",
                json=service.dict()
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def create_route(self, route: KongRouteConfig) -> Dict[str, Any]:
        try:
            response = await self.client.post(
                f"{self.admin_url}/routes",
                json=route.dict()
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def create_plugin(self, plugin: KongPluginConfig) -> Dict[str, Any]:
        try:
            response = await self.client.post(
                f"{self.admin_url}/plugins",
                json=plugin.dict(exclude_none=True)
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def proxy_request(self, path: str, method: str = "POST", data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        try:
            proxy_url = f"http://localhost:8000{path}"
            
            if headers is None:
                headers = {}
            
            if method.upper() == "POST":
                response = await self.client.post(proxy_url, json=data, headers=headers)
            elif method.upper() == "GET":
                response = await self.client.get(proxy_url, headers=headers)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_ai_analytics(self) -> Dict[str, Any]:
        try:
            plugins = await self.get_plugins()
            ai_plugins = [p for p in plugins if p.get("name", "").startswith("ai-")]
            
            analytics = {
                "total_ai_plugins": len(ai_plugins),
                "plugins": ai_plugins,
                "cache_stats": {},
                "rate_limit_stats": {}
            }
            
            for plugin in ai_plugins:
                if plugin.get("name") == "ai-semantic-cache":
                    analytics["cache_stats"][plugin.get("service", {}).get("name", "unknown")] = {
                        "enabled": plugin.get("enabled", False),
                        "config": plugin.get("config", {})
                    }
                elif plugin.get("name") == "ai-rate-limiting-advanced":
                    analytics["rate_limit_stats"][plugin.get("service", {}).get("name", "unknown")] = {
                        "enabled": plugin.get("enabled", False),
                        "config": plugin.get("config", {})
                    }
            
            return analytics
        except Exception as e:
            return {"error": str(e)}

    async def route_to_model(self, query: str, model_type: str = "simple") -> Dict[str, Any]:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return {"error": "GROQ_API_KEY not configured"}

        model_routes = {
            "simple": "/ai/simple",
            "complex": "/ai/complex", 
            "fallback": "/ai/fallback"
        }
        
        route_path = model_routes.get(model_type, "/ai/simple")
        
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": query}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        return await self.proxy_request(route_path, "POST", payload, headers)

    def close(self):
        self.client.close()


kong_client = KongClient()