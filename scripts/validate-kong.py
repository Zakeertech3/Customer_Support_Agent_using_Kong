import asyncio
import httpx
import json
import os
from typing import Dict, Any


async def check_kong_health() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/status")
            return response.status_code == 200
    except Exception as e:
        print(f"Kong health check failed: {e}")
        return False


async def validate_services() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/services")
            if response.status_code == 200:
                services = response.json().get("data", [])
                expected_services = ["groq-llama-simple", "groq-gpt-complex", "groq-llama-fallback"]
                found_services = [s["name"] for s in services]
                
                return {
                    "status": "success",
                    "expected": expected_services,
                    "found": found_services,
                    "missing": [s for s in expected_services if s not in found_services]
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def validate_routes() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/routes")
            if response.status_code == 200:
                routes = response.json().get("data", [])
                expected_routes = ["ai-simple-route", "ai-complex-route", "ai-fallback-route"]
                found_routes = [r["name"] for r in routes]
                
                return {
                    "status": "success",
                    "expected": expected_routes,
                    "found": found_routes,
                    "missing": [r for r in expected_routes if r not in found_routes]
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def validate_plugins() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/plugins")
            if response.status_code == 200:
                plugins = response.json().get("data", [])
                expected_plugins = ["ai-proxy-advanced", "ai-semantic-cache", "ai-prompt-guard", "ai-rate-limiting-advanced"]
                found_plugins = [p["name"] for p in plugins]
                
                plugin_counts = {}
                for plugin in plugins:
                    name = plugin["name"]
                    plugin_counts[name] = plugin_counts.get(name, 0) + 1
                
                return {
                    "status": "success",
                    "expected": expected_plugins,
                    "found": list(set(found_plugins)),
                    "counts": plugin_counts,
                    "missing": [p for p in expected_plugins if p not in found_plugins]
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def test_chromadb() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8003/api/v1/heartbeat")
            if response.status_code == 200:
                return {"status": "success", "message": "ChromaDB is running"}
            else:
                return {"status": "error", "message": f"ChromaDB HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"ChromaDB connection failed: {e}"}


async def test_groq_integration() -> Dict[str, Any]:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"status": "error", "message": "GROQ_API_KEY not set"}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [{"role": "user", "content": "Hello, this is a test"}],
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 50
            }
            
            response = await client.post(
                "http://localhost:8000/ai/simple",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {"status": "success", "message": "Groq integration working"}
            else:
                return {"status": "error", "message": f"Groq test failed: HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Groq test failed: {e}"}


async def main():
    print("Kong AI Gateway Validation")
    print("=" * 40)
    
    print("\n1. Checking Kong health...")
    health = await check_kong_health()
    print(f"   Kong Health: {'✓ OK' if health else '✗ FAILED'}")
    
    if not health:
        print("Kong is not running. Please start Kong first.")
        return
    
    print("\n2. Validating services...")
    services = await validate_services()
    if services["status"] == "success":
        print(f"   Services: ✓ {len(services['found'])}/{len(services['expected'])} found")
        if services["missing"]:
            print(f"   Missing: {services['missing']}")
    else:
        print(f"   Services: ✗ {services['message']}")
    
    print("\n3. Validating routes...")
    routes = await validate_routes()
    if routes["status"] == "success":
        print(f"   Routes: ✓ {len(routes['found'])}/{len(routes['expected'])} found")
        if routes["missing"]:
            print(f"   Missing: {routes['missing']}")
    else:
        print(f"   Routes: ✗ {routes['message']}")
    
    print("\n4. Validating plugins...")
    plugins = await validate_plugins()
    if plugins["status"] == "success":
        print(f"   Plugins: ✓ {len(plugins['found'])}/{len(plugins['expected'])} types found")
        print(f"   Plugin instances: {plugins['counts']}")
        if plugins["missing"]:
            print(f"   Missing: {plugins['missing']}")
    else:
        print(f"   Plugins: ✗ {plugins['message']}")
    
    print("\n5. Testing ChromaDB...")
    chroma = await test_chromadb()
    print(f"   ChromaDB: {'✓ ' + chroma['message'] if chroma['status'] == 'success' else '✗ ' + chroma['message']}")
    
    print("\n6. Testing Groq integration...")
    groq = await test_groq_integration()
    print(f"   Groq API: {'✓ ' + groq['message'] if groq['status'] == 'success' else '✗ ' + groq['message']}")
    
    print("\n" + "=" * 40)
    print("Validation complete!")


if __name__ == "__main__":
    asyncio.run(main())