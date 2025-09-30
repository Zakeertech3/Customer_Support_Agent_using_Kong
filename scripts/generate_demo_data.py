#!/usr/bin/env python3

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DemoDataGenerator:
    def __init__(self):
        self.simple_queries = [
            "What are your business hours?",
            "How do I reset my password?",
            "Where is your office located?",
            "What is your phone number?",
            "Do you offer refunds?",
            "How much does your service cost?",
            "Can I get a demo of your product?",
            "What payment methods do you accept?",
            "How do I contact support?",
            "What services do you provide?"
        ]
        
        self.complex_queries = [
            "I'm having trouble integrating your API with my microservices architecture, specifically with authentication flows and rate limiting configurations.",
            "Can you help me troubleshoot a complex database migration issue involving foreign key constraints and data integrity checks?",
            "I need to implement a distributed system with Kong Gateway, multiple upstream services, load balancing, and circuit breaker patterns.",
            "How do I configure OAuth2 authentication with JWT tokens, refresh token rotation, and proper scope management?",
            "I'm experiencing performance issues with my Kubernetes deployment involving pod autoscaling, resource limits, and network policies.",
            "Can you assist with implementing a comprehensive monitoring solution using Prometheus, Grafana, and custom metrics collection?",
            "I need help setting up a multi-region deployment with data replication, disaster recovery, and automated failover mechanisms."
        ]
        
        self.negative_sentiment_queries = [
            "This is absolutely terrible! Your service has been down for hours and I'm losing money!",
            "I'm extremely frustrated with the lack of support. This is unacceptable!",
            "Your API is completely broken and your documentation is useless!",
            "I've been waiting for hours and no one has helped me. This is ridiculous!",
            "Your system keeps crashing and it's costing me customers. Fix this now!",
            "I'm furious! This is the worst experience I've ever had!",
            "Absolutely disgusted with your terrible service and incompetent staff!"
        ]
        
        self.escalation_scenarios = [
            "I'm absolutely furious! Your complex API integration is completely broken and I can't figure out the authentication flow with OAuth2 and JWT tokens!",
            "This is unacceptable! I've been trying to configure Kong Gateway with microservices for days and nothing works!",
            "I'm extremely disappointed with your terrible documentation for database migrations and foreign key constraints!"
        ]

    def generate_demo_conversations(self, count: int = 10) -> List[Dict[str, Any]]:
        conversations = []
        
        for i in range(count):
            conversation_type = random.choice(["simple", "complex", "negative", "escalation"])
            
            if conversation_type == "simple":
                query = random.choice(self.simple_queries)
                expected_complexity = random.uniform(0.0, 0.3)
                expected_sentiment = random.uniform(0.0, 0.5)
                expected_model = "llama-3.3-70b-versatile"
                expected_escalation = False
                
            elif conversation_type == "complex":
                query = random.choice(self.complex_queries)
                expected_complexity = random.uniform(0.3, 0.8)
                expected_sentiment = random.uniform(-0.1, 0.3)
                expected_model = "openai/gpt-oss-120b"
                expected_escalation = False
                
            elif conversation_type == "negative":
                query = random.choice(self.negative_sentiment_queries)
                expected_complexity = random.uniform(0.1, 0.5)
                expected_sentiment = random.uniform(-1.0, -0.5)
                expected_model = random.choice(["llama-3.3-70b-versatile", "openai/gpt-oss-120b"])
                expected_escalation = True
                
            else:  # escalation
                query = random.choice(self.escalation_scenarios)
                expected_complexity = random.uniform(0.7, 1.0)
                expected_sentiment = random.uniform(-1.0, -0.6)
                expected_model = "openai/gpt-oss-120b"
                expected_escalation = True
            
            conversation = {
                "id": f"demo_conversation_{i+1}",
                "type": conversation_type,
                "query": query,
                "customer_id": f"demo_customer_{i+1}",
                "session_id": f"demo_session_{i+1}",
                "expected_complexity": expected_complexity,
                "expected_sentiment": expected_sentiment,
                "expected_model": expected_model,
                "expected_escalation": expected_escalation,
                "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))).isoformat()
            }
            
            conversations.append(conversation)
        
        return conversations

    def generate_performance_test_data(self) -> Dict[str, Any]:
        return {
            "concurrent_test_queries": [
                "What are your business hours?",
                "How do I reset my password?",
                "Can you help me with API integration?",
                "I'm having trouble with authentication flows",
                "What is your pricing structure?",
                "How do I configure Kong Gateway?",
                "I need help with database migration",
                "What services do you provide?"
            ],
            "cache_test_query": "What are your business hours?",
            "load_test_scenarios": [
                {"name": "Light Load", "users": 5, "queries": 2},
                {"name": "Medium Load", "users": 10, "queries": 3},
                {"name": "Heavy Load", "users": 20, "queries": 2}
            ],
            "response_time_requirements": {
                "simple": {"max_time_ms": 2000, "query": "What are your business hours?"},
                "complex": {"max_time_ms": 5000, "query": "I need help with Kong Gateway configuration and OAuth2 authentication"},
                "cached": {"max_time_ms": 500, "query": "This is a cached query test"}
            }
        }

    def save_demo_data(self, filename: str = "demo_data.json") -> None:
        demo_data = {
            "conversations": self.generate_demo_conversations(20),
            "performance_tests": self.generate_performance_test_data(),
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        print(f"Demo data generated and saved to {filename}")

    def get_test_scenarios_by_category(self) -> Dict[str, List[str]]:
        return {
            "simple": self.simple_queries,
            "complex": self.complex_queries,
            "negative_sentiment": self.negative_sentiment_queries,
            "escalation": self.escalation_scenarios
        }


def main():
    generator = DemoDataGenerator()
    generator.save_demo_data()
    
    scenarios = generator.get_test_scenarios_by_category()
    print("\nDemo Query Categories:")
    for category, queries in scenarios.items():
        print(f"\n{category.upper()}:")
        for i, query in enumerate(queries[:3], 1):
            print(f"  {i}. {query[:80]}{'...' if len(query) > 80 else ''}")
        if len(queries) > 3:
            print(f"  ... and {len(queries) - 3} more")


if __name__ == "__main__":
    main()
  