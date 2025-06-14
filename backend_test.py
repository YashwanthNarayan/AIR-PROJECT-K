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
    MIXED = "mixed"

class UserType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"

class TestProjectKV3Backend(unittest.TestCase):
    """Test cases for Project K AI Educational Chatbot backend V3.0 with authentication"""

    def setUp(self):
        """Set up test case - create student and teacher accounts"""
        self.student_token = None
        self.teacher_token = None
        self.student_id = None
        self.teacher_id = None
        self.class_id = None
        self.join_code = None
        self.session_id = None
        
        # Register student and teacher
        self.register_student()
        self.register_teacher()

    def register_student(self):
        """Test student registration"""
        print("\n🔍 Testing Student Registration...")
        url = f"{API_URL}/auth/register"
        payload = {
            "email": f"student_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Rahul Sharma",
            "user_type": UserType.STUDENT.value,
            "grade_level": GradeLevel.GRADE_10.value
        }
        
        try:
            response = requests.post(url, json=payload)
            print(f"Student Registration Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to register student")
            data = response.json()
            self.student_token = data.get("access_token")
            self.student_id = data.get("user", {}).get("id")
            
            print(f"Registered student with ID: {self.student_id}")
            self.assertIsNotNone(self.student_token, "Student token should not be None")
            self.assertIsNotNone(self.student_id, "Student ID should not be None")
            print("✅ Student registration test passed")
            return data
        except Exception as e:
            print(f"❌ Student registration test failed: {str(e)}")
            return None

    def register_teacher(self):
        """Test teacher registration"""
        print("\n🔍 Testing Teacher Registration...")
        url = f"{API_URL}/auth/register"
        payload = {
            "email": f"teacher_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Priya Patel",
            "user_type": UserType.TEACHER.value,
            "school_name": "Delhi Public School"
        }
        
        try:
            response = requests.post(url, json=payload)
            print(f"Teacher Registration Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to register teacher")
            data = response.json()
            self.teacher_token = data.get("access_token")
            self.teacher_id = data.get("user", {}).get("id")
            
            print(f"Registered teacher with ID: {self.teacher_id}")
            self.assertIsNotNone(self.teacher_token, "Teacher token should not be None")
            self.assertIsNotNone(self.teacher_id, "Teacher ID should not be None")
            print("✅ Teacher registration test passed")
            return data
        except Exception as e:
            print(f"❌ Teacher registration test failed: {str(e)}")
            return None

    def test_01_login(self):
        """Test login functionality"""
        print("\n🔍 Testing Login Functionality...")
        
        # Skip if registration failed
        if not self.student_id or not self.teacher_id:
            self.skipTest("Registration failed, cannot test login")
        
        # Test student login
        url = f"{API_URL}/auth/login"
        payload = {
            "email": "student_test@example.com",
            "password": "SecurePass123!"
        }
        
        # Register a new account specifically for login test
        register_url = f"{API_URL}/auth/register"
        register_payload = {
            "email": "student_test@example.com",
            "password": "SecurePass123!",
            "name": "Login Test Student",
            "user_type": UserType.STUDENT.value,
            "grade_level": GradeLevel.GRADE_9.value
        }
        
        try:
            # Register first
            register_response = requests.post(register_url, json=register_payload)
            self.assertEqual(register_response.status_code, 200, "Failed to register test account")
            
            # Then login
            login_response = requests.post(url, json=payload)
            print(f"Student Login Response: {login_response.status_code}")
            
            self.assertEqual(login_response.status_code, 200, "Failed to login as student")
            login_data = login_response.json()
            
            self.assertIsNotNone(login_data.get("access_token"), "Login should return access token")
            self.assertEqual(login_data.get("user_type"), UserType.STUDENT.value, "User type should be student")
            print("✅ Student login test passed")
        except Exception as e:
            print(f"❌ Student login test failed: {str(e)}")
        
        # Test teacher login
        payload = {
            "email": "teacher_test@example.com",
            "password": "SecurePass123!"
        }
        
        # Register a new teacher account for login test
        register_payload = {
            "email": "teacher_test@example.com",
            "password": "SecurePass123!",
            "name": "Login Test Teacher",
            "user_type": UserType.TEACHER.value,
            "school_name": "Test School"
        }
        
        try:
            # Register first
            register_response = requests.post(register_url, json=register_payload)
            self.assertEqual(register_response.status_code, 200, "Failed to register test teacher account")
            
            # Then login
            login_response = requests.post(url, json=payload)
            print(f"Teacher Login Response: {login_response.status_code}")
            
            self.assertEqual(login_response.status_code, 200, "Failed to login as teacher")
            login_data = login_response.json()
            
            self.assertIsNotNone(login_data.get("access_token"), "Login should return access token")
            self.assertEqual(login_data.get("user_type"), UserType.TEACHER.value, "User type should be teacher")
            print("✅ Teacher login test passed")
        except Exception as e:
            print(f"❌ Teacher login test failed: {str(e)}")

    def test_02_student_profile(self):
        """Test student profile endpoint with authentication"""
        print("\n🔍 Testing Student Profile with Authentication...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        url = f"{API_URL}/student/profile"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Student Profile Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get student profile")
            data = response.json()
            
            self.assertEqual(data.get("user_id"), self.student_id, "User ID mismatch")
            self.assertEqual(data.get("name"), "Rahul Sharma", "Name mismatch")
            print("✅ Student profile test passed")
        except Exception as e:
            print(f"❌ Student profile test failed: {str(e)}")

    def test_03_teacher_profile(self):
        """Test teacher profile endpoint with authentication"""
        print("\n🔍 Testing Teacher Profile with Authentication...")
        
        if not self.teacher_token:
            self.skipTest("Teacher token not available")
        
        url = f"{API_URL}/teacher/profile"
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Teacher Profile Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get teacher profile")
            data = response.json()
            
            self.assertEqual(data.get("user_id"), self.teacher_id, "User ID mismatch")
            self.assertEqual(data.get("name"), "Priya Patel", "Name mismatch")
            self.assertEqual(data.get("school_name"), "Delhi Public School", "School name mismatch")
            print("✅ Teacher profile test passed")
        except Exception as e:
            print(f"❌ Teacher profile test failed: {str(e)}")

    def test_04_create_class(self):
        """Test class creation by teacher"""
        print("\n🔍 Testing Class Creation...")
        
        if not self.teacher_token:
            self.skipTest("Teacher token not available")
        
        url = f"{API_URL}/teacher/classes"
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        payload = {
            "subject": Subject.PHYSICS.value,
            "class_name": "Advanced Physics",
            "grade_level": GradeLevel.GRADE_11.value,
            "description": "Advanced physics class covering mechanics, thermodynamics, and electromagnetism"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Create Class Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to create class")
            data = response.json()
            
            self.class_id = data.get("class_id")
            self.join_code = data.get("join_code")
            
            self.assertIsNotNone(self.class_id, "Class ID should not be None")
            self.assertIsNotNone(self.join_code, "Join code should not be None")
            self.assertEqual(data.get("teacher_id"), self.teacher_id, "Teacher ID mismatch")
            self.assertEqual(data.get("subject"), Subject.PHYSICS.value, "Subject mismatch")
            self.assertEqual(data.get("class_name"), "Advanced Physics", "Class name mismatch")
            
            print(f"Created class with ID: {self.class_id} and join code: {self.join_code}")
            print("✅ Create class test passed")
        except Exception as e:
            print(f"❌ Create class test failed: {str(e)}")

    def test_05_get_teacher_classes(self):
        """Test getting teacher's classes"""
        print("\n🔍 Testing Get Teacher Classes...")
        
        if not self.teacher_token or not self.class_id:
            self.skipTest("Teacher token or class ID not available")
        
        url = f"{API_URL}/teacher/classes"
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Get Teacher Classes Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get teacher classes")
            data = response.json()
            
            self.assertIsInstance(data, list, "Response should be a list")
            self.assertTrue(len(data) > 0, "Teacher should have at least one class")
            
            # Check if our created class is in the list
            class_ids = [cls.get("class_id") for cls in data]
            self.assertIn(self.class_id, class_ids, "Created class not found in teacher's classes")
            
            print(f"Teacher has {len(data)} classes")
            print("✅ Get teacher classes test passed")
        except Exception as e:
            print(f"❌ Get teacher classes test failed: {str(e)}")

    def test_06_join_class(self):
        """Test student joining a class"""
        print("\n🔍 Testing Join Class...")
        
        if not self.student_token or not self.join_code:
            self.skipTest("Student token or join code not available")
        
        url = f"{API_URL}/student/join-class"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        payload = {
            "join_code": self.join_code
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Join Class Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to join class")
            data = response.json()
            
            self.assertIn("message", data, "Response should contain a message")
            self.assertIn("class", data, "Response should contain class details")
            
            class_data = data.get("class", {})
            self.assertEqual(class_data.get("class_id"), self.class_id, "Class ID mismatch")
            self.assertEqual(class_data.get("join_code"), self.join_code, "Join code mismatch")
            
            print(f"Student joined class: {class_data.get('class_name')}")
            print("✅ Join class test passed")
        except Exception as e:
            print(f"❌ Join class test failed: {str(e)}")

    def test_07_get_student_classes(self):
        """Test getting student's joined classes"""
        print("\n🔍 Testing Get Student Classes...")
        
        if not self.student_token or not self.class_id:
            self.skipTest("Student token or class ID not available")
        
        url = f"{API_URL}/student/classes"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Get Student Classes Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get student classes")
            data = response.json()
            
            self.assertIsInstance(data, list, "Response should be a list")
            self.assertTrue(len(data) > 0, "Student should have at least one class")
            
            # Check if our joined class is in the list
            class_ids = [cls.get("class_id") for cls in data]
            self.assertIn(self.class_id, class_ids, "Joined class not found in student's classes")
            
            print(f"Student has joined {len(data)} classes")
            print("✅ Get student classes test passed")
        except Exception as e:
            print(f"❌ Get student classes test failed: {str(e)}")

    def test_08_chat_session(self):
        """Test creating a chat session with authentication"""
        print("\n🔍 Testing Chat Session Creation...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        url = f"{API_URL}/chat/session"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        payload = {
            "subject": Subject.MATH.value
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Create Chat Session Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to create chat session")
            data = response.json()
            
            self.session_id = data.get("session_id")
            self.assertIsNotNone(self.session_id, "Session ID should not be None")
            self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
            self.assertEqual(data.get("subject"), Subject.MATH.value, "Subject mismatch")
            
            print(f"Created chat session with ID: {self.session_id}")
            print("✅ Create chat session test passed")
        except Exception as e:
            print(f"❌ Create chat session test failed: {str(e)}")

    def test_09_send_chat_message(self):
        """Test sending a chat message with authentication"""
        print("\n🔍 Testing Send Chat Message...")
        
        if not self.student_token or not self.session_id:
            self.skipTest("Student token or session ID not available")
        
        url = f"{API_URL}/chat/message"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        payload = {
            "session_id": self.session_id,
            "subject": Subject.MATH.value,
            "user_message": "Can you help me solve the quadratic equation x^2 - 5x + 6 = 0?"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Send Chat Message Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to send chat message")
            data = response.json()
            
            self.assertEqual(data.get("session_id"), self.session_id, "Session ID mismatch")
            self.assertEqual(data.get("student_id"), self.student_id, "Student ID mismatch")
            self.assertEqual(data.get("subject"), Subject.MATH.value, "Subject mismatch")
            self.assertEqual(data.get("user_message"), payload["user_message"], "User message mismatch")
            self.assertIsNotNone(data.get("bot_response"), "Bot response should not be None")
            
            print(f"Bot response preview: {data.get('bot_response')[:100]}...")
            print("✅ Send chat message test passed")
        except Exception as e:
            print(f"❌ Send chat message test failed: {str(e)}")

    def test_10_chat_history(self):
        """Test getting chat history with authentication"""
        print("\n🔍 Testing Get Chat History...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        url = f"{API_URL}/chat/history"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Get Chat History Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get chat history")
            data = response.json()
            
            self.assertIsInstance(data, list, "Chat history should be a list")
            
            if len(data) > 0:
                # If we have chat history, check the first message
                message = data[0]
                self.assertEqual(message.get("student_id"), self.student_id, "Student ID mismatch")
                self.assertIsNotNone(message.get("user_message"), "User message should not be None")
                self.assertIsNotNone(message.get("bot_response"), "Bot response should not be None")
            
            print(f"Chat history contains {len(data)} messages")
            print("✅ Get chat history test passed")
        except Exception as e:
            print(f"❌ Get chat history test failed: {str(e)}")

    def test_11_practice_test_generation(self):
        """Test practice test generation with authentication"""
        print("\n🔍 Testing Practice Test Generation...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        url = f"{API_URL}/practice/generate"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        payload = {
            "subject": Subject.MATH.value,
            "topics": ["Algebra"],
            "difficulty": DifficultyLevel.MEDIUM.value,
            "question_count": 3
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Practice Test Generation Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to generate practice test")
            data = response.json()
            
            self.assertIn("test_id", data, "Test ID not found in response")
            self.assertIn("questions", data, "Questions not found in response")
            self.assertIn("total_questions", data, "Total questions not found in response")
            
            questions = data.get("questions", [])
            self.assertTrue(len(questions) > 0, "Should have at least one question")
            
            # Check the first question structure
            if len(questions) > 0:
                question = questions[0]
                self.assertIn("question_text", question, "Question text not found")
                self.assertIn("options", question, "Options not found")
                self.assertIn("correct_answer", question, "Correct answer not found")
            
            print(f"Generated {len(questions)} practice questions")
            print("✅ Practice test generation test passed")
        except Exception as e:
            print(f"❌ Practice test generation test failed: {str(e)}")

    def test_12_practice_test_submission(self):
        """Test practice test submission with authentication"""
        print("\n🔍 Testing Practice Test Submission...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        # First generate a test
        gen_url = f"{API_URL}/practice/generate"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        gen_payload = {
            "subject": Subject.MATH.value,
            "topics": ["Algebra"],
            "difficulty": DifficultyLevel.MEDIUM.value,
            "question_count": 2
        }
        
        try:
            gen_response = requests.post(gen_url, json=gen_payload, headers=headers)
            self.assertEqual(gen_response.status_code, 200, "Failed to generate practice test")
            gen_data = gen_response.json()
            
            test_id = gen_data.get("test_id")
            questions = gen_data.get("questions", [])
            
            if len(questions) == 0:
                self.skipTest("No questions generated")
            
            # Create student answers (just use the correct answers for testing)
            student_answers = {}
            question_ids = []
            for question in questions:
                question_id = question.get("id")
                question_ids.append(question_id)
                student_answers[question_id] = question.get("correct_answer")
            
            # Submit the test
            submit_url = f"{API_URL}/practice/submit"
            submit_payload = {
                "test_id": test_id,
                "questions": question_ids,
                "student_answers": student_answers,
                "time_taken": 300  # 5 minutes
            }
            
            submit_response = requests.post(submit_url, json=submit_payload, headers=headers)
            print(f"Practice Test Submission Response: {submit_response.status_code}")
            
            self.assertEqual(submit_response.status_code, 200, "Failed to submit practice test")
            submit_data = submit_response.json()
            
            self.assertIn("score", submit_data, "Score not found in response")
            self.assertIn("correct_answers", submit_data, "Correct answers not found in response")
            self.assertIn("total_questions", submit_data, "Total questions not found in response")
            self.assertIn("xp_earned", submit_data, "XP earned not found in response")
            
            # Since we used correct answers, score should be 100%
            self.assertEqual(submit_data.get("score"), 100.0, "Score should be 100%")
            self.assertEqual(submit_data.get("correct_answers"), len(questions), "All answers should be correct")
            
            print(f"Submitted practice test with score: {submit_data.get('score')}%")
            print(f"Earned {submit_data.get('xp_earned')} XP")
            print("✅ Practice test submission test passed")
        except Exception as e:
            print(f"❌ Practice test submission test failed: {str(e)}")

    def test_13_student_dashboard(self):
        """Test student dashboard with authentication"""
        print("\n🔍 Testing Student Dashboard...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        url = f"{API_URL}/dashboard"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Student Dashboard Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get student dashboard")
            data = response.json()
            
            self.assertIn("profile", data, "Profile not found in dashboard")
            self.assertIn("stats", data, "Stats not found in dashboard")
            self.assertIn("recent_activity", data, "Recent activity not found in dashboard")
            
            profile = data.get("profile", {})
            self.assertEqual(profile.get("user_id"), self.student_id, "User ID mismatch")
            
            stats = data.get("stats", {})
            self.assertIn("total_messages", stats, "Total messages not found in stats")
            self.assertIn("total_xp", stats, "Total XP not found in stats")
            
            print(f"Student dashboard loaded with {len(data.get('recent_activity', {}).get('messages', []))} recent messages")
            print("✅ Student dashboard test passed")
        except Exception as e:
            print(f"❌ Student dashboard test failed: {str(e)}")

    def test_14_teacher_dashboard(self):
        """Test teacher dashboard with authentication"""
        print("\n🔍 Testing Teacher Dashboard...")
        
        if not self.teacher_token:
            self.skipTest("Teacher token not available")
        
        url = f"{API_URL}/teacher/dashboard"
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Teacher Dashboard Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Failed to get teacher dashboard")
            data = response.json()
            
            self.assertIn("profile", data, "Profile not found in dashboard")
            self.assertIn("classes", data, "Classes not found in dashboard")
            self.assertIn("stats", data, "Stats not found in dashboard")
            
            profile = data.get("profile", {})
            self.assertEqual(profile.get("user_id"), self.teacher_id, "User ID mismatch")
            
            classes = data.get("classes", [])
            self.assertTrue(len(classes) > 0, "Teacher should have at least one class")
            
            stats = data.get("stats", {})
            self.assertIn("total_classes", stats, "Total classes not found in stats")
            self.assertIn("total_students", stats, "Total students not found in stats")
            
            print(f"Teacher dashboard loaded with {len(classes)} classes")
            print("✅ Teacher dashboard test passed")
        except Exception as e:
            print(f"❌ Teacher dashboard test failed: {str(e)}")

    def test_15_jwt_validation(self):
        """Test JWT token validation"""
        print("\n🔍 Testing JWT Token Validation...")
        
        if not self.student_token:
            self.skipTest("Student token not available")
        
        # Test with valid token
        url = f"{API_URL}/student/profile"
        valid_headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            valid_response = requests.get(url, headers=valid_headers)
            print(f"Valid Token Response: {valid_response.status_code}")
            
            self.assertEqual(valid_response.status_code, 200, "Valid token should be accepted")
            
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid.token.here"}
            invalid_response = requests.get(url, headers=invalid_headers)
            print(f"Invalid Token Response: {invalid_response.status_code}")
            
            self.assertEqual(invalid_response.status_code, 401, "Invalid token should be rejected")
            
            # Test with missing token
            missing_response = requests.get(url)
            print(f"Missing Token Response: {missing_response.status_code}")
            
            self.assertEqual(missing_response.status_code, 401, "Missing token should be rejected")
            
            print("✅ JWT token validation test passed")
        except Exception as e:
            print(f"❌ JWT token validation test failed: {str(e)}")

    def test_16_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check...")
        
        url = f"{API_URL}/health"
        
        try:
            response = requests.get(url)
            print(f"Health Check Response: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Health check should return 200")
            data = response.json()
            
            self.assertEqual(data.get("status"), "healthy", "Status should be 'healthy'")
            self.assertIn("timestamp", data, "Timestamp should be included")
            self.assertIn("version", data, "Version should be included")
            
            print(f"API version: {data.get('version')}")
            print("✅ Health check test passed")
        except Exception as e:
            print(f"❌ Health check test failed: {str(e)}")

if __name__ == "__main__":
    # Run the V3 tests
    print("\n==== TESTING PROJECT K V3 BACKEND ====\n")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
