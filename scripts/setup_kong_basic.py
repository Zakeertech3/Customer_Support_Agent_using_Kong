import requests
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import config

def setup_kong_basic():
    print("Setting up basic Kong configuration...")
    
    kong_admin_url = config.kong.admin_url
    
    try:
        # Test Kong Admin API
        response = requests.get(f"{kong_admin_url}/status")
        if response.status_code != 200:
            print(f"Kong Admin API not accessible: {response.status_code}")
            return False
        
        print("✓ Kong Admin API is accessible")
        
        # Create a basic service for Groq API
        service_data = {
            "name": "groq-api-service",
            "url": "https://api.groq.com",
            "tags": ["groq", "ai"]
        }
        
        # Check if service exists
        services_response = requests.get(f"{kong_admin_url}/services")
        existing_services = services_response.json().get('data', [])
        service_exists = any(s['name'] == 'groq-api-service' for s in existing_services)
        
        if not service_exists:
            response = requests.post(f"{kong_admin_url}/services", json=service_data)
            if response.status_code in [200, 201]:
                print("✓ Created Groq API service")
            else:
                print(f"Failed to create service: {response.text}")
                return False
        else:
            print("✓ Groq API service already exists")
        
        # Create a route for the service
        route_data = {
            "name": "groq-chat-route",
            "paths": ["/ai/chat"],
            "methods": ["POST", "OPTIONS"],
            "service": {"name": "groq-api-service"},
            "tags": ["ai-chat"]
        }
        
        # Check if route exists
        routes_response = requests.get(f"{kong_admin_url}/routes")
        existing_routes = routes_response.json().get('data', [])
        route_exists = any(r['name'] == 'groq-chat-route' for r in existing_routes)
        
        if not route_exists:
            response = requests.post(f"{kong_admin_url}/routes", json=route_data)
            if response.status_code in [200, 201]:
                print("✓ Created chat route")
            else:
                print(f"Failed to create route: {response.text}")
                return False
        else:
            print("✓ Chat route already exists")
        
        # Add CORS plugin
        cors_plugin_data = {
            "name": "cors",
            "config": {
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "headers": ["Accept", "Accept-Version", "Content-Length", "Content-Type", "Date", "Authorization"],
                "exposed_headers": ["X-Auth-Token"],
                "credentials": True,
                "max_age": 3600
            }
        }
        
        # Check if CORS plugin exists on the service
        plugins_response = requests.get(f"{kong_admin_url}/services/groq-api-service/plugins")
        existing_plugins = plugins_response.json().get('data', [])
        cors_exists = any(p['name'] == 'cors' for p in existing_plugins)
        
        if not cors_exists:
            response = requests.post(f"{kong_admin_url}/services/groq-api-service/plugins", json=cors_plugin_data)
            if response.status_code in [200, 201]:
                print("✓ Added CORS plugin")
            else:
                print(f"Failed to add CORS plugin: {response.text}")
        else:
            print("✓ CORS plugin already exists")
        
        # Add rate limiting plugin
        rate_limit_plugin_data = {
            "name": "rate-limiting",
            "config": {
                "minute": 100,
                "hour": 1000,
                "policy": "local"
            }
        }
        
        rate_limit_exists = any(p['name'] == 'rate-limiting' for p in existing_plugins)
        
        if not rate_limit_exists:
            response = requests.post(f"{kong_admin_url}/services/groq-api-service/plugins", json=rate_limit_plugin_data)
            if response.status_code in [200, 201]:
                print("✓ Added rate limiting plugin")
            else:
                print(f"Failed to add rate limiting plugin: {response.text}")
        else:
            print("✓ Rate limiting plugin already exists")
        
        print("\n✓ Kong basic configuration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up Kong: {e}")
        return False

if __name__ == "__main__":
    setup_kong_basic()
