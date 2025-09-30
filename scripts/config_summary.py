from app.config import config
import json

def display_config_summary():
    print("Kong Support Agent Configuration Summary")
    print("=" * 50)
    
    sections = [
        ("Groq API Configuration", {
            "API Key": f"{config.groq.api_key[:20]}..." if config.groq.api_key else "Not set",
            "Simple Model": config.groq.simple_model,
            "Complex Model": config.groq.complex_model,
            "Fallback Model": config.groq.fallback_model,
            "Max Tokens (Simple)": config.groq.max_tokens_simple,
            "Max Tokens (Complex)": config.groq.max_tokens_complex,
            "Max Tokens (Fallback)": config.groq.max_tokens_fallback,
            "Temperature (Simple)": config.groq.temperature_simple,
            "Temperature (Complex)": config.groq.temperature_complex,
            "Temperature (Fallback)": config.groq.temperature_fallback
        }),
        
        ("Kong Gateway Configuration", {
            "Admin URL": config.kong.admin_url,
            "Proxy URL": config.kong.proxy_url,
            "Manager URL": config.kong.manager_url,
            "Simple Route": config.kong.simple_route,
            "Complex Route": config.kong.complex_route,
            "Fallback Route": config.kong.fallback_route,
            "Unified Route": config.kong.unified_route
        }),
        
        ("ChromaDB Configuration", {
            "URL": config.chromadb.url,
            "Host": config.chromadb.host,
            "Port": config.chromadb.port,
            "Simple Collection": config.chromadb.simple_collection,
            "Complex Collection": config.chromadb.complex_collection,
            "Fallback Collection": config.chromadb.fallback_collection
        }),
        
        ("Database Configuration", {
            "PostgreSQL Host": config.database.postgres_host,
            "PostgreSQL Port": config.database.postgres_port,
            "PostgreSQL User": config.database.postgres_user,
            "PostgreSQL Database": config.database.postgres_db,
            "Connection URL": f"postgresql://{config.database.postgres_user}:***@{config.database.postgres_host}:{config.database.postgres_port}/{config.database.postgres_db}"
        }),
        
        ("Server Configuration", {
            "FastAPI Host": config.server.fastapi_host,
            "FastAPI Port": config.server.fastapi_port,
            "Backend URL": config.server.backend_url,
            "Streamlit Host": config.server.streamlit_host,
            "Streamlit Port": config.server.streamlit_port
        }),
        
        ("Analysis Configuration", {
            "Complexity Threshold": config.analysis.complexity_threshold,
            "Sentiment Threshold": config.analysis.sentiment_threshold,
            "Similarity Threshold": config.analysis.similarity_threshold,
            "Escalation Complexity Threshold": config.analysis.escalation_complexity_threshold,
            "Escalation Sentiment Threshold": config.analysis.escalation_sentiment_threshold
        }),
        
        ("Cache Configuration", {
            "Enabled": config.cache.enabled,
            "Similarity Threshold": config.cache.similarity_threshold,
            "TTL (seconds)": config.cache.ttl,
            "Max Size": config.cache.max_size
        }),
        
        ("Rate Limiting Configuration", {
            "Simple Model Limit": config.rate_limit.simple_limit,
            "Complex Model Limit": config.rate_limit.complex_limit,
            "Fallback Model Limit": config.rate_limit.fallback_limit,
            "Window Size (seconds)": config.rate_limit.window_size
        }),
        
        ("Security Configuration", {
            "Prompt Guard Enabled": config.security.prompt_guard_enabled,
            "Max Body Size": config.security.prompt_guard_max_body_size
        }),
        
        ("Observability Configuration", {
            "AI Analytics Enabled": config.observability.ai_analytics_enabled,
            "Observability Enabled": config.observability.observability_enabled,
            "Log Level": config.observability.log_level
        }),
        
        ("Session Configuration", {
            "Backup Interval (seconds)": config.session.backup_interval,
            "CRM Storage Type": config.session.crm_storage_type,
            "CRM Backup File": config.session.crm_backup_file
        }),
        
        ("Environment", {
            "Environment": config.environment
        })
    ]
    
    for section_name, section_config in sections:
        print(f"\n{section_name}:")
        print("-" * len(section_name))
        for key, value in section_config.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)

def export_config_json():
    config_dict = {
        "groq": {
            "api_key_set": bool(config.groq.api_key),
            "simple_model": config.groq.simple_model,
            "complex_model": config.groq.complex_model,
            "fallback_model": config.groq.fallback_model,
            "max_tokens": {
                "simple": config.groq.max_tokens_simple,
                "complex": config.groq.max_tokens_complex,
                "fallback": config.groq.max_tokens_fallback
            },
            "temperature": {
                "simple": config.groq.temperature_simple,
                "complex": config.groq.temperature_complex,
                "fallback": config.groq.temperature_fallback
            }
        },
        "kong": {
            "admin_url": config.kong.admin_url,
            "proxy_url": config.kong.proxy_url,
            "manager_url": config.kong.manager_url,
            "routes": {
                "simple": config.kong.simple_route,
                "complex": config.kong.complex_route,
                "fallback": config.kong.fallback_route,
                "unified": config.kong.unified_route
            }
        },
        "chromadb": {
            "url": config.chromadb.url,
            "host": config.chromadb.host,
            "port": config.chromadb.port,
            "collections": {
                "simple": config.chromadb.simple_collection,
                "complex": config.chromadb.complex_collection,
                "fallback": config.chromadb.fallback_collection
            }
        },
        "analysis": {
            "complexity_threshold": config.analysis.complexity_threshold,
            "sentiment_threshold": config.analysis.sentiment_threshold,
            "similarity_threshold": config.analysis.similarity_threshold,
            "escalation": {
                "complexity_threshold": config.analysis.escalation_complexity_threshold,
                "sentiment_threshold": config.analysis.escalation_sentiment_threshold
            }
        },
        "cache": {
            "enabled": config.cache.enabled,
            "similarity_threshold": config.cache.similarity_threshold,
            "ttl": config.cache.ttl,
            "max_size": config.cache.max_size
        },
        "rate_limit": {
            "simple": config.rate_limit.simple_limit,
            "complex": config.rate_limit.complex_limit,
            "fallback": config.rate_limit.fallback_limit,
            "window_size": config.rate_limit.window_size
        },
        "security": {
            "prompt_guard_enabled": config.security.prompt_guard_enabled,
            "max_body_size": config.security.prompt_guard_max_body_size
        },
        "environment": config.environment
    }
    
    with open("config_export.json", "w") as f:
        json.dump(config_dict, f, indent=2)
    
    print("Configuration exported to config_export.json")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        export_config_json()
    else:
        display_config_summary()