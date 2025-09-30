import unittest
import requests
import json

class TestUserJourney(unittest.TestCase):

    BASE_URL = "http://localhost:8080"

    def test_full_user_journey(self):
        # 1. Start a new session
        response = requests.post(f"{self.BASE_URL}/api/session")
        self.assertEqual(response.status_code, 200)
        session_data = response.json()
        self.assertIn("session_id", session_data)
        session_id = session_data["session_id"]

        # 2. Send a simple query
        simple_query = {
            "session_id": session_id,
            "query": "What is your name?"
        }
        response = requests.post(f"{self.BASE_URL}/api/query", json=simple_query)
        self.assertEqual(response.status_code, 200)
        query_response = response.json()
        self.assertIn("response", query_response)
        self.assertIn("model_used", query_response)

        # 3. Send a complex query that triggers an escalation
        complex_query = {
            "session_id": session_id,
            "query": "I need comprehensive assistance with migrating our entire microservices architecture from monolithic design to containerized Kubernetes deployment with custom service mesh configuration, advanced monitoring, distributed tracing, automated CI/CD pipelines, multi-region disaster recovery, and performance optimization across multiple database systems including PostgreSQL, MongoDB, and Redis clusters."
        }
        response = requests.post(f"{self.BASE_URL}/api/query", json=complex_query)
        self.assertEqual(response.status_code, 200)
        escalation_response = response.json()
        self.assertIn("escalation_ticket", escalation_response)
        self.assertIsNotNone(escalation_response["escalation_ticket"])

        # 4. Verify the conversation history and escalation status
        response = requests.get(f"{self.BASE_URL}/api/session/{session_id}")
        self.assertEqual(response.status_code, 200)
        session_history = response.json()
        self.assertEqual(len(session_history["conversation_history"]), 4) # User, Bot, User, Bot
        self.assertIsNotNone(session_history["escalation_ticket"])

if __name__ == "__main__":
    unittest.main()
