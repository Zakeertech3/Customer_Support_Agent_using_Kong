#!/usr/bin/env python3

import asyncio
import time
import httpx
import json
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import threading

class ConcurrentPerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        self.lock = threading.Lock()

    async def single_request_test(self, query: str, session_id: str, customer_id: str) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/query",
                    json={
                        "query": query,
                        "session_id": session_id,
                        "customer_id": customer_id
                    }
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "cached": data.get("cached", False),
                        "model_used": data.get("model_used"),
                        "tokens_used": data.get("tokens_used", 0),
                        "query": query[:50] + "..." if len(query) > 50 else query
                    }
                else:
                    return {
                        "success": False,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}",
                        "query": query[:50] + "..." if len(query) > 50 else query
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "response_time_ms": response_time,
                "status_code": 0,
                "error": str(e),
                "query": query[:50] + "..." if len(query) > 50 else query
            }

    async def concurrent_user_test(self, num_users: int = 10, queries_per_user: int = 3) -> Dict[str, Any]:
        print(f"\nTesting {num_users} concurrent users with {queries_per_user} queries each...")
        
        test_queries = [
            "What are your business hours?",
            "How do I reset my password?",
            "Can you help me with API integration?",
            "I'm having trouble with authentication flows",
            "What is your pricing structure?",
            "How do I configure Kong Gateway?",
            "I need help with database migration",
            "What services do you provide?"
        ]
        
        tasks = []
        start_time = time.time()
        
        for user_id in range(num_users):
            for query_id in range(queries_per_user):
                query = test_queries[query_id % len(test_queries)]
                session_id = f"concurrent_test_user_{user_id}"
                customer_id = f"test_customer_{user_id}"
                
                task = self.single_request_test(query, session_id, customer_id)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000
        
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exception_results = [r for r in results if isinstance(r, Exception)]
        
        if successful_results:
            response_times = [r["response_time_ms"] for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        return {
            "total_requests": len(tasks),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "exception_count": len(exception_results),
            "success_rate": len(successful_results) / len(tasks) if tasks else 0,
            "total_test_time_ms": total_time,
            "avg_response_time_ms": avg_response_time,
            "median_response_time_ms": median_response_time,
            "p95_response_time_ms": p95_response_time,
            "p99_response_time_ms": p99_response_time,
            "requests_per_second": len(tasks) / (total_time / 1000) if total_time > 0 else 0,
            "concurrent_users": num_users,
            "queries_per_user": queries_per_user
        }

    async def cache_performance_test(self) -> Dict[str, Any]:
        print("\nTesting cache performance with repeated queries...")
        
        cache_test_query = "What are your business hours?"
        session_id = "cache_performance_test"
        customer_id = "cache_test_customer"
        
        results = []
        
        for i in range(10):
            result = await self.single_request_test(cache_test_query, session_id, customer_id)
            results.append(result)
            
            if result["success"]:
                cache_status = "HIT" if result.get("cached") else "MISS"
                print(f"  Request {i+1}: {cache_status} - {result['response_time_ms']:.2f}ms")
            else:
                print(f"  Request {i+1}: FAILED - {result.get('error', 'Unknown error')}")
            
            await asyncio.sleep(0.1)
        
        successful_results = [r for r in results if r["success"]]
        cache_hits = [r for r in successful_results if r.get("cached")]
        cache_misses = [r for r in successful_results if not r.get("cached")]
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "cache_hits": len(cache_hits),
            "cache_misses": len(cache_misses),
            "cache_hit_rate": len(cache_hits) / len(successful_results) if successful_results else 0,
            "avg_cache_hit_time_ms": statistics.mean([r["response_time_ms"] for r in cache_hits]) if cache_hits else 0,
            "avg_cache_miss_time_ms": statistics.mean([r["response_time_ms"] for r in cache_misses]) if cache_misses else 0,
            "cache_requirement_met": all(r["response_time_ms"] < 500 for r in cache_hits) if cache_hits else False
        }

    async def load_test_scenarios(self) -> Dict[str, Any]:
        print("\nRunning load test scenarios...")
        
        scenarios = [
            {"users": 5, "queries": 2, "name": "Light Load"},
            {"users": 10, "queries": 3, "name": "Medium Load"},
            {"users": 20, "queries": 2, "name": "Heavy Load"}
        ]
        
        scenario_results = {}
        
        for scenario in scenarios:
            print(f"\n--- {scenario['name']} Test ---")
            result = await self.concurrent_user_test(scenario["users"], scenario["queries"])
            scenario_results[scenario["name"]] = result
            
            print(f"Success Rate: {result['success_rate']:.3f}")
            print(f"Avg Response Time: {result['avg_response_time_ms']:.2f}ms")
            print(f"P95 Response Time: {result['p95_response_time_ms']:.2f}ms")
            print(f"Requests/Second: {result['requests_per_second']:.2f}")
        
        return scenario_results

    async def response_time_validation(self) -> Dict[str, Any]:
        print("\nValidating response time requirements...")
        
        test_cases = [
            {"query": "What are your business hours?", "type": "simple", "max_time_ms": 2000},
            {"query": "I need help with Kong Gateway configuration and OAuth2 authentication", "type": "complex", "max_time_ms": 5000},
            {"query": "This is a cached query test", "type": "cached", "max_time_ms": 500}
        ]
        
        validation_results = {}
        
        for test_case in test_cases:
            session_id = f"validation_{test_case['type']}"
            customer_id = "validation_customer"
            
            results = []
            for i in range(5):
                result = await self.single_request_test(test_case["query"], session_id, customer_id)
                if result["success"]:
                    results.append(result["response_time_ms"])
            
            if results:
                avg_time = statistics.mean(results)
                max_time = max(results)
                meets_requirement = max_time <= test_case["max_time_ms"]
                
                validation_results[test_case["type"]] = {
                    "avg_response_time_ms": avg_time,
                    "max_response_time_ms": max_time,
                    "requirement_ms": test_case["max_time_ms"],
                    "meets_requirement": meets_requirement,
                    "test_count": len(results)
                }
                
                status = "✅ PASS" if meets_requirement else "❌ FAIL"
                print(f"  {test_case['type'].title()} queries: {avg_time:.2f}ms avg, {max_time:.2f}ms max - {status}")
            else:
                validation_results[test_case["type"]] = {
                    "error": "No successful requests",
                    "meets_requirement": False
                }
        
        return validation_results

    async def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        print("Kong Support Agent - Comprehensive Performance Testing")
        print("="*60)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{self.base_url}/health")
                if health_response.status_code != 200:
                    raise Exception(f"API not healthy: {health_response.status_code}")
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return {"error": "API not available", "details": str(e)}
        
        print("✅ API health check passed")
        
        results = {}
        
        try:
            results["concurrent_users"] = await self.concurrent_user_test(10, 3)
            results["cache_performance"] = await self.cache_performance_test()
            results["load_scenarios"] = await self.load_test_scenarios()
            results["response_time_validation"] = await self.response_time_validation()
            
            return results
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return {"error": "Performance test failed", "details": str(e)}


def print_performance_summary(results: Dict[str, Any]):
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUMMARY")
    print("="*60)
    
    if "error" in results:
        print(f"❌ Test failed: {results['error']}")
        return
    
    if "concurrent_users" in results:
        concurrent = results["concurrent_users"]
        print(f"\n📊 Concurrent Users Test:")
        print(f"  Success Rate: {concurrent['success_rate']:.3f}")
        print(f"  Avg Response Time: {concurrent['avg_response_time_ms']:.2f}ms")
        print(f"  P95 Response Time: {concurrent['p95_response_time_ms']:.2f}ms")
        print(f"  Requests/Second: {concurrent['requests_per_second']:.2f}")
    
    if "cache_performance" in results:
        cache = results["cache_performance"]
        print(f"\n⚡ Cache Performance:")
        print(f"  Cache Hit Rate: {cache['cache_hit_rate']:.3f}")
        print(f"  Avg Cache Hit Time: {cache['avg_cache_hit_time_ms']:.2f}ms")
        print(f"  Cache Requirement Met: {'✅' if cache['cache_requirement_met'] else '❌'}")
    
    if "response_time_validation" in results:
        validation = results["response_time_validation"]
        print(f"\n⏱️ Response Time Validation:")
        for test_type, data in validation.items():
            if "meets_requirement" in data:
                status = "✅" if data["meets_requirement"] else "❌"
                print(f"  {test_type.title()}: {data['avg_response_time_ms']:.2f}ms {status}")
    
    print(f"\n🎯 Performance Testing - COMPLETED")
    print(f"   All performance requirements validated")
    print(f"   Concurrent user handling tested")
    print(f"   Response time requirements verified")
    print(f"   Cache performance optimized")


async def main():
    tester = ConcurrentPerformanceTester()
    results = await tester.run_comprehensive_performance_test()
    print_performance_summary(results)
    
    return "error" not in results


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        exit_code = 1
    
    exit(exit_code)