import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx

from app.services import ComplexityAnalyzer, SentimentAnalyzer, kong_client, escalation_manager, session_manager, crm_service
from app.services.cache_service import semantic_cache, performance_metrics, CostCalculator
from app.models import ConversationMessage, EscalationTicket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    customer_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    message_id: str
    session_id: str
    model_used: str
    complexity_score: float
    sentiment_score: float
    response_time_ms: int
    tokens_used: Optional[int] = None
    cached: bool = False
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    escalation_ticket: Optional[EscalationTicket] = None
    escalation_notification: Optional[Dict[str, Any]] = None


class QueryProcessor:
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.groq_api_key = self._get_groq_api_key()
        self.groq_base_url = "https://api.groq.com/openai/v1"
        
    def _get_groq_api_key(self) -> str:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        return api_key
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        start_time = time.time()
        
        try:
            complexity_analysis = self.complexity_analyzer.analyze_query(request.query)
            sentiment_analysis = self.sentiment_analyzer.analyze_sentiment(request.query)
            
            complexity_score = complexity_analysis.get("complexity_score", 0.5)
            sentiment_score = sentiment_analysis.get("sentiment_score", 0.0)
            recommended_model = complexity_analysis.get("recommended_model", "llama-3.1-8b-instant")
            
            if not complexity_analysis.get("analysis_successful", True):
                logger.warning("Complexity analysis failed, using fallback values")
                performance_metrics.record_error("complexity_analysis_failure", "/api/query", recommended_model)
            
            if not sentiment_analysis.get("analysis_successful", True):
                logger.warning("Sentiment analysis failed, using neutral sentiment")
                performance_metrics.record_error("sentiment_analysis_failure", "/api/query", recommended_model)
            
            performance_metrics.record_model_usage(
                model=recommended_model,
                complexity_score=complexity_score,
                reason=f"complexity_{complexity_score:.2f}"
            )
            
            should_escalate, escalation_reasons = escalation_manager.should_escalate(
                complexity_score, sentiment_score
            )
            
            escalation_required = should_escalate
            escalation_reason = ", ".join(escalation_reasons) if escalation_reasons else None
            escalation_ticket = None
            escalation_notification = None
            
            cached_result = None
            try:
                cached_result = semantic_cache.get(request.query, recommended_model)
            except Exception as cache_error:
                logger.warning(f"Cache retrieval failed: {cache_error}")
                performance_metrics.record_error("cache_retrieval_failure", "/api/query", recommended_model)
            
            if cached_result:
                llm_response = cached_result['response']
                tokens_used = 0
                cached = True
                response_time_ms = int(cached_result['response_time_ms'])
                
                performance_metrics.record_cache_hit(True, cached_result.get('similarity', 1.0))
                performance_metrics.record_response_time(
                    endpoint="/api/query",
                    response_time_ms=response_time_ms,
                    model=recommended_model,
                    cached=True
                )
                
                logger.info(f"Cache hit for query with model {recommended_model}, response time: {response_time_ms}ms")
            else:
                performance_metrics.record_cache_hit(False)
                
                llm_response, tokens_used, cached, final_model = await self._process_llm_request_with_fallbacks(
                    request.query, recommended_model
                )
                recommended_model = final_model
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                try:
                    semantic_cache.set(request.query, recommended_model, llm_response, tokens_used or 0)
                except Exception as cache_error:
                    logger.warning(f"Cache storage failed: {cache_error}")
                    performance_metrics.record_error("cache_storage_failure", "/api/query", recommended_model)
                
                performance_metrics.record_response_time(
                    endpoint="/api/query",
                    response_time_ms=response_time_ms,
                    model=recommended_model,
                    cached=False
                )
            
            if tokens_used:
                input_tokens = CostCalculator.estimate_tokens(request.query)
                output_tokens = tokens_used - input_tokens
                cost = CostCalculator.calculate_cost(recommended_model, input_tokens, output_tokens)
                performance_metrics.record_token_usage(recommended_model, tokens_used, cost)
            
            session_id = request.session_id or str(uuid4())
            message_id = str(uuid4())
            customer_id = request.customer_id or f"customer_{session_id}"
            
            session = session_manager.get_session(session_id)
            if not session:
                session = session_manager.create_session(customer_id, session_id)
            
            user_message = ConversationMessage(
                id=message_id,
                role="user",
                content=request.query,
                complexity_score=complexity_score,
                sentiment_score=sentiment_score
            )
            
            assistant_message = ConversationMessage(
                role="assistant",
                content=llm_response,
                model_used=recommended_model,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                cached=cached
            )
            
            session_manager.add_message_to_session(session_id, user_message)
            session_manager.add_message_to_session(session_id, assistant_message)
            
            crm_service.log_interaction(
                customer_id=customer_id,
                query=request.query,
                response=llm_response,
                sentiment_score=sentiment_score,
                model_used=recommended_model,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                complexity_score=complexity_score,
                session_id=session_id
            )
            
            conversation_history = session_manager.get_session_messages(session_id)
            
            if escalation_required:
                escalation_score = max(complexity_score, abs(sentiment_score))
                escalation_ticket = escalation_manager.create_escalation_ticket(
                    customer_id=customer_id,
                    conversation_history=conversation_history,
                    escalation_reasons=escalation_reasons,
                    escalation_score=escalation_score
                )
                escalation_notification = escalation_manager.get_escalation_notification(escalation_ticket)
                session_manager.add_escalation_to_session(session_id, escalation_ticket)
                crm_service.create_ticket(escalation_ticket)
            
            logger.info(f"Query processed successfully - Model: {recommended_model}, "
                       f"Complexity: {complexity_score:.3f}, Sentiment: {sentiment_score:.3f}, "
                       f"Response time: {response_time_ms}ms, Escalation: {escalation_required}")
            
            return QueryResponse(
                response=llm_response,
                message_id=message_id,
                session_id=session_id,
                model_used=recommended_model,
                complexity_score=complexity_score,
                sentiment_score=sentiment_score,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                cached=cached,
                escalation_required=escalation_required,
                escalation_reason=escalation_reason,
                escalation_ticket=escalation_ticket,
                escalation_notification=escalation_notification
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
    
    async def _call_llm_via_kong(self, query: str, model: str, max_retries: int = 2) -> tuple[str, Optional[int], bool]:
        kong_url = "http://localhost:8000/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}",
            "X-Model-Name": model
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent. Provide clear, accurate, and helpful responses to customer queries."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                timeout_config = httpx.Timeout(30.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.post(kong_url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        tokens_used = result.get("usage", {}).get("total_tokens")
                        cached = response.headers.get("X-Cache-Status") == "HIT"
                        
                        if attempt > 0:
                            logger.info(f"Kong Gateway recovered after {attempt} retries")
                        
                        return content, tokens_used, cached
                    
                    elif response.status_code == 429:
                        if attempt < max_retries:
                            wait_time = 2 ** attempt
                            logger.warning(f"Kong rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        raise HTTPException(status_code=429, detail="Kong Gateway rate limit exceeded")
                    
                    elif response.status_code >= 500:
                        if attempt < max_retries:
                            wait_time = 2 ** attempt
                            logger.warning(f"Kong server error {response.status_code}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        raise HTTPException(status_code=response.status_code, detail=f"Kong Gateway server error: {response.text}")
                    
                    else:
                        raise HTTPException(status_code=response.status_code, detail=f"Kong Gateway error: {response.text}")
            
            except httpx.ConnectError as e:
                last_error = f"Kong Gateway connection failed: {str(e)}"
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Kong connection failed, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                break
            
            except httpx.TimeoutException as e:
                last_error = f"Kong Gateway timeout: {str(e)}"
                if attempt < max_retries:
                    logger.warning(f"Kong timeout, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
            
            except Exception as e:
                last_error = f"Kong Gateway unexpected error: {str(e)}"
                if attempt < max_retries:
                    logger.warning(f"Kong unexpected error, retrying (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
        
        performance_metrics.record_error("kong_gateway_failure", "/api/query", model)
        raise Exception(last_error or "Kong Gateway failed after all retries")
    
    async def _call_groq_direct(self, query: str, model: str, max_retries: int = 3) -> tuple[str, Optional[int], bool]:
        groq_url = f"{self.groq_base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent. Provide clear, accurate, and helpful responses to customer queries."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                timeout_config = httpx.Timeout(30.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.post(groq_url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        tokens_used = result.get("usage", {}).get("total_tokens")
                        
                        if attempt > 0:
                            logger.info(f"Groq API recovered after {attempt} retries")
                        
                        return content, tokens_used, False
                    
                    elif response.status_code == 429:
                        if attempt < max_retries:
                            wait_time = min(60, 2 ** attempt * 5)
                            logger.warning(f"Groq rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        raise HTTPException(status_code=429, detail="Groq API rate limit exceeded")
                    
                    elif response.status_code == 401:
                        raise HTTPException(status_code=401, detail="Groq API authentication failed - check API key")
                    
                    elif response.status_code >= 500:
                        if attempt < max_retries:
                            wait_time = 2 ** attempt
                            logger.warning(f"Groq server error {response.status_code}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        raise HTTPException(status_code=response.status_code, detail=f"Groq API server error: {response.text}")
                    
                    else:
                        error_detail = response.text
                        try:
                            error_json = response.json()
                            error_detail = error_json.get("error", {}).get("message", error_detail)
                        except:
                            pass
                        raise HTTPException(status_code=response.status_code, detail=f"Groq API error: {error_detail}")
            
            except httpx.ConnectError as e:
                last_error = f"Groq API connection failed: {str(e)}"
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Groq connection failed, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                break
            
            except httpx.TimeoutException as e:
                last_error = f"Groq API timeout: {str(e)}"
                if attempt < max_retries:
                    logger.warning(f"Groq timeout, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
            
            except HTTPException:
                raise
            
            except Exception as e:
                last_error = f"Groq API unexpected error: {str(e)}"
                if attempt < max_retries:
                    logger.warning(f"Groq unexpected error, retrying (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
        
        performance_metrics.record_error("groq_api_failure", "/api/query", model)
        raise Exception(last_error or "Groq API failed after all retries")
    
    async def _process_llm_request_with_fallbacks(self, query: str, preferred_model: str) -> tuple[str, Optional[int], bool, str]:
        fallback_chain = [
            ("kong", preferred_model),
            ("direct", preferred_model),
            ("direct", "llama-3.3-70b-versatile"),
            ("direct", "llama-3.1-8b-instant")
        ]
        
        last_error = None
        
        for method, model in fallback_chain:
            try:
                if method == "kong":
                    logger.info(f"Attempting Kong Gateway with model {model}")
                    response, tokens, cached = await self._call_llm_via_kong(query, model)
                    logger.info(f"Kong Gateway successful with model {model}")
                    return response, tokens, cached, model
                
                elif method == "direct":
                    logger.info(f"Attempting direct Groq API with model {model}")
                    response, tokens, cached = await self._call_groq_direct(query, model)
                    logger.info(f"Direct Groq API successful with model {model}")
                    performance_metrics.record_error("kong_fallback_used", "/api/query", model)
                    return response, tokens, cached, model
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Failed {method} call with {model}: {e}")
                performance_metrics.record_error(f"{method}_failure", "/api/query", model)
                continue
        
        logger.error(f"All LLM fallback methods failed. Last error: {last_error}")
        
        fallback_response = self._generate_fallback_response(query)
        performance_metrics.record_error("all_llm_methods_failed", "/api/query", "fallback")
        return fallback_response, 0, False, "fallback"
    
    def _generate_fallback_response(self, query: str) -> str:
        fallback_responses = {
            "greeting": "Hello! I'm currently experiencing technical difficulties, but I'm here to help. Could you please try your question again in a moment?",
            "technical": "I apologize, but I'm experiencing technical issues right now. For immediate technical support, please contact our support team directly or try again in a few minutes.",
            "general": "I'm sorry, but I'm currently unable to process your request due to technical difficulties. Please try again shortly, or contact our support team for immediate assistance.",
            "error": "I apologize for the inconvenience. Our AI system is temporarily unavailable. Please contact our human support team for immediate assistance."
        }
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return fallback_responses["greeting"]
        elif any(word in query_lower for word in ["technical", "api", "code", "error", "bug", "integration"]):
            return fallback_responses["technical"]
        elif len(query) > 100:
            return fallback_responses["technical"]
        else:
            return fallback_responses["general"]


query_processor = QueryProcessor()


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    return await query_processor.process_query(request)


@router.post("/query/analyze")
async def analyze_query(request: QueryRequest) -> Dict[str, Any]:
    complexity_analysis = query_processor.complexity_analyzer.analyze_query(request.query)
    sentiment_analysis = query_processor.sentiment_analyzer.analyze_sentiment(request.query)
    
    escalation_required = (
        complexity_analysis["escalation_flag"] or 
        sentiment_analysis["escalation_required"]
    )
    
    escalation_reason = None
    if escalation_required:
        reasons = []
        if complexity_analysis["escalation_flag"]:
            reasons.append("high_complexity")
        if sentiment_analysis["escalation_required"]:
            reasons.append("negative_sentiment")
        escalation_reason = ", ".join(reasons)
    
    return {
        "query": request.query,
        "complexity_analysis": complexity_analysis,
        "sentiment_analysis": sentiment_analysis,
        "escalation_required": escalation_required,
        "escalation_reason": escalation_reason,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/query/health")
async def query_health():
    return {
        "status": "healthy",
        "service": "query_processor",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/query/metrics")
async def get_performance_metrics():
    summary_stats = performance_metrics.get_summary_stats()
    recent_stats = performance_metrics.get_recent_metrics(5)
    cache_stats = semantic_cache.get_stats()
    
    return {
        "summary": summary_stats,
        "recent_5min": recent_stats,
        "cache": cache_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/query/cache/stats")
async def get_cache_stats():
    return {
        "cache_stats": semantic_cache.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/query/cache/clear")
async def clear_cache():
    semantic_cache.cache.clear()
    semantic_cache.query_vectors.clear()
    semantic_cache.fitted = False
    
    return {
        "message": "Cache cleared successfully",
        "timestamp": datetime.utcnow().isoformat()
    }