import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.services.complexity_analyzer import ComplexityAnalyzer, QueryType
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.escalation_manager import EscalationManager
from app.models import ConversationMessage, EscalationTicket, SessionData


class TestComplexityAnalyzerUnit(unittest.TestCase):
    def setUp(self):
        self.analyzer = ComplexityAnalyzer()

    def test_simple_queries_routing(self):
        simple_queries = [
            "What are your business hours?",
            "Where is your office?",
            "How much does it cost?",
            "Can you help me?",
            "What is your phone number?"
        ]
        
        for query in simple_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_query(query)
                self.assertTrue(result["analysis_successful"])
                self.assertLess(result["complexity_score"], 0.3)
                self.assertEqual(result["recommended_model"], "llama-3.3-70b-versatile")
                self.assertFalse(result["escalation_flag"])

    def test_complex_queries_routing(self):
        complex_queries = [
            "I'm having trouble integrating your API with my microservices architecture, specifically with authentication flows and rate limiting configurations.",
            "Can you help me troubleshoot a complex database migration issue involving foreign key constraints and data integrity checks?",
            "I need to implement a distributed caching system with Redis clustering and automatic failover mechanisms for high availability."
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_query(query)
                self.assertTrue(result["analysis_successful"])
                self.assertGreaterEqual(result["complexity_score"], 0.3)
                self.assertEqual(result["recommended_model"], "openai/gpt-oss-120b")

    def test_escalation_threshold_queries(self):
        escalation_queries = [
            "This is an extremely complex multi-phase enterprise integration project involving microservices architecture, API gateway configuration, database migrations, security implementations, monitoring systems, and performance optimization across multiple cloud environments with strict compliance requirements."
        ]
        
        for query in escalation_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_query(query)
                self.assertTrue(result["analysis_successful"])
                self.assertGreaterEqual(result["complexity_score"], 0.8)
                self.assertTrue(result["escalation_flag"])

    def test_empty_query_handling(self):
        result = self.analyzer.analyze_query("")
        self.assertFalse(result["analysis_successful"])
        self.assertEqual(result["complexity_score"], 0.0)
        self.assertIn("error", result)

    def test_technical_terms_detection(self):
        technical_query = "Configure Kong API Gateway with OAuth2 authentication, JWT tokens, rate limiting, and SSL certificates"
        result = self.analyzer.analyze_query(technical_query)
        
        self.assertGreater(result["technical_terms_count"], 5)
        self.assertGreater(result["complexity_score"], 0.3)


class TestSentimentAnalysisUnit(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment_detection(self):
        positive_queries = [
            "Thank you so much for your excellent service!",
            "I'm really happy with your product, it works great!",
            "Amazing support team, very helpful and friendly!"
        ]
        
        for query in positive_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_sentiment(query)
                self.assertTrue(result["analysis_successful"])
                self.assertGreater(result["sentiment_score"], 0.1)
                self.assertFalse(result["escalation_required"])
                self.assertEqual(self.analyzer.get_sentiment_label(result["sentiment_score"]), "positive")

    def test_negative_sentiment_detection(self):
        negative_queries = [
            "This is absolutely terrible! Your service has been down for hours!",
            "I'm extremely frustrated with the lack of support. This is unacceptable!",
            "Your API is completely broken and your documentation is useless!"
        ]
        
        for query in negative_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_sentiment(query)
                self.assertTrue(result["analysis_successful"])
                self.assertLess(result["sentiment_score"], -0.1)
                self.assertEqual(self.analyzer.get_sentiment_label(result["sentiment_score"]), "negative")

    def test_escalation_threshold(self):
        highly_negative_queries = [
            "I'm furious! This is the worst experience I've ever had!",
            "Absolutely disgusted with your terrible service!"
        ]
        
        for query in highly_negative_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_sentiment(query)
                self.assertLess(result["sentiment_score"], -0.5)
                self.assertTrue(result["escalation_required"])

    def test_neutral_sentiment_detection(self):
        neutral_queries = [
            "Can you help me with my account?",
            "I need information about your pricing.",
            "How do I configure this setting?"
        ]
        
        for query in neutral_queries:
            with self.subTest(query=query):
                result = self.analyzer.analyze_sentiment(query)
                self.assertTrue(result["analysis_successful"])
                self.assertGreaterEqual(result["sentiment_score"], -0.1)
                self.assertLessEqual(result["sentiment_score"], 0.1)
                self.assertEqual(self.analyzer.get_sentiment_label(result["sentiment_score"]), "neutral")

    def test_empty_query_handling(self):
        result = self.analyzer.analyze_sentiment("")
        self.assertEqual(result["sentiment_score"], 0.0)
        self.assertFalse(result["analysis_successful"])

    def test_sentiment_emoji_mapping(self):
        test_cases = [
            (0.5, "😊"),
            (0.0, "😐"),
            (-0.5, "😠")
        ]
        
        for score, expected_emoji in test_cases:
            with self.subTest(score=score):
                emoji = self.analyzer.get_sentiment_emoji(score)
                self.assertEqual(emoji, expected_emoji)


class TestEscalationLogicUnit(unittest.TestCase):
    def setUp(self):
        self.manager = EscalationManager()

    def test_complexity_escalation_trigger(self):
        should_escalate, reasons = self.manager.should_escalate(0.9, 0.0)
        self.assertTrue(should_escalate)
        self.assertIn("complexity", reasons)

    def test_sentiment_escalation_trigger(self):
        should_escalate, reasons = self.manager.should_escalate(0.3, -0.7)
        self.assertTrue(should_escalate)
        self.assertIn("sentiment", reasons)

    def test_combined_escalation_trigger(self):
        should_escalate, reasons = self.manager.should_escalate(0.9, -0.7)
        self.assertTrue(should_escalate)
        self.assertIn("complexity", reasons)
        self.assertIn("sentiment", reasons)

    def test_no_escalation_needed(self):
        should_escalate, reasons = self.manager.should_escalate(0.3, 0.2)
        self.assertFalse(should_escalate)
        self.assertEqual(len(reasons), 0)

    def test_escalation_summary_generation(self):
        messages = [
            ConversationMessage(role="user", content="I'm having trouble with API integration"),
            ConversationMessage(role="assistant", content="I can help you with that", model_used="llama-3.3-70b-versatile"),
            ConversationMessage(role="user", content="This is extremely frustrating and not working at all!")
        ]
        
        summary = self.manager.generate_escalation_summary(messages, ["complexity", "sentiment"])
        
        self.assertIn("ESCALATION TRIGGERED", summary)
        self.assertIn("COMPLEXITY, SENTIMENT", summary)
        self.assertIn("Total messages: 3", summary)
        self.assertIn("extremely frustrating", summary)

    def test_escalation_ticket_creation(self):
        messages = [
            ConversationMessage(role="user", content="This is a complex technical issue", complexity_score=0.9, sentiment_score=-0.6)
        ]
        
        ticket = self.manager.create_escalation_ticket("test_customer", messages, ["complexity", "sentiment"], 0.9)
        
        self.assertIsInstance(ticket, EscalationTicket)
        self.assertEqual(ticket.customer_id, "test_customer")
        self.assertEqual(ticket.reason, "complexity")
        self.assertEqual(ticket.priority, "critical")
        self.assertEqual(ticket.escalation_score, 0.9)

    def test_priority_calculation(self):
        test_cases = [
            (0.95, ["sentiment"], "critical"),
            (0.85, ["complexity"], "high"),
            (0.7, ["complexity"], "medium"),
            (0.5, ["complexity"], "low")
        ]
        
        for score, reasons, expected_priority in test_cases:
            with self.subTest(score=score, reasons=reasons):
                priority = self.manager._calculate_priority(score, reasons)
                self.assertEqual(priority, expected_priority)
    