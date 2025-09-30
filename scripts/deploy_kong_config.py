import os
import subprocess
import sys
import time
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import config

def check_kong_health():
    try:
        response = requests.get(f"{config.kong.admin_url}/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def substitute_env_vars(config_file_path):
    with open(config_file_path, 'r') as file:
        content = file.read()
    
    env_vars = {
        'GROQ_API_KEY': config.groq.api_key,
        'GROQ_SIMPLE_MODEL': config.groq.simple_model,
        'GROQ_COMPLEX_MODEL': config.groq.complex_model,
        'GROQ_FALLBACK_MODEL': config.groq.fallback_model,
        'GROQ_MAX_TOKENS_SIMPLE': str(config.groq.max_tokens_simple),
        'GROQ_MAX_TOKENS_COMPLEX': str(config.groq.max_tokens_complex),
        'GROQ_MAX_TOKENS_FALLBACK': str(config.groq.max_tokens_fallback),
        'GROQ_TEMPERATURE_SIMPLE': str(config.groq.temperature_simple),
        'GROQ_TEMPERATURE_COMPLEX': str(config.groq.temperature_complex),
        'GROQ_TEMPERATURE_FALLBACK': str(config.groq.temperature_fallback),
        'CHROMADB_URL': config.chromadb.url,
        'SEMANTIC_CACHE_ENABLED': str(config.cache.enabled).lower(),
        'SEMANTIC_CACHE_SIMILARITY': str(config.cache.similarity_threshold),
        'SEMANTIC_CACHE_TTL': str(config.cache.ttl),
        'SEMANTIC_CACHE_MAX_SIZE': str(config.cache.max_size),
        'PROMPT_GUARD_ENABLED': str(config.security.prompt_guard_enabled).lower(),
        'PROMPT_GUARD_MAX_BODY_SIZE': str(config.security.prompt_guard_max_body_size),
        'RATE_LIMIT_SIMPLE': str(config.rate_limit.simple_limit),
        'RATE_LIMIT_COMPLEX': str(config.rate_limit.complex_limit),
        'RATE_LIMIT_FALLBACK': str(config.rate_limit.fallback_limit),
        'RATE_LIMIT_WINDOW': str(config.rate_limit.window_size)
    }
    
    for var, value in env_vars.items():
        content = content.replace(f"$({var})", value)
        content = content.replace(f"${{{var}}}", value)
    
    temp_config_path = config_file_path.replace('.yml', '_processed.yml')
    with open(temp_config_path, 'w') as file:
        file.write(content)
    
    return temp_config_path

def deploy_kong_config():
    print("Deploying Kong configuration...")
    
    if not check_kong_health():
        print("Kong is not running. Please start Kong first.")
        return False
    
    # Check if basic configuration is already in place
    try:
        services_response = requests.get(f"{config.kong.admin_url}/services")
        if services_response.status_code == 200:
            services = services_response.json().get('data', [])
            groq_service_exists = any(s['name'] == 'groq-api-service' for s in services)
            
            if groq_service_exists:
                print("Kong configuration already deployed via basic setup!")
                return True
            else:
                print("Running basic Kong setup...")
                # Import and run the basic setup
                from pathlib import Path
                import sys
                project_root = Path(__file__).parent.parent
                sys.path.insert(0, str(project_root))
                
                from scripts.setup_kong_basic import setup_kong_basic
                return setup_kong_basic()
        else:
            print(f"Failed to check Kong services: {services_response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error checking Kong configuration: {e}")
        return False

def validate_kong_config():
    print("Validating Kong configuration...")
    
    try:
        services_response = requests.get(f"{config.kong.admin_url}/services")
        routes_response = requests.get(f"{config.kong.admin_url}/routes")
        plugins_response = requests.get(f"{config.kong.admin_url}/plugins")
        
        if all(r.status_code == 200 for r in [services_response, routes_response, plugins_response]):
            services = services_response.json()['data']
            routes = routes_response.json()['data']
            plugins = plugins_response.json()['data']
            
            print(f"Services configured: {len(services)}")
            print(f"Routes configured: {len(routes)}")
            print(f"Plugins configured: {len(plugins)}")
            
            expected_services = ['groq-simple-service', 'groq-complex-service', 'groq-fallback-service']
            configured_services = [s['name'] for s in services]
            
            missing_services = set(expected_services) - set(configured_services)
            if missing_services:
                print(f"Missing services: {missing_services}")
                return False
            
            print("Kong configuration validation passed!")
            return True
        else:
            print("Failed to validate Kong configuration")
            return False
            
    except Exception as e:
        print(f"Error validating Kong configuration: {e}")
        return False

if __name__ == "__main__":
    print("Kong Configuration Deployment Script")
    print("=" * 40)
    
    if deploy_kong_config():
        time.sleep(2)
        validate_kong_config()
    else:
        sys.exit(1)