import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import uvicorn

from app.routes import query_router, escalation_router, session_router, crm_router


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    error_type: str
    message: str
    timestamp: str
    path: str


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Kong Support Agent API")
    
    from app.services.performance_monitor import performance_monitor
    from app.services.kong_performance import performance_scheduler
    
    await performance_monitor.start_monitoring(60)
    await performance_scheduler.start_scheduled_optimization(15)
    logger.info("Performance monitoring and optimization started")
    
    yield
    
    await performance_monitor.stop_monitoring()
    await performance_scheduler.stop_scheduled_optimization()
    logger.info("Shutting down Kong Support Agent API")


app = FastAPI(
    title="Kong Support Agent API",
    description="Intelligent customer support agent with Kong AI Gateway integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_type="HTTP_ERROR",
            message=exc.detail,
            timestamp=datetime.utcnow().isoformat(),
            path=str(request.url.path)
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()} - Path: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_type="VALIDATION_ERROR",
            message=f"Request validation failed: {exc.errors()}",
            timestamp=datetime.utcnow().isoformat(),
            path=str(request.url.path)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    from app.services.error_handler import system_error_handler, ErrorSeverity
    
    error_type = type(exc).__name__
    system_error_handler.record_error(
        error_type, 
        "main_app", 
        ErrorSeverity.HIGH, 
        {"path": str(request.url.path), "method": request.method}
    )
    
    logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}", exc_info=True)
    
    if "kong" in str(exc).lower():
        error_message = "Kong Gateway service temporarily unavailable. Using fallback processing."
        error_type_name = "KONG_GATEWAY_ERROR"
    elif "groq" in str(exc).lower() or "api" in str(exc).lower():
        error_message = "AI service temporarily unavailable. Please try again shortly."
        error_type_name = "LLM_API_ERROR"
    else:
        error_message = "An unexpected error occurred. Our team has been notified."
        error_type_name = "INTERNAL_ERROR"
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_type=error_type_name,
            message=error_message,
            timestamp=datetime.utcnow().isoformat(),
            path=str(request.url.path)
        ).dict()
    )


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(f"Response: {response.status_code} - {process_time:.2f}ms")
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


app.include_router(query_router)
app.include_router(escalation_router)
app.include_router(session_router)
app.include_router(crm_router)


@app.get("/")
async def root():
    return {"message": "Kong Support Agent API", "status": "running"}


@app.get("/performance/health")
async def performance_health():
    from app.services.performance_monitor import performance_monitor
    return performance_monitor.get_system_health()


@app.get("/performance/alerts")
async def performance_alerts():
    from app.services.performance_monitor import performance_monitor
    return {
        "alerts": performance_monitor.get_alerts(1),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/performance/optimize")
async def performance_optimization():
    from app.services.kong_performance import kong_optimizer
    return await kong_optimizer.run_performance_optimization()


@app.get("/performance/kong")
async def kong_performance():
    from app.services.kong_performance import kong_optimizer
    return await kong_optimizer.check_kong_performance()


@app.get("/performance/history")
async def optimization_history():
    from app.services.kong_performance import kong_optimizer
    return {
        "optimization_history": kong_optimizer.get_optimization_history(24),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/system/errors")
async def system_error_statistics():
    from app.services.error_handler import system_error_handler
    return system_error_handler.get_error_statistics()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )