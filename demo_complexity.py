#!/usr/bin/env python3

import logging
from app.services.complexity_analyzer import ComplexityAnalyzer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def demo_complexity_analysis():
    analyzer = ComplexityAnalyzer()
    
    demo_queries = [
        "What are your business hours?",
        "How do I reset my password?",
        "How do I integrate your API with my system?",
        "I'm having trouble with my database connection",
        "Configure OAuth authentication with JWT tokens and Redis cache",
        "I need comprehensive assistance with migrating our entire microservices architecture from monolithic design to containerized Kubernetes deployment with custom service mesh configuration, advanced monitoring, distributed tracing, automated CI/CD pipelines, multi-region disaster recovery, and performance optimization across multiple database systems including PostgreSQL, MongoDB, and Redis clusters."
    ]
    
    print("=== Query Complexity Analysis Demo ===\n")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"Query {i}: {query}")
        analysis = analyzer.analyze_query(query)
        
        print(f"  Complexity Score: {analysis['complexity_score']:.3f}")
        print(f"  Question Type: {analysis['question_type']}")
        print(f"  Recommended Model: {analysis['recommended_model']}")
        print(f"  Escalation Flag: {analysis['escalation_flag']}")
        print(f"  Technical Terms: {analysis['technical_terms_count']}")
        print(f"  Word Count: {analysis['word_count']}")
        print(f"  Rationale: {analysis['rationale']}")
        print("-" * 80)

if __name__ == "__main__":
    demo_complexity_analysis()