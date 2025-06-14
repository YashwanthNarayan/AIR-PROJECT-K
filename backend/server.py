from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import jwt
import bcrypt
import random
import string
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import google.generativeai as genai
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
security = HTTPBearer(auto_error=False)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class UserType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

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

class AlertType(str, Enum):
    STRUGGLING = "struggling"
    INACTIVE = "inactive"
    EXCELLENT_PROGRESS = "excellent_progress"
    NEEDS_ATTENTION = "needs_attention"

class AssignmentType(str, Enum):
    PRACTICE_TEST = "practice_test"
    STUDY_TOPIC = "study_topic"
    CUSTOM = "custom"

class NotificationType(str, Enum):
    TEACHER_MESSAGE = "teacher_message"
    ASSIGNMENT = "assignment"
    DAILY_PRACTICE = "daily_practice"
    ACHIEVEMENT = "achievement"
    REMINDER = "reminder"

class CalendarEventType(str, Enum):
    STUDY_SESSION = "study_session"
    PRACTICE_TEST = "practice_test"
    ASSIGNMENT_DUE = "assignment_due"
    CLASS = "class"
    EXAM = "exam"

# Authentication Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    user_type: UserType

class TeacherRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str
    school_name: str
    subjects_taught: List[Subject]
    grade_levels_taught: List[GradeLevel]
    experience_years: int = 0

class StudentRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str
    grade_level: GradeLevel
    subjects: List[Subject] = []
    learning_goals: List[str] = []
    study_hours_per_day: int = 2
    preferred_study_time: str = "evening"

# Enhanced Models with new features
class Classroom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    teacher_id: str
    name: str
    subject: Subject
    grade_level: GradeLevel
    join_code: str  # Unique 6-digit code for students to join
    students: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    description: Optional[str] = None

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str
    recipient_id: str  # student_id
    sender_id: Optional[str] = None  # teacher_id (None for system notifications)
    title: str
    message: str
    notification_type: NotificationType
    related_id: Optional[str] = None  # assignment_id, class_id, etc.
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    student_id: str
    title: str
    description: Optional[str] = None
    event_type: CalendarEventType
    subject: Optional[Subject] = None
    start_time: datetime
    end_time: datetime
    is_completed: bool = False
    reminder_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PracticeTestSettings(BaseModel):
    subject: Subject
    topics: List[str]
    num_questions: int = Field(ge=5, le=50)  # minimum 5, maximum 50
    difficulty: str = "mixed"  # easy, medium, hard, mixed

class Assignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assignment_id: str
    teacher_id: str
    class_id: Optional[str] = None
    student_ids: List[str] = []
    title: str
    description: str
    assignment_type: AssignmentType
    subject: Subject
    topics: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Teacher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    name: str
    email: EmailStr
    hashed_password: str
    school_name: str
    subjects_taught: List[Subject]
    grade_levels_taught: List[GradeLevel]
    experience_years: int
    students: List[str] = []
    classes: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_verified: bool = False

class StudentProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    name: str
    email: EmailStr
    hashed_password: str
    grade_level: GradeLevel
    subjects: List[Subject] = []
    learning_goals: List[str] = []
    study_hours_per_day: int = 2
    preferred_study_time: str = "evening"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_study_time: int = 0
    streak_days: int = 0
    total_xp: int = 0
    level: int = 1
    badges: List[str] = []
    assigned_teacher: Optional[str] = None
    joined_classes: List[str] = []  # List of class_ids

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    student_id: str
    subject: Subject
    user_message: str
    bot_response: str
    bot_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    difficulty_level: Optional[str] = None
    topic: Optional[str] = None
    confidence_score: Optional[float] = None
    learning_points: List[str] = []

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    student_id: str
    subject: Subject
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_messages: int = 0
    topics_covered: List[str] = []
    session_summary: str = ""

# Input Models
class ClassroomCreate(BaseModel):
    name: str
    subject: Subject
    grade_level: GradeLevel
    description: Optional[str] = None

class JoinClassRequest(BaseModel):
    join_code: str

class NotificationCreate(BaseModel):
    recipient_ids: List[str]  # Can send to multiple students
    title: str
    message: str
    notification_type: NotificationType = NotificationType.TEACHER_MESSAGE
    related_id: Optional[str] = None

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: CalendarEventType
    subject: Optional[Subject] = None
    start_time: datetime
    end_time: datetime

# Helper functions
def generate_join_code() -> str:
    """Generate a unique 6-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if user_id is None:
            return None
        return {"user_id": user_id, "user_type": user_type}
    except jwt.PyJWTError:
        return None

def convert_objectid(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, dict):
        if "_id" in obj:
            del obj["_id"]
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    else:
        return obj

# Enhanced Practice Test Generator
async def generate_practice_questions(settings: PracticeTestSettings):
    """Generate customized practice questions based on settings"""
    api_key = os.environ.get('GEMINI_API_KEY')
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    topics_str = ", ".join(settings.topics)
    system_prompt = f"""Generate {settings.num_questions} practice questions for {settings.subject.value.title()}.

    Topics to cover: {topics_str}
    Difficulty: {settings.difficulty}
    Number of questions: {settings.num_questions}
    
    For each question, create a JSON object with:
    - question_text: The question
    - question_type: "mcq", "short_answer", or "numerical"
    - options: Array of 4 options (for MCQ only)
    - correct_answer: The correct answer
    - explanation: Detailed explanation of the solution
    - topic: Which topic this question covers
    - difficulty: "easy", "medium", or "hard"
    
    Return ONLY a valid JSON array with {settings.num_questions} questions.
    Make questions age-appropriate for middle/high school students.
    
    Example format:
    [
      {{
        "question_text": "What is 2 + 2?",
        "question_type": "mcq",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4",
        "explanation": "2 + 2 = 4 by basic addition",
        "topic": "Basic Arithmetic",
        "difficulty": "easy"
      }}
    ]"""
    
    try:
        response = await asyncio.to_thread(model.generate_content, system_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating practice questions: {str(e)}")
        return None

# Daily notification scheduler
async def send_daily_practice_reminders():
    """Send daily practice test reminders to all active students"""
    try:
        # Get all students who were active in the last 3 days
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        active_students = await db.student_profiles.find({
            "last_active": {"$gte": three_days_ago}
        }).to_list(1000)
        
        for student in active_students:
            # Check if already sent today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_reminder = await db.notifications.find_one({
                "recipient_id": student['student_id'],
                "notification_type": NotificationType.DAILY_PRACTICE,
                "created_at": {"$gte": today_start}
            })
            
            if not existing_reminder:
                # Get student's most active subject
                recent_messages = await db.chat_messages.find({
                    "student_id": student['student_id']
                }).sort("timestamp", -1).limit(10).to_list(10)
                
                most_common_subject = "math"  # default
                if recent_messages:
                    subject_counts = {}
                    for msg in recent_messages:
                        subject = msg.get('subject')
                        subject_counts[subject] = subject_counts.get(subject, 0) + 1
                    most_common_subject = max(subject_counts, key=subject_counts.get)
                
                # Create notification
                notification_id = str(uuid.uuid4())
                notification = Notification(
                    notification_id=notification_id,
                    recipient_id=student['student_id'],
                    title="Daily Practice Reminder",
                    message=f"Time for your daily {most_common_subject} practice! Take a quick quiz to reinforce what you learned.",
                    notification_type=NotificationType.DAILY_PRACTICE,
                    related_id=most_common_subject
                )
                
                await db.notifications.insert_one(notification.dict())
                
    except Exception as e:
        logger.error(f"Error sending daily reminders: {str(e)}")

# Authentication Routes (existing)
@api_router.post("/auth/register/student")
async def register_student(student_data: StudentRegistration):
    """Register a new student"""
    try:
        existing_student = await db.student_profiles.find_one({"email": student_data.email})
        if existing_student:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password(student_data.password)
        student_id = str(uuid.uuid4())
        student_dict = student_data.dict()
        student_dict.pop('password')
        student_dict['student_id'] = student_id
        student_dict['hashed_password'] = hashed_password
        
        student_obj = StudentProfile(**student_dict)
        await db.student_profiles.insert_one(student_obj.dict())
        
        access_token = create_access_token(
            data={"sub": student_id, "user_type": UserType.STUDENT}
        )
        
        user_response = student_obj.dict()
        user_response.pop('hashed_password', None)
        user_response = convert_objectid(user_response)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": UserType.STUDENT,
            "user": user_response
        }
    except Exception as e:
        logger.error(f"Error in student registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@api_router.post("/auth/register/teacher")
async def register_teacher(teacher_data: TeacherRegistration):
    """Register a new teacher"""
    try:
        existing_teacher = await db.teachers.find_one({"email": teacher_data.email})
        if existing_teacher:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password(teacher_data.password)
        teacher_id = str(uuid.uuid4())
        teacher_dict = teacher_data.dict()
        teacher_dict.pop('password')
        teacher_dict['teacher_id'] = teacher_id
        teacher_dict['hashed_password'] = hashed_password
        
        teacher_obj = Teacher(**teacher_dict)
        await db.teachers.insert_one(teacher_obj.dict())
        
        access_token = create_access_token(
            data={"sub": teacher_id, "user_type": UserType.TEACHER}
        )
        
        user_response = teacher_obj.dict()
        user_response.pop('hashed_password', None)
        user_response = convert_objectid(user_response)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": UserType.TEACHER,
            "user": user_response
        }
    except Exception as e:
        logger.error(f"Error in teacher registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    """Login for both students and teachers"""
    try:
        if login_data.user_type == UserType.STUDENT:
            user = await db.student_profiles.find_one({"email": login_data.email})
            if not user or not verify_password(login_data.password, user['hashed_password']):
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            user_id = user['student_id']
        else:
            user = await db.teachers.find_one({"email": login_data.email})
            if not user or not verify_password(login_data.password, user['hashed_password']):
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            user_id = user['teacher_id']
        
        access_token = create_access_token(
            data={"sub": user_id, "user_type": login_data.user_type}
        )
        
        user_response = convert_objectid(user)
        user_response.pop('hashed_password', None)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": login_data.user_type,
            "user": user_response
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# Enhanced Teacher Routes
@api_router.post("/teacher/classroom")
async def create_classroom(classroom_data: ClassroomCreate, current_user = Depends(get_current_user)):
    """Create a new classroom with unique join code"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Generate unique join code
        join_code = generate_join_code()
        while await db.classrooms.find_one({"join_code": join_code, "is_active": True}):
            join_code = generate_join_code()
        
        class_id = str(uuid.uuid4())
        classroom_obj = Classroom(
            class_id=class_id,
            teacher_id=current_user["user_id"],
            join_code=join_code,
            **classroom_data.dict()
        )
        
        await db.classrooms.insert_one(classroom_obj.dict())
        
        # Update teacher's classes list
        await db.teachers.update_one(
            {"teacher_id": current_user["user_id"]},
            {"$addToSet": {"classes": class_id}}
        )
        
        return convert_objectid(classroom_obj.dict())
    except Exception as e:
        logger.error(f"Error creating classroom: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create classroom")

@api_router.get("/teacher/dashboard")
async def get_teacher_dashboard(current_user = Depends(get_current_user)):
    """Get comprehensive teacher dashboard"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        teacher_id = current_user["user_id"]
        teacher = await db.teachers.find_one({"teacher_id": teacher_id})
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        # Get teacher's classes
        classes = await db.classrooms.find({"teacher_id": teacher_id, "is_active": True}).to_list(100)
        
        # Get all students in teacher's classes
        all_student_ids = []
        for classroom in classes:
            all_student_ids.extend(classroom.get('students', []))
        all_student_ids = list(set(all_student_ids))
        
        # Get student profiles
        students = await db.student_profiles.find({"student_id": {"$in": all_student_ids}}).to_list(100)
        
        # Get recent activity
        recent_activity = []
        if all_student_ids:
            recent_messages = await db.chat_messages.find(
                {"student_id": {"$in": all_student_ids}}
            ).sort("timestamp", -1).limit(20).to_list(20)
            
            for msg in recent_messages:
                student = next((s for s in students if s['student_id'] == msg['student_id']), None)
                if student:
                    recent_activity.append({
                        "student_name": student['name'],
                        "subject": msg['subject'],
                        "message_preview": msg['user_message'][:50] + "..." if len(msg['user_message']) > 50 else msg['user_message'],
                        "timestamp": msg['timestamp']
                    })

        teacher_response = convert_objectid(teacher)
        teacher_response.pop('hashed_password', None)
        
        return {
            "teacher": teacher_response,
            "stats": {
                "total_students": len(students),
                "total_classes": len(classes),
                "subjects_taught": teacher.get('subjects_taught', [])
            },
            "classes": [convert_objectid(cls) for cls in classes],
            "students": [convert_objectid(student) for student in students],
            "recent_activity": recent_activity
        }
    except Exception as e:
        logger.error(f"Error getting teacher dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get teacher dashboard")

@api_router.post("/teacher/notification")
async def send_notification(notification_data: NotificationCreate, current_user = Depends(get_current_user)):
    """Send notification to students"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        notifications_created = []
        for recipient_id in notification_data.recipient_ids:
            notification_id = str(uuid.uuid4())
            notification = Notification(
                notification_id=notification_id,
                recipient_id=recipient_id,
                sender_id=current_user["user_id"],
                **notification_data.dict(exclude={'recipient_ids'})
            )
            await db.notifications.insert_one(notification.dict())
            notifications_created.append(notification_id)
        
        return {
            "message": f"Sent notification to {len(notification_data.recipient_ids)} students",
            "notification_ids": notifications_created
        }
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

# Enhanced Student Routes
@api_router.post("/student/join-class")
async def join_class(join_request: JoinClassRequest, current_user = Depends(get_current_user)):
    """Join a class using join code"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Find classroom by join code
        classroom = await db.classrooms.find_one({
            "join_code": join_request.join_code.upper(),
            "is_active": True
        })
        
        if not classroom:
            raise HTTPException(status_code=404, detail="Invalid join code")
        
        student_id = current_user["user_id"]
        
        # Check if already joined
        if student_id in classroom.get('students', []):
            raise HTTPException(status_code=400, detail="Already joined this class")
        
        # Add student to classroom
        await db.classrooms.update_one(
            {"class_id": classroom['class_id']},
            {"$addToSet": {"students": student_id}}
        )
        
        # Update student's joined classes
        await db.student_profiles.update_one(
            {"student_id": student_id},
            {"$addToSet": {"joined_classes": classroom['class_id']}}
        )
        
        # Update teacher's students list
        await db.teachers.update_one(
            {"teacher_id": classroom['teacher_id']},
            {"$addToSet": {"students": student_id}}
        )
        
        return {
            "message": f"Successfully joined {classroom['name']}",
            "class": convert_objectid(classroom)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining class: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join class")

@api_router.get("/student/notifications")
async def get_student_notifications(current_user = Depends(get_current_user)):
    """Get notifications for current student"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        notifications = await db.notifications.find({
            "recipient_id": current_user["user_id"]
        }).sort("created_at", -1).limit(50).to_list(50)
        
        return [convert_objectid(notification) for notification in notifications]
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@api_router.put("/student/notification/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user = Depends(get_current_user)):
    """Mark notification as read"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await db.notifications.update_one(
            {
                "notification_id": notification_id,
                "recipient_id": current_user["user_id"]
            },
            {"$set": {"is_read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@api_router.post("/student/calendar/event")
async def create_calendar_event(event_data: CalendarEventCreate, current_user = Depends(get_current_user)):
    """Create a calendar event for student"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        event_id = str(uuid.uuid4())
        event = CalendarEvent(
            event_id=event_id,
            student_id=current_user["user_id"],
            **event_data.dict()
        )
        
        await db.calendar_events.insert_one(event.dict())
        return convert_objectid(event.dict())
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create calendar event")

@api_router.get("/student/calendar")
async def get_student_calendar(current_user = Depends(get_current_user)):
    """Get calendar events for student"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get events for next 30 days
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        events = await db.calendar_events.find({
            "student_id": current_user["user_id"],
            "start_time": {"$gte": start_date, "$lte": end_date}
        }).sort("start_time", 1).to_list(100)
        
        return [convert_objectid(event) for event in events]
    except Exception as e:
        logger.error(f"Error getting calendar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get calendar")

@api_router.post("/practice/generate-custom")
async def generate_custom_practice_test(settings: PracticeTestSettings, current_user = Depends(get_current_user)):
    """Generate customized practice test"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        questions_text = await generate_practice_questions(settings)
        if not questions_text:
            raise HTTPException(status_code=500, detail="Failed to generate questions")
        
        return {
            "questions": questions_text,
            "settings": settings.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating practice test: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate practice test")

@api_router.get("/student/classes")
async def get_student_classes(current_user = Depends(get_current_user)):
    """Get classes that student has joined"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        student = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        joined_classes = student.get('joined_classes', [])
        if not joined_classes:
            return []
        
        classes = await db.classrooms.find({
            "class_id": {"$in": joined_classes},
            "is_active": True
        }).to_list(100)
        
        return [convert_objectid(cls) for cls in classes]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student classes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get student classes")

# AI Bot Classes (simplified for performance)
class SubjectBot:
    def __init__(self, subject: Subject):
        self.subject = subject
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def teach_subject(self, message: str, session_id: str, student_profile=None):
        """Teach subject using Socratic method"""
        system_prompt = f"""You are the {self.subject.value.title()} tutor for Project K. 
        Use the Socratic method - guide students with questions rather than direct answers.
        Be encouraging and supportive. Keep responses concise and age-appropriate for middle/high school."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[])
        
        response = await asyncio.to_thread(
            chat.send_message,
            f"System: {system_prompt}\n\nUser: {message}"
        )
        
        return response.text

# Initialize bots
subject_bots = {
    Subject.MATH: SubjectBot(Subject.MATH),
    Subject.PHYSICS: SubjectBot(Subject.PHYSICS),
    Subject.CHEMISTRY: SubjectBot(Subject.CHEMISTRY),
    Subject.BIOLOGY: SubjectBot(Subject.BIOLOGY),
    Subject.ENGLISH: SubjectBot(Subject.ENGLISH),
    Subject.HISTORY: SubjectBot(Subject.HISTORY),
    Subject.GEOGRAPHY: SubjectBot(Subject.GEOGRAPHY)
}

# Existing chat and dashboard routes (maintained)
@api_router.post("/chat/session")
async def create_chat_session(subject: Subject, current_user = Depends(get_current_user)):
    """Create a new chat session for a subject"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        session_id = str(uuid.uuid4())
        session_obj = ChatSession(
            session_id=session_id,
            student_id=current_user["user_id"],
            subject=subject
        )
        await db.chat_sessions.insert_one(session_obj.dict())
        return convert_objectid(session_obj.dict())
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@api_router.post("/chat/message")
async def send_chat_message(session_id: str, user_message: str, subject: Subject, current_user = Depends(get_current_user)):
    """Send a message and get AI response"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        student_profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        
        bot_response = ""
        bot_type = f"{subject.value}_bot"
        
        if subject in subject_bots:
            bot_response = await subject_bots[subject].teach_subject(
                user_message, session_id, student_profile
            )
        else:
            bot_response = f"I'm here to help you with {subject.value}! What would you like to learn?"
        
        message_obj = ChatMessage(
            session_id=session_id,
            student_id=current_user["user_id"],
            subject=subject,
            user_message=user_message,
            bot_response=bot_response,
            bot_type=bot_type
        )
        
        await db.chat_messages.insert_one(message_obj.dict())
        
        # Update session activity
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"last_active": datetime.utcnow()},
                "$inc": {"total_messages": 1}
            }
        )
        
        # Award XP for engagement
        if student_profile:
            await db.student_profiles.update_one(
                {"student_id": current_user["user_id"]},
                {
                    "$inc": {"total_xp": 5},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
        
        return convert_objectid(message_obj.dict())
        
    except Exception as e:
        logger.error(f"Error in chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/dashboard")
async def get_student_dashboard(current_user = Depends(get_current_user)):
    """Get comprehensive dashboard data for current student"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        if not profile:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get recent activity
        recent_messages = await db.chat_messages.find({"student_id": current_user["user_id"]}).sort("timestamp", -1).limit(10).to_list(10)
        
        # Calculate study stats
        total_messages = await db.chat_messages.count_documents({"student_id": current_user["user_id"]})
        subjects_studied = await db.chat_messages.distinct("subject", {"student_id": current_user["user_id"]})
        
        # Get notifications (last 10)
        notifications = await db.notifications.find({
            "recipient_id": current_user["user_id"]
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Get joined classes
        joined_classes = await db.classrooms.find({
            "class_id": {"$in": profile.get('joined_classes', [])},
            "is_active": True
        }).to_list(100)
        
        # Get calendar events for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_events = await db.calendar_events.find({
            "student_id": current_user["user_id"],
            "start_time": {"$gte": today_start, "$lt": today_end}
        }).sort("start_time", 1).to_list(10)
        
        profile_response = convert_objectid(profile)
        profile_response.pop('hashed_password', None)
        
        return {
            "profile": profile_response,
            "stats": {
                "total_messages": total_messages,
                "subjects_studied": len(subjects_studied),
                "study_streak": profile.get("streak_days", 0),
                "total_xp": profile.get("total_xp", 0),
                "level": profile.get("level", 1)
            },
            "recent_activity": {
                "messages": [convert_objectid(msg) for msg in recent_messages]
            },
            "subjects_progress": subjects_studied,
            "notifications": [convert_objectid(notification) for notification in notifications],
            "joined_classes": [convert_objectid(cls) for cls in joined_classes],
            "today_events": [convert_objectid(event) for event in today_events]
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

# Health check routes
@api_router.get("/")
async def root():
    return {"message": "Project K - AI Educational Chatbot API v3.0 Enhanced"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "3.0-enhanced"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
