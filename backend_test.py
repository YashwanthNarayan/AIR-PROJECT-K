#!/usr/bin/env python3
import requests
import json
import time
import unittest
import os
from dotenv import load_dotenv
import sys

# Load environment variables from frontend/.env to get the backend URL
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Add /api prefix to the backend URL
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

class TestProjectKBackend(unittest.TestCase):
    """Test cases for Project K AI Educational Chatbot backend"""

    def setUp(self):
        """Set up test case - create a new chat session"""
        self.session_id = None
        self.create_session()

    def create_session(self):
        """Create a new chat session"""
        url = f"{API_URL}/chat/session"
        payload = {"student_name": "Test Student"}
        
        response = requests.post(url, json=payload)
        print(f"Create Session Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to create chat session")
        data = response.json()
        self.session_id = data.get("session_id")
        print(f"Created session with ID: {self.session_id}")
        self.assertIsNotNone(self.session_id, "Session ID should not be None")
        return data

    def test_01_get_session(self):
        """Test getting a chat session"""
        url = f"{API_URL}/chat/session/{self.session_id}"
        response = requests.get(url)
        print(f"Get Session Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to get chat session")
        data = response.json()
        self.assertEqual(data.get("session_id"), self.session_id, "Session ID mismatch")
        self.assertEqual(data.get("student_name"), "Test Student", "Student name mismatch")
        print("✅ Get session test passed")

    def test_02_welcome_message(self):
        """Test welcome message API"""
        url = f"{API_URL}/welcome/{self.session_id}"
        response = requests.get(url)
        print(f"Welcome Message Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to get welcome message")
        data = response.json()
        self.assertIn("message", data, "Welcome message not found")
        self.assertIn("quick_actions", data, "Quick actions not found")
        self.assertTrue(len(data["quick_actions"]) > 0, "Quick actions should not be empty")
        print("✅ Welcome message test passed")

    def test_03_health_check(self):
        """Test health check endpoint"""
        url = f"{API_URL}/health"
        response = requests.get(url)
        print(f"Health Check Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed health check")
        data = response.json()
        self.assertEqual(data.get("status"), "healthy", "Health status should be 'healthy'")
        print("✅ Health check test passed")

    def test_04_send_math_question(self):
        """Test sending a math question and verify it routes to Math Bot"""
        url = f"{API_URL}/chat/message"
        payload = {
            "session_id": self.session_id,
            "user_message": "I need help with solving 2x + 5 = 15"
        }
        
        response = requests.post(url, json=payload)
        print(f"Send Math Question Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to send math question")
        data = response.json()
        self.assertEqual(data.get("session_id"), self.session_id, "Session ID mismatch")
        self.assertEqual(data.get("user_message"), payload["user_message"], "User message mismatch")
        self.assertIsNotNone(data.get("bot_response"), "Bot response should not be None")
        self.assertEqual(data.get("bot_type"), "math_bot", "Bot type should be 'math_bot'")
        print(f"Math Bot Response: {data.get('bot_response')[:100]}...")
        print("✅ Math question routing test passed")

    def test_05_send_general_greeting(self):
        """Test sending a general greeting and verify it stays with Central Brain"""
        url = f"{API_URL}/chat/message"
        payload = {
            "session_id": self.session_id,
            "user_message": "Hello, I'm struggling with my homework"
        }
        
        response = requests.post(url, json=payload)
        print(f"Send General Greeting Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to send general greeting")
        data = response.json()
        self.assertEqual(data.get("session_id"), self.session_id, "Session ID mismatch")
        self.assertEqual(data.get("user_message"), payload["user_message"], "User message mismatch")
        self.assertIsNotNone(data.get("bot_response"), "Bot response should not be None")
        self.assertEqual(data.get("bot_type"), "central_brain", "Bot type should be 'central_brain'")
        print(f"Central Brain Response: {data.get('bot_response')[:100]}...")
        print("✅ General greeting routing test passed")

    def test_06_get_chat_history(self):
        """Test getting chat history to verify message persistence"""
        # First, send a couple of messages to ensure there's history
        self.test_04_send_math_question()
        self.test_05_send_general_greeting()
        
        # Now get the chat history
        url = f"{API_URL}/chat/history/{self.session_id}"
        response = requests.get(url)
        print(f"Get Chat History Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to get chat history")
        data = response.json()
        self.assertIsInstance(data, list, "Chat history should be a list")
        self.assertTrue(len(data) >= 2, "Chat history should have at least 2 messages")
        
        # Verify the messages in the history
        messages = [msg.get("user_message") for msg in data]
        self.assertIn("I need help with solving 2x + 5 = 15", messages, "Math question not found in history")
        self.assertIn("Hello, I'm struggling with my homework", messages, "General greeting not found in history")
        
        print(f"Chat history contains {len(data)} messages")
        print("✅ Chat history test passed")

    def test_07_get_all_sessions(self):
        """Test getting all chat sessions"""
        url = f"{API_URL}/chat/sessions"
        response = requests.get(url)
        print(f"Get All Sessions Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to get all sessions")
        data = response.json()
        self.assertIsInstance(data, list, "Sessions should be a list")
        self.assertTrue(len(data) > 0, "There should be at least one session")
        
        # Verify our session is in the list
        session_ids = [session.get("session_id") for session in data]
        self.assertIn(self.session_id, session_ids, "Our session ID not found in all sessions")
        
        print(f"Found {len(data)} sessions")
        print("✅ Get all sessions test passed")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
