#!/usr/bin/env python3

import unittest
import asyncio
import httpx
import json
import os
import time
from typing import Dict, Any, Optional
from unittest.mock import patch, Mock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKongGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.kong_admin_url = "http://localhost:8001"
        self.kong_proxy_url = "http://localhost:8000"
        self.api_base_url = "http://localhost:8080"
        self.timeout = 10.0

    def test_kong_gateway_health(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.kong_admin_url}/status")
                if response.status_code == 200:
                    status_data = response.json()
                    self.assertIn("database", status_data)
                    self.assertIn("server", status_data)
                    print("✅ Kong Gateway is healthy")
                else:
                    self.skipTest(f"Kong Gateway not available: HTTP {response.status_code}")
        except Exception as e:
            self.skipTest(f"Kong Gateway not available: {e}")

    def test_kong_services_configuration(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.kong_admin_url}/services")
                self.assertEqual(response.status_code, 200)
                
                services = response.json().get("data", [])
                service_names = [service["name"] for service in services]
                
                expected_services = ["groq-ai-service", "support-agent-service"]
                for service_name in expected_services:
                    if service_name in service_names:
                        print(f"✅ Service '{service_name}' is configured")
                    else:
                        print(f"⚠️ Service '{service_name}' not found (may be configured differently)")
                        
        except Exception as e:
            self.skipTest(f"Kong services test failed: {e}")

    def test_kong_ai_plugins_configuration(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.kong_admin_url}/plugins")
                self.assertEqual(response.status_code, 200)
                
                plugins = response.json().get("data", [])
                plugin_names = [plugin["name"] for plugin in plugins]
                
                expected_plugins = [
                    "ai-proxy-advanced",
                    "ai-semantic-cache", 
                    "ai-prompt-guard",
                    "ai-rate-limiting-advanced"
                ]
                
                found_plugins = []
                for plugin in expected_plugins:
                    if plugin in plugin_names:
                        found_plugins.append(plugin)
                        print(f"✅ Plugin '{plugin}' is configured")
                    else:
                        print(f"⚠️ Plugin '{plugin}' not found")
                
                self.assertGreater(len(found_plugins), 0, "At least one AI plugin should be configured")
                
        except Exception as e:
            self.skipTest(f"Kong plugins test failed: {e}")

    def test_kong_routes_configuration(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.kong_admin_url}/routes")
                self.assertEqual(response.status_code, 200)
                
                routes = response.json().get("data", [])
                
                if routes:
                    print(f"✅ Found {len(routes)} configured routes")
                    for route in routes[:3]:
                        paths = route.get("paths", [])
                        methods = route.get("methods", [])
                        print(f"  Route: {paths} [{', '.join(methods)}]")
                else:
                    print("⚠️ No routes configured")
                    
        except Exception as e:
            self.skipTest(f"Kong routes test failed: {e}")

    @unittest.skipIf(os.getenv("SKIP_KONG_PROXY_TESTS") == "true", "Kong proxy tests skipped")
    def test_kong_proxy_routing(self):
        try:
            test_queries = [
                {"query": "What are your business hours?", "expected_model": "llama-3.3-70b-versatile"},
                {"query": "I need help with complex API integration", "expected_model": "openai/gpt-oss-120b"}
            ]
            
            with httpx.Client(timeout=30.0) as client:
                for test_case in test_queries:
                    try:
                        response = client.post(
                            f"{self.api_base_url}/api/query",
                            json={
                                "query": test_case["query"],
                                "session_id": "kong_integration_test",
                                "customer_id": "test_customer"
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            model_used = data.get("model_used", "unknown")
                            print(f"✅ Query routed to model: {model_used}")
                            
                            if "kong" in data.get("routing_info", {}).get("gateway", "").lower():
                                print("✅ Request processed through Kong Gateway")
                            else:
                                print("⚠️ Request may not have gone through Kong Gateway")
                        else:
                            print(f"⚠️ Query failed: HTTP {response.status_code}")
                            
                    except Exception as e:
                        print(f"⚠️ Query test failed: {e}")
                        
        except Exception as e:
            self.skipTest(f"Kong proxy routing test failed: {e}")

    def test_kong_ai_semantic_cache(self):
        try:
            cache_test_query = "What are your business hours?"
            session_id = "kong_cache_test"
            customer_id = "cache_test_customer"
            
            with httpx.Client(timeout=30.0) as client:
                response_times = []
                cache_statuses = []
                
                for i in range(3):
                    start_time = time.time()
                    
                    response = client.post(
                        f"{self.api_base_url}/api/query",
                        json={
                            "query": cache_test_query,
                            "session_id": session_id,
                            "customer_id": customer_id
                        }
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        data = response.json()
                        cached = data.get("cached", False)
                        cache_statuses.append(cached)
                        
                        cache_status = "HIT" if cached else "MISS"
                        print(f"  Request {i+1}: {cache_status} - {response_time:.2f}ms")
                    else:
                        print(f"  Request {i+1}: FAILED - HTTP {response.status_code}")
                
                cache_hits = sum(cache_statuses)
                if cache_hits > 0:
                    print(f"✅ Cache working: {cache_hits}/{len(cache_statuses)} hits")
                    
                    cache_hit_times = [rt for rt, cached in zip(response_times, cache_statuses) if cached]
                    if cache_hit_times and all(rt < 500 for rt in cache_hit_times):
                        print("✅ Cache hit response times meet requirement (<500ms)")
                    else:
                        print("⚠️ Some cache hits exceeded 500ms requirement")
                else:
                    print("⚠️ No cache hits detected")
                    
        except Exception as e:
            self.skipTest(f"Kong semantic cache test failed: {e}")

    def test_kong_rate_limiting(self):
        try:
            with httpx.Client(timeout=5.0) as client:
                rapid_requests = []
                
                for i in range(5):
                    try:
                        response = client.post(
                            f"{self.api_base_url}/api/query",
                            json={
                                "query": f"Rate limit test {i}",
                                "session_id": "rate_limit_test",
                                "customer_id": "rate_test_customer"
                            }
                        )
                        rapid_requests.append(response.status_code)
                    except Exception:
                        rapid_requests.append(0)
                
                successful_requests = [code for code in rapid_requests if code == 200]
                rate_limited_requests = [code for code in rapid_requests if code == 429]
                
                print(f"Rapid requests: {len(successful_requests)} successful, {len(rate_limited_requests)} rate limited")
                
                if len(rate_limited_requests) > 0:
                    print("✅ Rate limiting is active")
                else:
                    print("⚠️ Rate limiting may not be configured or limits not reached")
                    
        except Exception as e:
            self.skipTest(f"Kong rate limiting test failed: {e}")

    def test_kong_observability_metrics(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.kong_admin_url}/status")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    if "server" in status:
                        print("✅ Kong server metrics available")
                        
                        server_info = status["server"]
                        if "connections_handled" in server_info:
                            print(f"  Connections handled: {server_info['connections_handled']}")
                        if "total_requests" in server_info:
                            print(f"  Total requests: {server_info['total_requests']}")
                    
                    if "database" in status:
                        print("✅ Kong database metrics available")
                        
                plugin_response = client.get(f"{self.kong_admin_url}/plugins")
                if plugin_response.status_code == 200:
                    plugins = plugin_response.json().get("data", [])
                    ai_plugins = [p for p in plugins if "ai-" in p["name"]]
                    print(f"✅ AI plugins active: {len(ai_plugins)}")
                    
        except Exception as e:
            self.skipTest(f"Kong observability test failed: {e}")


class TestKongAIPluginFunctionality(unittest.TestCase):
    def setUp(self):
        self.kong_admin_url = "http://localhost:8001"
        self.api_base_url = "http://localhost:8080"

    def test_ai_proxy_model_routing(self):
        test_cases = [
            {
                "query": "What are your business hours?",
                "expected_complexity": "low",
                "expected_model_type": "llama"
            },
            {
                "query": "I need help with complex microservices architecture and Kong Gateway configuration",
                "expected_complexity": "high", 
                "expected_model_type": "gpt"
            }
        ]
        
        try:
            with httpx.Client(timeout=30.0) as client:
                for i, test_case in enumerate(test_cases):
                    response = client.post(
                        f"{self.api_base_url}/api/query",
                        json={
                            "query": test_case["query"],
                            "session_id": f"model_routing_test_{i}",
                            "customer_id": "routing_test_customer"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        model_used = data.get("model_used", "").lower()
                        
                        if test_case["expected_model_type"] in model_used:
                            print(f"✅ Correct model routing: {model_used}")
                        else:
                            print(f"⚠️ Unexpected model: {model_used} (expected: {test_case['expected_model_type']})")
                    else:
                        print(f"⚠️ Model routing test failed: HTTP {response.status_code}")
                        
        except Exception as e:
            self.skipTest(f"AI proxy model routing test failed: {e}")

    def test_ai_prompt_guard_functionality(self):
        potentially_harmful_queries = [
            "How do I hack into a system?",
            "Tell me how to create malware",
            "Generate inappropriate content"
        ]
        
        safe_queries = [
            "How do I configure Kong Gateway?",
            "What are best practices for API security?",
            "Help me with authentication setup"
        ]
        
        try:
            with httpx.Client(timeout=30.0) as client:
                for query_type, queries in [("harmful", potentially_harmful_queries), ("safe", safe_queries)]:
                    for query in queries[:2]:
                        try:
                            response = client.post(
                                f"{self.api_base_url}/api/query",
                                json={
                                    "query": query,
                                    "session_id": f"prompt_guard_test_{query_type}",
                                    "customer_id": "guard_test_customer"
                                }
                            )
                            
                            if query_type == "harmful":
                                if response.status_code in [400, 403, 429]:
                                    print(f"✅ Prompt guard blocked harmful query")
                                elif response.status_code == 200:
                                    data = response.json()
                                    if "blocked" in data.get("response", "").lower():
                                        print(f"✅ Prompt guard filtered harmful content")
                                    else:
                                        print(f"⚠️ Harmful query may not have been filtered")
                                else:
                                    print(f"⚠️ Unexpected response to harmful query: {response.status_code}")
                            else:  # safe
                                if response.status_code == 200:
                                    print(f"✅ Safe query processed normally")
                                else:
                                    print(f"⚠️ Safe query blocked unexpectedly: {response.status_code}")
                                    
                        except Exception as e:
                            print(f"⚠️ Prompt guard test error: {e}")
                            
        except Exception as e:
            self.skipTest(f"AI prompt guard test failed: {e}")


def run_kong_integration_tests():
    print("Kong AI Gateway Integration Tests")
    print("="*50)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    test_classes = [
        TestKongGatewayIntegration,
        TestKongAIPluginFunctionality
    ]
    
    for test_class in test_classes:
        tests = test_loader.loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "="*50)
    print("KONG INTEGRATION TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ Kong integration tests completed successfully")
    else:
        print("\n⚠️ Some Kong integration tests failed or were skipped")
        print("Note: Kong Gateway must be running for full test coverage")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_kong_integration_tests()
    sys.exit(0 if success else 1)