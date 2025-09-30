import re
import logging
from typing import Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    SIMPLE_FAQ = "simple_faq"
    TECHNICAL = "technical"
    MULTI_STEP = "multi_step"
    TROUBLESHOOTING = "troubleshooting"
    INTEGRATION = "integration"

class ComplexityAnalyzer:
    def __init__(self):
        self.technical_terms = {
            "api", "authentication", "authorization", "oauth", "jwt", "token", "endpoint", 
            "microservices", "database", "sql", "nosql", "mongodb", "postgresql", "mysql",
            "docker", "kubernetes", "container", "deployment", "ci/cd", "pipeline",
            "webhook", "rest", "graphql", "json", "xml", "yaml", "configuration",
            "middleware", "proxy", "gateway", "load balancer", "cache", "redis",
            "encryption", "ssl", "tls", "certificate", "security", "vulnerability",
            "rate limiting", "throttling", "scaling", "performance", "optimization",
            "monitoring", "logging", "metrics", "analytics", "debugging", "error",
            "exception", "timeout", "latency", "throughput", "concurrent", "async",
            "synchronous", "queue", "message broker", "kafka", "rabbitmq", "pub/sub",
            "migration", "schema", "foreign key", "constraint", "index", "query",
            "transaction", "acid", "consistency", "availability", "partition tolerance",
            "distributed", "cluster", "node", "replica", "backup", "recovery"
        }
        
        self.simple_patterns = [
            r"^(what|where|when|who) (is|are|do|does|can|will)",
            r"^(can you|could you|please) (help|tell|show|explain)",
            r"(business hours|office location|contact|phone|email)",
            r"(reset password|forgot password|login|sign in)",
            r"(pricing|cost|price|fee|billing)",
            r"^(what|where|when|who|how).*(hours|location|contact|price|cost)"
        ]
        
        self.integration_patterns = [
            r"(integrate|integration|integrating).*(api|system|service)",
            r"(connect|connecting).*(api|system|service)",
            r"(setup|configure).*(integration|api)"
        ]
        
        self.troubleshooting_patterns = [
            r"(trouble|problem|issue|error).*(with|in)",
            r"(troubleshoot|troubleshooting|debug|debugging)",
            r"(not working|doesn't work|broken|failed)",
            r"(fix|solve|resolve).*(problem|issue|error)"
        ]
        
        self.multi_step_patterns = [
            r"(multiple|several|various|different).*(step|stage|phase|method)",
            r"(first.*then|step.*step|stage.*stage)",
            r"(configure.*and.*setup|setup.*and.*configure)"
        ]
        
        self.technical_patterns = [
            r"(configure|configuration|setup|install)",
            r"(migrate|migration|upgrade|update)",
            r"(architecture|design|implement|implementation)",
            r"(custom|customization|customize)",
            r"(performance|optimization|scale|scaling)"
        ]

    def calculate_complexity(self, query: str) -> float:
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to complexity analyzer")
                return 0.0
            
            if len(query) > 10000:
                logger.warning(f"Query too long ({len(query)} chars), truncating for analysis")
                query = query[:10000]
                
            query_lower = query.lower().strip()
            
            length_score = self._calculate_length_score(query_lower)
            technical_score = self._calculate_technical_score(query_lower)
            question_complexity_score = self._analyze_question_type_score(query_lower)
            
            total_complexity = min(length_score + technical_score + question_complexity_score, 1.0)
            
            logger.info(f"Complexity analysis for query: '{query[:50]}...' - "
                       f"Length: {length_score:.3f}, Technical: {technical_score:.3f}, "
                       f"Question: {question_complexity_score:.3f}, Total: {total_complexity:.3f}")
            
            return total_complexity
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return 0.5

    def _calculate_length_score(self, query: str) -> float:
        word_count = len(query.split())
        return min(word_count / 40, 0.5)

    def _calculate_technical_score(self, query: str) -> float:
        technical_count = self._count_technical_terms(query)
        return min(technical_count / 8 * 0.4, 0.4)

    def _count_technical_terms(self, query: str) -> int:
        words = re.findall(r'\b\w+\b', query.lower())
        return sum(1 for word in words if word in self.technical_terms)

    def _analyze_question_type_score(self, query: str) -> float:
        question_type = self._analyze_question_type(query)
        
        complexity_weights = {
            QueryType.SIMPLE_FAQ: 0.0,
            QueryType.TECHNICAL: 0.15,
            QueryType.MULTI_STEP: 0.25,
            QueryType.TROUBLESHOOTING: 0.2,
            QueryType.INTEGRATION: 0.3
        }
        
        return complexity_weights.get(question_type, 0.1)

    def _analyze_question_type(self, query: str) -> QueryType:
        for pattern in self.simple_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.SIMPLE_FAQ
        
        for pattern in self.integration_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.INTEGRATION
        
        for pattern in self.troubleshooting_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.TROUBLESHOOTING
        
        for pattern in self.multi_step_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.MULTI_STEP
        
        for pattern in self.technical_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.TECHNICAL
        
        if len(query.split()) > 30:
            return QueryType.MULTI_STEP
        elif any(term in query for term in self.technical_terms):
            return QueryType.TECHNICAL
        
        return QueryType.SIMPLE_FAQ

    def get_model_recommendation(self, complexity_score: float) -> Tuple[str, str, bool]:
        if complexity_score < 0.3:
            model = "llama-3.3-70b-versatile"
            rationale = f"Simple query (complexity: {complexity_score:.3f}) - using cost-effective model"
            escalation_flag = False
        elif complexity_score < 0.8:
            model = "openai/gpt-oss-120b"
            rationale = f"Moderate complexity (complexity: {complexity_score:.3f}) - using advanced reasoning model"
            escalation_flag = False
        else:
            model = "openai/gpt-oss-120b"
            rationale = f"High complexity (complexity: {complexity_score:.3f}) - using advanced model with escalation flag"
            escalation_flag = True
        
        logger.info(f"Model recommendation: {model} - {rationale}")
        return model, rationale, escalation_flag

    def analyze_query(self, query: str) -> Dict:
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided for analysis")
                return {
                    "query": query,
                    "complexity_score": 0.0,
                    "recommended_model": "llama-3.3-70b-versatile",
                    "rationale": "Empty query - using simple model",
                    "escalation_flag": False,
                    "question_type": QueryType.SIMPLE_FAQ.value,
                    "technical_terms_count": 0,
                    "word_count": 0,
                    "analysis_successful": False,
                    "error": "Empty query"
                }
            
            complexity_score = self.calculate_complexity(query)
            model, rationale, escalation_flag = self.get_model_recommendation(complexity_score)
            question_type = self._analyze_question_type(query.lower())
            technical_terms_count = self._count_technical_terms(query.lower())
            
            analysis_result = {
                "query": query,
                "complexity_score": complexity_score,
                "recommended_model": model,
                "rationale": rationale,
                "escalation_flag": escalation_flag,
                "question_type": question_type.value,
                "technical_terms_count": technical_terms_count,
                "word_count": len(query.split()),
                "analysis_successful": True
            }
            
            logger.info(f"Complete query analysis: {analysis_result}")
            return analysis_result
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query": query,
                "complexity_score": 0.5,
                "recommended_model": "llama-3.1-8b-instant",
                "rationale": f"Analysis failed, using fallback model: {str(e)}",
                "escalation_flag": True,
                "question_type": QueryType.TECHNICAL.value,
                "technical_terms_count": 0,
                "word_count": len(query.split()) if query else 0,
                "analysis_successful": False,
                "error": str(e)
            }