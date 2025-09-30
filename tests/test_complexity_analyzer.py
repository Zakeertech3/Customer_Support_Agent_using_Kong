import unittest
from app.services.complexity_analyzer import ComplexityAnalyzer, QueryType

class TestComplexityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ComplexityAnalyzer()

    def test_simple_faq_queries(self):
        simple_queries = [
            "What are your business hours?",
            "Where is your office located?",
            "How do I reset my password?",
            "Can you help me with pricing?",
            "What is your contact information?",
            "How much does it cost?"
        ]
        
        for query in simple_queries:
            with self.subTest(query=query):
                complexity = self.analyzer.calculate_complexity(query)
                self.assertLess(complexity, 0.3, f"Query '{query}' should be simple (< 0.3), got {complexity}")
                
                model, rationale, escalation = self.analyzer.get_model_recommendation(complexity)
                self.assertEqual(model, "llama-3.3-70b-versatile")
                self.assertFalse(escalation)

    def test_complex_technical_queries(self):
        complex_queries = [
            "I'm having trouble integrating your API with my microservices architecture, specifically with authentication flows and rate limiting configurations.",
            "Can you help me troubleshoot a complex database migration issue involving foreign key constraints and performance optimization?",
            "I need to configure multiple webhook endpoints with custom authentication middleware for our distributed system architecture.",
            "How do I implement a custom load balancing strategy with health checks and automatic failover for our Kubernetes cluster deployment?"
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                complexity = self.analyzer.calculate_complexity(query)
                self.assertGreaterEqual(complexity, 0.3, f"Query '{query}' should be complex (>= 0.3), got {complexity}")
                
                model, rationale, escalation = self.analyzer.get_model_recommendation(complexity)
                self.assertEqual(model, "openai/gpt-oss-120b")

    def test_multi_step_queries(self):
        multi_step_queries = [
            "I need to first migrate my database schema, then update the API endpoints, configure the load balancer, and finally test the entire system with multiple concurrent users.",
            "Can you walk me through setting up OAuth authentication, configuring rate limiting, implementing caching, and monitoring the performance metrics?",
            "I want to integrate multiple third-party services, handle webhook callbacks, process async messages, and generate comprehensive analytics reports."
        ]
        
        for query in multi_step_queries:
            with self.subTest(query=query):
                analysis = self.analyzer.analyze_query(query)
                self.assertIn(analysis["question_type"], ["multi_step", "integration", "technical"])
                self.assertGreaterEqual(analysis["complexity_score"], 0.4)

    def test_technical_terms_counting(self):
        technical_query = "Configure OAuth JWT authentication with Redis cache and PostgreSQL database"
        non_technical_query = "What time do you open and close?"
        
        tech_count = self.analyzer._count_technical_terms(technical_query.lower())
        non_tech_count = self.analyzer._count_technical_terms(non_technical_query.lower())
        
        self.assertGreater(tech_count, 0)
        self.assertEqual(non_tech_count, 0)

    def test_question_type_analysis(self):
        test_cases = [
            ("What are your business hours?", QueryType.SIMPLE_FAQ),
            ("How do I integrate your API with my system?", QueryType.INTEGRATION),
            ("I'm having trouble with my database connection", QueryType.TROUBLESHOOTING),
            ("Configure authentication middleware for the system", QueryType.TECHNICAL)
        ]
        
        for query, expected_type in test_cases:
            with self.subTest(query=query):
                detected_type = self.analyzer._analyze_question_type(query.lower())
                self.assertEqual(detected_type, expected_type)

    def test_escalation_flag_high_complexity(self):
        very_complex_query = "I need comprehensive assistance with migrating our entire microservices architecture from monolithic design to containerized Kubernetes deployment with custom service mesh configuration, advanced monitoring, distributed tracing, automated CI/CD pipelines, multi-region disaster recovery, and performance optimization across multiple database systems including PostgreSQL, MongoDB, and Redis clusters."
        
        complexity = self.analyzer.calculate_complexity(very_complex_query)
        model, rationale, escalation = self.analyzer.get_model_recommendation(complexity)
        
        self.assertGreaterEqual(complexity, 0.8)
        self.assertTrue(escalation)
        self.assertEqual(model, "openai/gpt-oss-120b")

    def test_empty_and_edge_cases(self):
        edge_cases = ["", "   ", "a", "?", "help"]
        
        for query in edge_cases:
            with self.subTest(query=repr(query)):
                complexity = self.analyzer.calculate_complexity(query)
                self.assertGreaterEqual(complexity, 0.0)
                self.assertLessEqual(complexity, 1.0)

    def test_complexity_score_bounds(self):
        test_queries = [
            "Hi",
            "What is your API documentation?",
            "I need help with complex microservices architecture integration involving multiple authentication systems, database migrations, performance optimization, and distributed caching mechanisms."
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                complexity = self.analyzer.calculate_complexity(query)
                self.assertGreaterEqual(complexity, 0.0)
                self.assertLessEqual(complexity, 1.0)

    def test_analyze_query_complete_result(self):
        query = "How do I configure OAuth authentication with JWT tokens?"
        result = self.analyzer.analyze_query(query)
        
        required_keys = [
            "query", "complexity_score", "recommended_model", 
            "rationale", "escalation_flag", "question_type", 
            "technical_terms_count", "word_count"
        ]
        
        for key in required_keys:
            self.assertIn(key, result)
        
        self.assertEqual(result["query"], query)
        self.assertIsInstance(result["complexity_score"], float)
        self.assertIsInstance(result["escalation_flag"], bool)
        self.assertGreater(result["technical_terms_count"], 0)

if __name__ == "__main__":
    unittest.main()