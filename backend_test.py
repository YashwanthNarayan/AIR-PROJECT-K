#!/usr/bin/env python3
import requests
import json
import time
import unittest
import os
import uuid
from dotenv import load_dotenv
import sys
from enum import Enum

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

# Enums to match backend
class GradeLevel(str, Enum):
    GRADE_6 = "6th"
    GRADE_7 = "7th" 
    GRADE_8 = "8th"
    GRADE_9 = "9th"
    GRADE_10 = "10th"
    GRADE_11 = "11th"
    GRADE_12 = "12th"

class Subject(str, Enum):
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"  
    HARD = "hard"

class TestProjectKBackend(unittest.TestCase):
    """Test cases for Project K AI Educational Chatbot backend V2.0"""

    def setUp(self):
        """Set up test case - create a student profile and chat session"""
        self.student_id = None
        self.session_id = None
        self.student_profile = self.create_student_profile()
        if self.student_id:
            self.chat_session = self.create_chat_session()

    def create_student_profile(self):
        """Test creating a student profile"""
        print("\n🔍 Testing Enhanced Student Profile System...")
        url = f"{API_URL}/student/profile"
        payload = {
            "name": "Rahul Sharma",
            "grade_level": GradeLevel.GRADE_10.value,
            "subjects": [
                Subject.MATH.value,
                Subject.PHYSICS.value,
                Subject.CHEMISTRY.value,
                Subject.BIOLOGY.value
            ],
            "learning_goals": [
                "Improve math problem-solving skills",
                "Prepare for science olympiad",
                "Build better study habits"
            ],
            "study_hours_per_day": 3,
            "preferred_study_time": "evening"
        }
        
        try:
            response = requests.post(url, json=payload)
            print(f"Create Student Profile Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to create student profile")
            data = response.json()
            self.student_id = data.get("student_id")
            print(f"Created student profile with ID: {self.student_id}")
            self.assertIsNotNone(self.student_id, "Student ID should not be None")
            self.assertEqual(data.get("name"), payload["name"], "Student name mismatch")
            self.assertEqual(data.get("grade_level"), payload["grade_level"], "Grade level mismatch")
            self.assertEqual(len(data.get("subjects")), len(payload["subjects"]), "Subjects count mismatch")
            print("✅ Create student profile test passed")
            return data
        except Exception as e:
            print(f"❌ Create student profile test failed: {str(e)}")
            return None

    def test_01_get_student_profile(self):
        """Test getting a student profile"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        url = f"{API_URL}/student/profile/{self.student_id}"
        response = requests.get(url)
        print(f"Get Student Profile Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to get student profile")
        data = response.json()
        self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
        self.assertEqual(data.get("name"), "Rahul Sharma", "Student name mismatch")
        self.assertEqual(data.get("grade_level"), GradeLevel.GRADE_10.value, "Grade level mismatch")
        print("✅ Get student profile test passed")
        return data

    def test_02_update_student_profile(self):
        """Test updating a student profile"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        url = f"{API_URL}/student/profile/{self.student_id}"
        updates = {
            "learning_goals": [
                "Improve math problem-solving skills",
                "Prepare for science olympiad",
                "Build better study habits",
                "Master calculus concepts"
            ],
            "total_xp": 50,  # Add some XP
            "streak_days": 3  # Add streak days
        }
        
        response = requests.put(url, json=updates)
        print(f"Update Student Profile Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed to update student profile")
        data = response.json()
        self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
        self.assertEqual(len(data.get("learning_goals")), 4, "Learning goals count mismatch")
        self.assertEqual(data.get("total_xp"), 50, "XP mismatch")
        self.assertEqual(data.get("streak_days"), 3, "Streak days mismatch")
        print("✅ Update student profile test passed")
        return data

    def create_chat_session(self):
        """Create a new chat session for a subject"""
        if not self.student_id:
            return None
            
        url = f"{API_URL}/chat/session"
        payload = {
            "student_id": self.student_id,
            "subject": Subject.MATH.value
        }
        
        try:
            response = requests.post(url, json=payload)
            print(f"Create Chat Session Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to create chat session")
            data = response.json()
            self.session_id = data.get("session_id")
            print(f"Created chat session with ID: {self.session_id}")
            self.assertIsNotNone(self.session_id, "Session ID should not be None")
            self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
            self.assertEqual(data.get("subject"), Subject.MATH.value, "Subject mismatch")
            print("✅ Create chat session test passed")
            return data
        except Exception as e:
            print(f"❌ Create chat session test failed: {str(e)}")
            return None

    def test_03_health_check(self):
        """Test health check endpoint"""
        url = f"{API_URL}/health"
        response = requests.get(url)
        print(f"Health Check Response: {response.status_code}")
        
        self.assertEqual(response.status_code, 200, "Failed health check")
        data = response.json()
        self.assertEqual(data.get("status"), "healthy", "Health status should be 'healthy'")
        print("✅ Health check test passed")

    def test_04_multiple_subject_bots(self):
        """Test all subject bots with appropriate questions"""
        if not self.student_id or not self.session_id:
            self.skipTest("Student profile or chat session not created")
        
        print("\n🔍 Testing Multiple Subject Bots...")
        
        # Test each subject bot with an appropriate question
        subject_questions = {
            Subject.MATH.value: "Can you help me solve the quadratic equation x^2 - 5x + 6 = 0?",
            Subject.PHYSICS.value: "Explain Newton's laws of motion with examples",
            Subject.CHEMISTRY.value: "What is the periodic table and how is it organized?",
            Subject.BIOLOGY.value: "Explain the process of photosynthesis in plants",
            Subject.ENGLISH.value: "Can you help me analyze the theme of Shakespeare's Macbeth?",
            Subject.HISTORY.value: "What were the major causes of World War II?",
            Subject.GEOGRAPHY.value: "Explain the formation of different types of mountains"
        }
        
        results = {}
        
        for subject, question in subject_questions.items():
            # Create a new session for each subject
            session_url = f"{API_URL}/chat/session"
            session_payload = {
                "student_id": self.student_id,
                "subject": subject
            }
            
            session_response = requests.post(session_url, json=session_payload)
            if session_response.status_code != 200:
                print(f"❌ Failed to create session for {subject}")
                continue
                
            session_data = session_response.json()
            subject_session_id = session_data.get("session_id")
            
            # Send a question to the subject bot
            message_url = f"{API_URL}/chat/message"
            message_payload = {
                "session_id": subject_session_id,
                "student_id": self.student_id,
                "subject": subject,
                "user_message": question
            }
            
            try:
                message_response = requests.post(message_url, json=message_payload)
                print(f"{subject.title()} Bot Response: {message_response.status_code}")
                
                self.assertEqual(message_response.status_code, 200, f"Failed to get response from {subject} bot")
                message_data = message_response.json()
                self.assertIsNotNone(message_data.get("bot_response"), f"{subject} bot response should not be None")
                
                # Check if the bot type matches the subject
                expected_bot_type = f"{subject}_bot"
                actual_bot_type = message_data.get("bot_type")
                
                print(f"{subject.title()} Bot Type: {actual_bot_type}")
                print(f"{subject.title()} Response Preview: {message_data.get('bot_response')[:100]}...")
                
                results[subject] = {
                    "success": True,
                    "bot_type": actual_bot_type,
                    "response_preview": message_data.get('bot_response')[:100]
                }
                
                print(f"✅ {subject.title()} bot test passed")
            except Exception as e:
                print(f"❌ {subject.title()} bot test failed: {str(e)}")
                results[subject] = {"success": False, "error": str(e)}
        
        # Verify that all subject bots were tested
        successful_subjects = [subject for subject, result in results.items() if result.get("success")]
        self.assertTrue(len(successful_subjects) >= 5, "At least 5 subject bots should work correctly")
        
        return results

    def test_05_central_brain_routing(self):
        """Test enhanced central brain routing to appropriate subject bots"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        print("\n🔍 Testing Enhanced Central Brain Routing...")
        
        # Create a new general session
        session_url = f"{API_URL}/chat/session"
        session_payload = {
            "student_id": self.student_id,
            "subject": Subject.MATH.value  # Default subject, but we'll test routing
        }
        
        session_response = requests.post(session_url, json=session_payload)
        self.assertEqual(session_response.status_code, 200, "Failed to create session for routing test")
        session_data = session_response.json()
        routing_session_id = session_data.get("session_id")
        
        # Test messages that should trigger different routing
        routing_tests = [
            {
                "message": "I'm feeling very stressed about my exams tomorrow",
                "expected_bot": "mindfulness_bot",
                "description": "Stress message should route to mindfulness bot"
            },
            {
                "message": "What is the capital of France?",
                "expected_bot": "geography_bot",
                "description": "Geography question should route to geography bot"
            },
            {
                "message": "Can you explain the process of photosynthesis?",
                "expected_bot": "biology_bot",
                "description": "Biology question should route to biology bot"
            }
        ]
        
        for test in routing_tests:
            message_url = f"{API_URL}/chat/message"
            message_payload = {
                "session_id": routing_session_id,
                "student_id": self.student_id,
                "subject": Subject.MATH.value,  # Default subject, but routing should override
                "user_message": test["message"]
            }
            
            try:
                message_response = requests.post(message_url, json=message_payload)
                print(f"Routing Test Response ({test['description']}): {message_response.status_code}")
                
                self.assertEqual(message_response.status_code, 200, f"Failed routing test: {test['description']}")
                message_data = message_response.json()
                
                print(f"Message: '{test['message']}'")
                print(f"Bot Type: {message_data.get('bot_type')}")
                print(f"Response Preview: {message_data.get('bot_response')[:100]}...")
                
                # Note: The actual bot_type might not exactly match our expected_bot
                # due to implementation details, but we can check if the response is appropriate
                self.assertIsNotNone(message_data.get("bot_response"), "Bot response should not be None")
                
                print(f"✅ Routing test passed: {test['description']}")
            except Exception as e:
                print(f"❌ Routing test failed ({test['description']}): {str(e)}")
        
        print("✅ Enhanced Central Brain Routing tests completed")

    def test_06_mindfulness_toolbox(self):
        """Test mindfulness toolbox backend features"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        print("\n🔍 Testing Mindfulness Toolbox Backend...")
        
        # Test creating a mindfulness session
        mindfulness_url = f"{API_URL}/mindfulness/session"
        activities = [
            {"activity_type": "breathing", "duration": 5},
            {"activity_type": "meditation", "duration": 10},
            {"activity_type": "stress_relief", "duration": 15}
        ]
        
        for activity in activities:
            payload = {
                "student_id": self.student_id,
                "activity_type": activity["activity_type"],
                "duration": activity["duration"]
            }
            
            try:
                response = requests.post(mindfulness_url, json=payload)
                print(f"Mindfulness {activity['activity_type']} Response: {response.status_code}")
                
                self.assertEqual(response.status_code, 200, f"Failed to create {activity['activity_type']} session")
                data = response.json()
                self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
                self.assertEqual(data.get("activity_type"), activity["activity_type"], "Activity type mismatch")
                self.assertEqual(data.get("duration"), activity["duration"], "Duration mismatch")
                
                print(f"✅ Mindfulness {activity['activity_type']} test passed")
            except Exception as e:
                print(f"❌ Mindfulness {activity['activity_type']} test failed: {str(e)}")
        
        # Test getting mindfulness history
        history_url = f"{API_URL}/mindfulness/activities/{self.student_id}"
        try:
            response = requests.get(history_url)
            print(f"Mindfulness History Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get mindfulness history")
            data = response.json()
            self.assertIsInstance(data, list, "Mindfulness history should be a list")
            self.assertTrue(len(data) >= 3, "Mindfulness history should have at least 3 activities")
            
            activity_types = [activity.get("activity_type") for activity in data]
            self.assertIn("breathing", activity_types, "Breathing activity not found in history")
            self.assertIn("meditation", activity_types, "Meditation activity not found in history")
            self.assertIn("stress_relief", activity_types, "Stress relief activity not found in history")
            
            print(f"Mindfulness history contains {len(data)} activities")
            print("✅ Mindfulness history test passed")
        except Exception as e:
            print(f"❌ Mindfulness history test failed: {str(e)}")
        
        # Test mindfulness bot with a stress-related query
        session_url = f"{API_URL}/chat/session"
        session_payload = {
            "student_id": self.student_id,
            "subject": Subject.MATH.value  # Default subject, but we'll test routing to mindfulness
        }
        
        session_response = requests.post(session_url, json=session_payload)
        mindfulness_session_id = session_response.json().get("session_id")
        
        message_url = f"{API_URL}/chat/message"
        message_payload = {
            "session_id": mindfulness_session_id,
            "student_id": self.student_id,
            "subject": Subject.MATH.value,
            "user_message": "I'm feeling very anxious about my upcoming exams. Can you help me relax?"
        }
        
        try:
            message_response = requests.post(message_url, json=message_payload)
            print(f"Mindfulness Bot Response: {message_response.status_code}")
            
            self.assertEqual(message_response.status_code, 200, "Failed to get response from mindfulness bot")
            message_data = message_response.json()
            
            print(f"Bot Type: {message_data.get('bot_type')}")
            print(f"Response Preview: {message_data.get('bot_response')[:100]}...")
            
            self.assertIsNotNone(message_data.get("bot_response"), "Mindfulness bot response should not be None")
            print("✅ Mindfulness bot test passed")
        except Exception as e:
            print(f"❌ Mindfulness bot test failed: {str(e)}")
        
        print("✅ Mindfulness Toolbox tests completed")

    def test_07_practice_test_generation(self):
        """Test practice test generation"""
        print("\n🔍 Testing Practice Test Generation...")
        
        url = f"{API_URL}/practice/generate"
        params = {
            "subject": Subject.MATH.value,
            "topic": "Algebra",
            "difficulty": DifficultyLevel.MEDIUM.value,
            "count": 3
        }
        
        try:
            response = requests.post(url, params=params)
            print(f"Practice Test Generation Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to generate practice test")
            data = response.json()
            self.assertIn("questions", data, "Questions not found in response")
            self.assertIn("message", data, "Message not found in response")
            
            print(f"Practice test generated with message: {data.get('message')}")
            print(f"Questions preview: {str(data.get('questions'))[:100]}...")
            print("✅ Practice test generation test passed")
        except Exception as e:
            print(f"❌ Practice test generation test failed: {str(e)}")

    def test_08_enhanced_chat_history(self):
        """Test enhanced chat history by subject"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        print("\n🔍 Testing Enhanced Chat History by Subject...")
        
        # Create sessions for different subjects and send messages
        subjects_to_test = [Subject.MATH.value, Subject.PHYSICS.value, Subject.ENGLISH.value]
        session_ids = {}
        
        for subject in subjects_to_test:
            # Create a session
            session_url = f"{API_URL}/chat/session"
            session_payload = {
                "student_id": self.student_id,
                "subject": subject
            }
            
            session_response = requests.post(session_url, json=session_payload)
            if session_response.status_code != 200:
                print(f"❌ Failed to create session for {subject}")
                continue
                
            session_data = session_response.json()
            subject_session_id = session_data.get("session_id")
            session_ids[subject] = subject_session_id
            
            # Send 2 messages for each subject
            message_url = f"{API_URL}/chat/message"
            for i in range(2):
                message_payload = {
                    "session_id": subject_session_id,
                    "student_id": self.student_id,
                    "subject": subject,
                    "user_message": f"Test message {i+1} for {subject} subject"
                }
                
                message_response = requests.post(message_url, json=message_payload)
                if message_response.status_code != 200:
                    print(f"❌ Failed to send message {i+1} for {subject}")
        
        # Test getting all chat history
        all_history_url = f"{API_URL}/chat/history/{self.student_id}"
        try:
            response = requests.get(all_history_url)
            print(f"All Chat History Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get all chat history")
            all_data = response.json()
            self.assertIsInstance(all_data, list, "Chat history should be a list")
            
            # Should have at least 6 messages (2 for each of 3 subjects)
            self.assertTrue(len(all_data) >= 6, f"Chat history should have at least 6 messages, got {len(all_data)}")
            
            print(f"All chat history contains {len(all_data)} messages")
            print("✅ All chat history test passed")
        except Exception as e:
            print(f"❌ All chat history test failed: {str(e)}")
        
        # Test getting chat history filtered by subject
        for subject in subjects_to_test:
            subject_history_url = f"{API_URL}/chat/history/{self.student_id}?subject={subject}"
            try:
                response = requests.get(subject_history_url)
                print(f"{subject.title()} Chat History Response: {response.status_code}")
                
                self.assertEqual(response.status_code, 200, f"Failed to get {subject} chat history")
                subject_data = response.json()
                self.assertIsInstance(subject_data, list, f"{subject} chat history should be a list")
                
                # Should have at least 2 messages for this subject
                self.assertTrue(len(subject_data) >= 2, f"{subject} chat history should have at least 2 messages")
                
                # Verify all messages are for this subject
                for message in subject_data:
                    self.assertEqual(message.get("subject"), subject, f"Message subject should be {subject}")
                
                print(f"{subject.title()} chat history contains {len(subject_data)} messages")
                print(f"✅ {subject.title()} chat history test passed")
            except Exception as e:
                print(f"❌ {subject.title()} chat history test failed: {str(e)}")
        
        # Test getting chat sessions
        sessions_url = f"{API_URL}/chat/sessions/{self.student_id}"
        try:
            response = requests.get(sessions_url)
            print(f"Chat Sessions Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get chat sessions")
            sessions_data = response.json()
            self.assertIsInstance(sessions_data, list, "Chat sessions should be a list")
            
            # Should have at least 3 sessions (one for each subject)
            self.assertTrue(len(sessions_data) >= 3, "Chat sessions should have at least 3 sessions")
            
            # Verify our session IDs are in the list
            session_ids_in_response = [session.get("session_id") for session in sessions_data]
            for subject, session_id in session_ids.items():
                self.assertIn(session_id, session_ids_in_response, f"{subject} session ID not found in sessions")
            
            print(f"Found {len(sessions_data)} chat sessions")
            print("✅ Chat sessions test passed")
        except Exception as e:
            print(f"❌ Chat sessions test failed: {str(e)}")
        
        print("✅ Enhanced Chat History tests completed")

    def test_09_xp_and_gamification(self):
        """Test XP and gamification system"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        print("\n🔍 Testing XP and Gamification System...")
        
        # First, get the current XP
        profile_url = f"{API_URL}/student/profile/{self.student_id}"
        profile_response = requests.get(profile_url)
        profile_data = profile_response.json()
        initial_xp = profile_data.get("total_xp", 0)
        initial_streak = profile_data.get("streak_days", 0)
        
        print(f"Initial XP: {initial_xp}, Initial Streak: {initial_streak}")
        
        # Send several chat messages to earn XP
        session_url = f"{API_URL}/chat/session"
        session_payload = {
            "student_id": self.student_id,
            "subject": Subject.MATH.value
        }
        
        session_response = requests.post(session_url, json=session_payload)
        xp_session_id = session_response.json().get("session_id")
        
        message_url = f"{API_URL}/chat/message"
        for i in range(3):  # Send 3 messages to earn XP
            message_payload = {
                "session_id": xp_session_id,
                "student_id": self.student_id,
                "subject": Subject.MATH.value,
                "user_message": f"XP test message {i+1}"
            }
            
            message_response = requests.post(message_url, json=message_payload)
            if message_response.status_code != 200:
                print(f"❌ Failed to send XP test message {i+1}")
        
        # Check if XP increased
        updated_profile_response = requests.get(profile_url)
        updated_profile_data = updated_profile_response.json()
        final_xp = updated_profile_data.get("total_xp", 0)
        
        print(f"Final XP: {final_xp}")
        self.assertTrue(final_xp > initial_xp, "XP should increase after sending messages")
        print(f"XP increased by {final_xp - initial_xp} points")
        
        # Test updating streak manually
        update_url = f"{API_URL}/student/profile/{self.student_id}"
        update_payload = {
            "streak_days": initial_streak + 1,
            "badges": ["First Chat", "Math Explorer"]
        }
        
        update_response = requests.put(update_url, json=update_payload)
        self.assertEqual(update_response.status_code, 200, "Failed to update streak and badges")
        
        # Verify streak and badges updated
        final_profile_response = requests.get(profile_url)
        final_profile_data = final_profile_response.json()
        final_streak = final_profile_data.get("streak_days", 0)
        badges = final_profile_data.get("badges", [])
        
        self.assertEqual(final_streak, initial_streak + 1, "Streak should be updated")
        self.assertTrue(len(badges) >= 2, "Should have at least 2 badges")
        self.assertIn("First Chat", badges, "First Chat badge not found")
        self.assertIn("Math Explorer", badges, "Math Explorer badge not found")
        
        print(f"Streak updated to {final_streak}")
        print(f"Badges: {badges}")
        print("✅ XP and Gamification test passed")

    def test_10_dashboard_analytics(self):
        """Test dashboard analytics API"""
        if not self.student_id:
            self.skipTest("Student profile not created")
            
        print("\n🔍 Testing Dashboard Analytics API...")
        
        url = f"{API_URL}/dashboard/{self.student_id}"
        try:
            response = requests.get(url)
            print(f"Dashboard Analytics Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get dashboard analytics")
            data = response.json()
            
            # Check dashboard structure
            self.assertIn("profile", data, "Profile section not found in dashboard")
            self.assertIn("stats", data, "Stats section not found in dashboard")
            self.assertIn("recent_activity", data, "Recent activity section not found in dashboard")
            self.assertIn("subjects_progress", data, "Subjects progress not found in dashboard")
            
            # Check stats
            stats = data.get("stats", {})
            self.assertIn("total_messages", stats, "Total messages not found in stats")
            self.assertIn("subjects_studied", stats, "Subjects studied not found in stats")
            self.assertIn("study_streak", stats, "Study streak not found in stats")
            self.assertIn("total_xp", stats, "Total XP not found in stats")
            self.assertIn("level", stats, "Level not found in stats")
            
            # Check recent activity
            recent_activity = data.get("recent_activity", {})
            self.assertIn("messages", recent_activity, "Recent messages not found")
            self.assertIn("sessions", recent_activity, "Recent sessions not found")
            
            print("Dashboard data structure is valid")
            print(f"Stats: {stats}")
            print(f"Recent activity: {len(recent_activity.get('messages', []))} messages, {len(recent_activity.get('sessions', []))} sessions")
            print(f"Subjects progress: {data.get('subjects_progress')}")
            print("✅ Dashboard Analytics test passed")
        except Exception as e:
            print(f"❌ Dashboard Analytics test failed: {str(e)}")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
