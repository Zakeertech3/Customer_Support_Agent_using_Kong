import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config import config

logger = logging.getLogger(__name__)

class EnvironmentService:
    def __init__(self):
        self.required_env_vars = [
            "GROQ_API_KEY",
            "KONG_ADMIN_URL",
            "KONG_PROXY_URL",
            "CHROMADB_URL",
            "POSTGRES_HOST",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB"
        ]
        
        self.optional_env_vars = [
            "KONG_LICENSE_DATA",
            "LOG_LEVEL",
            "ENVIRONMENT"
        ]
    
    def validate_environment(self) -> Dict[str, Any]:
        validation_results = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "configuration_status": {},
            "recommendations": []
        }
        
        for var in self.required_env_vars:
            value = os.getenv(var)
            if not value:
                validation_results["missing_required"].append(var)
                validation_results["valid"] = False
            else:
                validation_results["configuration_status"][var] = "✓ Set"
        
        for var in self.optional_env_vars:
            value = os.getenv(var)
            if not value:
                validation_results["missing_optional"].append(var)
            else:
                validation_results["configuration_status"][var] = "✓ Set"
        
        validation_results["recommendations"] = self._generate_recommendations(validation_results)
        
        return validation_results
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if validation_results["missing_required"]:
            recommendations.append("Set all required environment variables before starting the application")
        
        if "KONG_LICENSE_DATA" in validation_results["missing_optional"]:
            recommendations.append("Consider setting KONG_LICENSE_DATA for Kong Gateway Enterprise features")
        
        if config.environment == "production":
            recommendations.append("Ensure all security configurations are properly set for production")
            
        return recommendations
    
    def get_service_configurations(self) -> Dict[str, Any]:
        return {
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
            "database": {
                "host": config.database.postgres_host,
                "port": config.database.postgres_port,
                "database": config.database.postgres_db,
                "user": config.database.postgres_user,
                "password_set": bool(config.database.postgres_password)
            },
            "analysis": {
                "complexity_threshold": config.analysis.complexity_threshold,
                "sentiment_threshold": config.analysis.sentiment_threshold,
                "similarity_threshold": config.analysis.similarity_threshold,
                "escalation_thresholds": {
                    "complexity": config.analysis.escalation_complexity_threshold,
                    "sentiment": config.analysis.escalation_sentiment_threshold
                }
            },
            "cache": {
                "enabled": config.cache.enabled,
                "similarity_threshold": config.cache.similarity_threshold,
                "ttl": config.cache.ttl,
                "max_size": config.cache.max_size
            },
            "rate_limiting": {
                "simple_limit": config.rate_limit.simple_limit,
                "complex_limit": config.rate_limit.complex_limit,
                "fallback_limit": config.rate_limit.fallback_limit,
                "window_size": config.rate_limit.window_size
            },
            "security": {
                "prompt_guard_enabled": config.security.prompt_guard_enabled,
                "prompt_guard_max_body_size": config.security.prompt_guard_max_body_size
            },
            "observability": {
                "ai_analytics_enabled": config.observability.ai_analytics_enabled,
                "observability_enabled": config.observability.observability_enabled,
                "log_level": config.observability.log_level
            }
        }
    
    def generate_env_template(self) -> str:
        template = """# Kong Support Agent Environment Configuration

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Kong Gateway Configuration
KONG_ADMIN_URL=http://localhost:8001
KONG_PROXY_URL=http://localhost:8000
KONG_MANAGER_URL=http://localhost:8002

# ChromaDB Configuration
CHROMADB_URL=http://localhost:8002
CHROMADB_HOST=localhost
CHROMADB_PORT=8002

# PostgreSQL Database Configuration
POSTGRES_USER=kong
POSTGRES_PASSWORD=kongpass
POSTGRES_DB=kong
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Kong License (Optional for Enterprise features)
KONG_LICENSE_DATA=

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8080
BACKEND_URL=http://localhost:8080

STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# Application Configuration
LOG_LEVEL=INFO
CACHE_TTL=3600
SIMILARITY_THRESHOLD=0.85
COMPLEXITY_THRESHOLD=0.8
SENTIMENT_THRESHOLD=-0.5

# Groq Model Configuration
GROQ_SIMPLE_MODEL=llama-3.3-70b-versatile
GROQ_COMPLEX_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant

# Token Limits
GROQ_MAX_TOKENS_SIMPLE=1000
GROQ_MAX_TOKENS_COMPLEX=2000
GROQ_MAX_TOKENS_FALLBACK=500

# Temperature Settings
GROQ_TEMPERATURE_SIMPLE=0.7
GROQ_TEMPERATURE_COMPLEX=0.7
GROQ_TEMPERATURE_FALLBACK=0.5

# Escalation Thresholds
ESCALATION_COMPLEXITY_THRESHOLD=0.8
ESCALATION_SENTIMENT_THRESHOLD=-0.5

# Rate Limiting Configuration
RATE_LIMIT_SIMPLE=100
RATE_LIMIT_COMPLEX=50
RATE_LIMIT_FALLBACK=200
RATE_LIMIT_WINDOW=60

# Semantic Cache Configuration
SEMANTIC_CACHE_ENABLED=true
SEMANTIC_CACHE_SIMILARITY=0.85
SEMANTIC_CACHE_TTL=3600
SEMANTIC_CACHE_MAX_SIZE=1000

# Security Configuration
PROMPT_GUARD_ENABLED=true
PROMPT_GUARD_MAX_BODY_SIZE=8192

# Observability Configuration
AI_ANALYTICS_ENABLED=true
OBSERVABILITY_ENABLED=true

# Session Management
SESSION_BACKUP_INTERVAL=300
CRM_STORAGE_TYPE=memory
CRM_BACKUP_FILE=sessions_backup.json

# Environment
ENVIRONMENT=development
"""
        return template
    
    def export_configuration_summary(self) -> Dict[str, Any]:
        validation = self.validate_environment()
        configurations = self.get_service_configurations()
        
        return {
            "environment_validation": validation,
            "service_configurations": configurations,
            "system_info": {
                "environment": config.environment,
                "log_level": config.observability.log_level,
                "configuration_file": ".env"
            },
            "health_status": {
                "configuration_valid": validation["valid"],
                "required_vars_count": len(self.required_env_vars),
                "optional_vars_count": len(self.optional_env_vars),
                "missing_required_count": len(validation["missing_required"]),
                "missing_optional_count": len(validation["missing_optional"])
            }
        }

environment_service = EnvironmentService()
