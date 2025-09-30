import os
from typing import Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

class GroqConfig(BaseSettings):
    api_key: str = Field("", env="GROQ_API_KEY")
    simple_model: str = Field("llama-3.3-70b-versatile", env="GROQ_SIMPLE_MODEL")
    complex_model: str = Field("openai/gpt-oss-120b", env="GROQ_COMPLEX_MODEL")
    fallback_model: str = Field("llama-3.1-8b-instant", env="GROQ_FALLBACK_MODEL")
    
    max_tokens_simple: int = Field(1000, env="GROQ_MAX_TOKENS_SIMPLE")
    max_tokens_complex: int = Field(2000, env="GROQ_MAX_TOKENS_COMPLEX")
    max_tokens_fallback: int = Field(500, env="GROQ_MAX_TOKENS_FALLBACK")
    
    temperature_simple: float = Field(0.7, env="GROQ_TEMPERATURE_SIMPLE")
    temperature_complex: float = Field(0.7, env="GROQ_TEMPERATURE_COMPLEX")
    temperature_fallback: float = Field(0.5, env="GROQ_TEMPERATURE_FALLBACK")
    
    model_config = {"extra": "ignore"}

class KongConfig(BaseSettings):
    admin_url: str = Field("http://localhost:8001", env="KONG_ADMIN_URL")
    proxy_url: str = Field("http://localhost:8000", env="KONG_PROXY_URL")
    manager_url: str = Field("http://localhost:8002", env="KONG_MANAGER_URL")
    
    simple_route: str = "/ai/simple"
    complex_route: str = "/ai/complex"
    fallback_route: str = "/ai/fallback"
    unified_route: str = "/ai/chat"
    
    model_config = {"extra": "ignore"}

class ChromaDBConfig(BaseSettings):
    url: str = Field("http://localhost:8003", env="CHROMADB_URL")
    host: str = Field("localhost", env="CHROMADB_HOST")
    port: int = Field(8003, env="CHROMADB_PORT")
    
    simple_collection: str = "simple_queries"
    complex_collection: str = "complex_queries"
    fallback_collection: str = "fallback_queries"
    
    model_config = {"extra": "ignore"}

class DatabaseConfig(BaseSettings):
    postgres_user: str = Field("kong", env="POSTGRES_USER")
    postgres_password: str = Field("kongpass", env="POSTGRES_PASSWORD")
    postgres_db: str = Field("kong", env="POSTGRES_DB")
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    
    model_config = {"extra": "ignore"}
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

class ServerConfig(BaseSettings):
    fastapi_host: str = Field("0.0.0.0", env="FASTAPI_HOST")
    fastapi_port: int = Field(8080, env="FASTAPI_PORT")
    backend_url: str = Field("http://localhost:8080", env="BACKEND_URL")
    
    streamlit_host: str = Field("0.0.0.0", env="STREAMLIT_HOST")
    streamlit_port: int = Field(8501, env="STREAMLIT_PORT")
    
    model_config = {"extra": "ignore"}

class AnalysisConfig(BaseSettings):
    complexity_threshold: float = Field(0.8, env="COMPLEXITY_THRESHOLD")
    sentiment_threshold: float = Field(-0.5, env="SENTIMENT_THRESHOLD")
    similarity_threshold: float = Field(0.85, env="SIMILARITY_THRESHOLD")
    
    escalation_complexity_threshold: float = Field(0.8, env="ESCALATION_COMPLEXITY_THRESHOLD")
    escalation_sentiment_threshold: float = Field(-0.5, env="ESCALATION_SENTIMENT_THRESHOLD")
    
    model_config = {"extra": "ignore"}

class CacheConfig(BaseSettings):
    enabled: bool = Field(True, env="SEMANTIC_CACHE_ENABLED")
    similarity_threshold: float = Field(0.85, env="SEMANTIC_CACHE_SIMILARITY")
    ttl: int = Field(3600, env="SEMANTIC_CACHE_TTL")
    max_size: int = Field(1000, env="SEMANTIC_CACHE_MAX_SIZE")
    
    model_config = {"extra": "ignore"}

class RateLimitConfig(BaseSettings):
    simple_limit: int = Field(100, env="RATE_LIMIT_SIMPLE")
    complex_limit: int = Field(50, env="RATE_LIMIT_COMPLEX")
    fallback_limit: int = Field(200, env="RATE_LIMIT_FALLBACK")
    window_size: int = Field(60, env="RATE_LIMIT_WINDOW")
    
    model_config = {"extra": "ignore"}

class SecurityConfig(BaseSettings):
    prompt_guard_enabled: bool = Field(True, env="PROMPT_GUARD_ENABLED")
    prompt_guard_max_body_size: int = Field(8192, env="PROMPT_GUARD_MAX_BODY_SIZE")
    
    model_config = {"extra": "ignore"}

class ObservabilityConfig(BaseSettings):
    ai_analytics_enabled: bool = Field(True, env="AI_ANALYTICS_ENABLED")
    observability_enabled: bool = Field(True, env="OBSERVABILITY_ENABLED")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    model_config = {"extra": "ignore"}

class SessionConfig(BaseSettings):
    backup_interval: int = Field(300, env="SESSION_BACKUP_INTERVAL")
    crm_storage_type: str = Field("memory", env="CRM_STORAGE_TYPE")
    crm_backup_file: str = Field("sessions_backup.json", env="CRM_BACKUP_FILE")
    
    model_config = {"extra": "ignore"}

class AppConfig(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    
    groq: GroqConfig = Field(default_factory=GroqConfig)
    kong: KongConfig = Field(default_factory=KongConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

config = AppConfig()