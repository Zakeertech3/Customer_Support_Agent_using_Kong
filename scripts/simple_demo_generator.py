#!/usr/bin/env python3

import json
from datetime import datetime

def generate_demo_data():
    demo_data = {
        "simple_queries": [
            "What are your business hours?",
            "How do I reset my password?",
            "Where is your office located?",
            "What is your phone number?",
            "Do you offer refunds?"
        ],
        "complex_queries": [
            "I'm having trouble integrating your API with my microservices architecture, specifically with authentication flows and rate limiting configurations.",
            "Can you help me troubleshoot a complex database migration issue involving foreign key constraints and data integrity checks?",
            "I need to implement a distributed system with Kong Gateway, multiple upstream services, load balancing, and circuit breaker patterns."
        ],
        "negative_sentiment_queries": [
            "This is absolutely terrible! Your service has been down for hours and I'm losing money!",
            "I'm extremely frustrated with the lack of support. This is unacceptable!",
            "Your API is completely broken and your documentation is useless!"
        ],
        "performance_test_data": {
            "concurrent_test_queries": [
                "What are your business hours?",
                "How do I reset my password?",
                "Can you help me with API integration?",
                "I'm having trouble with authentication flows"
            ],
            "cache_test_query": "What are your business hours?",
            "load_test_scenarios": [
                {"name": "Light Load", "users": 5, "queries": 2},
                {"name": "Medium Load", "users": 10, "queries": 3},
                {"name": "Heavy Load", "users": 20, "queries": 2}
            ]
        },
        "generated_at": datetime.utcnow().isoformat(),
        "version": "1.0"
    }
    
    with open("demo_data.json", 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, indent=2, ensure_ascii=False)
    
    print("Demo data generated and saved to demo_data.json")
    print(f"Generated {len(demo_data['simple_queries'])} simple queries")
    print(f"Generated {len(demo_data['complex_queries'])} complex queries")
    print(f"Generated {len(demo_data['negative_sentiment_queries'])} negative sentiment queries")
    
    return demo_data

if __name__ == "__main__":
    generate_demo_data()