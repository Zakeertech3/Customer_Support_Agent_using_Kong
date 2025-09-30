import time
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.85, max_cache_size: int = 1000, ttl_seconds: int = 3600):
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.query_vectors: Dict[str, np.ndarray] = {}
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.fitted = False
        
    def _get_cache_key(self, query: str, model: str) -> str:
        content = f"{query}:{model}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _vectorize_query(self, query: str) -> Optional[np.ndarray]:
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided for vectorization")
                return None
            
            if not self.fitted:
                if len(self.query_vectors) > 0:
                    all_queries = list(self.query_vectors.keys())
                    all_queries.append(query)
                    self.vectorizer.fit(all_queries)
                    self.fitted = True
                    for cached_query in self.query_vectors:
                        try:
                            self.query_vectors[cached_query] = self.vectorizer.transform([cached_query]).toarray()[0]
                        except Exception as e:
                            logger.warning(f"Failed to re-vectorize cached query: {e}")
                            del self.query_vectors[cached_query]
                else:
                    self.vectorizer.fit([query])
                    self.fitted = True
            
            vector = self.vectorizer.transform([query]).toarray()[0]
            return vector
        except Exception as e:
            logger.error(f"Query vectorization failed: {e}")
            return None
    
    def _find_similar_query(self, query: str, model: str) -> Optional[str]:
        try:
            if not self.query_vectors:
                return None
                
            query_vector = self._vectorize_query(query)
            if query_vector is None:
                logger.warning("Failed to vectorize query for similarity search")
                return None
            
            best_similarity = 0.0
            best_key = None
            
            for cached_key, cached_data in self.cache.items():
                try:
                    if cached_data.get('model') != model:
                        continue
                        
                    cached_query = cached_data['query']
                    if cached_query in self.query_vectors:
                        cached_vector = self.query_vectors[cached_query]
                        if cached_vector is not None:
                            similarity = cosine_similarity([query_vector], [cached_vector])[0][0]
                            
                            if similarity > best_similarity and similarity >= self.similarity_threshold:
                                best_similarity = similarity
                                best_key = cached_key
                except Exception as e:
                    logger.warning(f"Error comparing with cached query {cached_key}: {e}")
                    continue
            
            return best_key
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return None
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        created_at = datetime.fromisoformat(cache_entry['created_at'])
        return datetime.utcnow() - created_at > timedelta(seconds=self.ttl_seconds)
    
    def _cleanup_expired(self):
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        if key in self.cache:
            query = self.cache[key]['query']
            if query in self.query_vectors:
                del self.query_vectors[query]
            del self.cache[key]
    
    def _evict_oldest(self):
        if not self.cache:
            return
            
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: datetime.fromisoformat(self.cache[k]['created_at']))
        self._remove_entry(oldest_key)
    
    def get(self, query: str, model: str) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to cache")
                return None
            
            self._cleanup_expired()
            
            cache_key = self._get_cache_key(query, model)
            
            if cache_key in self.cache and not self._is_expired(self.cache[cache_key]):
                response_time = (time.time() - start_time) * 1000
                logger.info(f"Cache hit for query hash {cache_key[:8]} in {response_time:.2f}ms")
                return {
                    'response': self.cache[cache_key]['response'],
                    'cached': True,
                    'response_time_ms': response_time,
                    'similarity': 1.0
                }
            
            similar_key = self._find_similar_query(query, model)
            if similar_key and not self._is_expired(self.cache[similar_key]):
                response_time = (time.time() - start_time) * 1000
                cached_query = self.cache[similar_key]['query']
                
                try:
                    query_vector = self._vectorize_query(query)
                    cached_vector = self.query_vectors.get(cached_query)
                    
                    if query_vector is not None and cached_vector is not None:
                        similarity = cosine_similarity([query_vector], [cached_vector])[0][0]
                        
                        logger.info(f"Semantic cache hit for query with {similarity:.3f} similarity in {response_time:.2f}ms")
                        return {
                            'response': self.cache[similar_key]['response'],
                            'cached': True,
                            'response_time_ms': response_time,
                            'similarity': similarity
                        }
                except Exception as e:
                    logger.warning(f"Failed to calculate similarity for cache hit: {e}")
                    return {
                        'response': self.cache[similar_key]['response'],
                        'cached': True,
                        'response_time_ms': response_time,
                        'similarity': self.similarity_threshold
                    }
            
            return None
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None
    
    def set(self, query: str, model: str, response: str, tokens_used: int = 0):
        try:
            if not query or not query.strip() or not response:
                logger.warning("Invalid query or response provided to cache")
                return
            
            if len(self.cache) >= self.max_cache_size:
                self._evict_oldest()
            
            cache_key = self._get_cache_key(query, model)
            query_vector = self._vectorize_query(query)
            
            self.cache[cache_key] = {
                'query': query,
                'model': model,
                'response': response,
                'tokens_used': tokens_used,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if query_vector is not None:
                self.query_vectors[query] = query_vector
            else:
                logger.warning(f"Failed to vectorize query for caching: {query[:50]}...")
            
            logger.info(f"Cached response for query hash {cache_key[:8]} with model {model}")
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        total_entries = len(self.cache)
        expired_count = sum(1 for entry in self.cache.values() if self._is_expired(entry))
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_count,
            'expired_entries': expired_count,
            'cache_size_limit': self.max_cache_size,
            'similarity_threshold': self.similarity_threshold,
            'ttl_seconds': self.ttl_seconds
        }

class PerformanceMetrics:
    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = {
            'response_times': [],
            'token_usage': [],
            'cache_hits': [],
            'model_usage': [],
            'error_rates': []
        }
        self.session_start = datetime.utcnow()
    
    def record_response_time(self, endpoint: str, response_time_ms: float, model: str = None, cached: bool = False):
        self.metrics['response_times'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'response_time_ms': response_time_ms,
            'model': model,
            'cached': cached
        })
    
    def record_token_usage(self, model: str, tokens_used: int, cost: float = 0.0):
        self.metrics['token_usage'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'model': model,
            'tokens_used': tokens_used,
            'cost': cost
        })
    
    def record_cache_hit(self, hit: bool, similarity: float = None):
        self.metrics['cache_hits'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'hit': hit,
            'similarity': similarity
        })
    
    def record_model_usage(self, model: str, complexity_score: float = None, reason: str = None):
        self.metrics['model_usage'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'model': model,
            'complexity_score': complexity_score,
            'reason': reason
        })
    
    def record_error(self, error_type: str, endpoint: str, model: str = None):
        self.metrics['error_rates'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'endpoint': endpoint,
            'model': model
        })
    
    def get_summary_stats(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        session_duration = (now - self.session_start).total_seconds()
        
        response_times = [m['response_time_ms'] for m in self.metrics['response_times']]
        cache_hits = [m for m in self.metrics['cache_hits'] if m['hit']]
        total_requests = len(self.metrics['response_times'])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        cache_hit_rate = len(cache_hits) / total_requests if total_requests > 0 else 0
        
        cached_responses = [m for m in self.metrics['response_times'] if m.get('cached', False)]
        avg_cache_response_time = sum(m['response_time_ms'] for m in cached_responses) / len(cached_responses) if cached_responses else 0
        
        total_tokens = sum(m['tokens_used'] for m in self.metrics['token_usage'])
        total_cost = sum(m['cost'] for m in self.metrics['token_usage'])
        
        model_counts = {}
        for m in self.metrics['model_usage']:
            model = m['model']
            model_counts[model] = model_counts.get(model, 0) + 1
        
        error_count = len(self.metrics['error_rates'])
        error_rate = error_count / total_requests if total_requests > 0 else 0
        
        return {
            'session_duration_seconds': session_duration,
            'total_requests': total_requests,
            'avg_response_time_ms': round(avg_response_time, 2),
            'avg_cache_response_time_ms': round(avg_cache_response_time, 2),
            'cache_hit_rate': round(cache_hit_rate, 3),
            'total_tokens_used': total_tokens,
            'total_cost': round(total_cost, 4),
            'model_usage_counts': model_counts,
            'error_count': error_count,
            'error_rate': round(error_rate, 3),
            'cache_performance_improvement': round(avg_response_time - avg_cache_response_time, 2) if avg_cache_response_time > 0 else 0
        }
    
    def get_recent_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_response_times = [
            m for m in self.metrics['response_times'] 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        recent_cache_hits = [
            m for m in self.metrics['cache_hits'] 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time and m['hit']
        ]
        
        recent_errors = [
            m for m in self.metrics['error_rates'] 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        total_recent = len(recent_response_times)
        recent_cache_rate = len(recent_cache_hits) / total_recent if total_recent > 0 else 0
        recent_error_rate = len(recent_errors) / total_recent if total_recent > 0 else 0
        
        recent_avg_time = sum(m['response_time_ms'] for m in recent_response_times) / total_recent if total_recent > 0 else 0
        
        return {
            'time_window_minutes': minutes,
            'recent_requests': total_recent,
            'recent_avg_response_time_ms': round(recent_avg_time, 2),
            'recent_cache_hit_rate': round(recent_cache_rate, 3),
            'recent_error_rate': round(recent_error_rate, 3)
        }

class CostCalculator:
    MODEL_COSTS = {
        'llama-3.3-70b-versatile': {'input': 0.00059, 'output': 0.00079},
        'openai/gpt-oss-120b': {'input': 0.0015, 'output': 0.002},
        'llama-3.1-8b-instant': {'input': 0.00005, 'output': 0.00008}
    }
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in cls.MODEL_COSTS:
            return 0.0
        
        costs = cls.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs['input']
        output_cost = (output_tokens / 1000) * costs['output']
        
        return input_cost + output_cost
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return len(text.split()) * 1.3

semantic_cache = SemanticCache()
performance_metrics = PerformanceMetrics()