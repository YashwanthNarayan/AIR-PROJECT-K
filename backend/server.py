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

# V3 Teacher Models
class Classroom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    teacher_id: str
    name: str
    subject: Subject
    grade_level: GradeLevel
    students: List[str] = []  # List of student IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Assignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assignment_id: str
    teacher_id: str
    class_id: Optional[str] = None
    student_ids: List[str] = []  # Can assign to specific students
    title: str
    description: str
    assignment_type: AssignmentType
    subject: Subject
    topics: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class TeacherNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note_id: str
    teacher_id: str
    student_id: str
    subject: Optional[Subject] = None
    title: str
    content: str
    is_private: bool = True  # Only visible to teacher
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    teacher_id: str
    student_id: str
    alert_type: AlertType
    subject: Optional[Subject] = None
    title: str
    description: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

# V3 Input Models
class ClassroomCreate(BaseModel):
    name: str
    subject: Subject
    grade_level: GradeLevel

class AssignmentCreate(BaseModel):
    title: str
    description: str
    assignment_type: AssignmentType
    subject: Subject
    topics: List[str] = []
    class_id: Optional[str] = None
    student_ids: List[str] = []
    due_date: Optional[datetime] = None

class TeacherNoteCreate(BaseModel):
    student_id: str
    subject: Optional[Subject] = None
    title: str
    content: str
    is_private: bool = True

class StudentAssign(BaseModel):
    student_ids: List[str]

# Authentication utility functions
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

# Helper function to convert MongoDB documents
def convert_objectid(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, dict):
        if "_id" in obj:
            del obj["_id"]  # Remove _id field
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    else:
        return obj

# AI Analytics for Teacher Insights
async def analyze_student_performance(student_id: str, teacher_id: str):
    """Analyze student performance and generate insights"""
    try:
        # Get student data
        student = await db.student_profiles.find_one({"student_id": student_id})
        if not student:
            return None

        # Get recent chat messages
        recent_messages = await db.chat_messages.find({"student_id": student_id}).sort("timestamp", -1).limit(50).to_list(50)
        
        # Calculate metrics
        total_messages = len(recent_messages)
        subjects_activity = {}
        
        for msg in recent_messages:
            subject = msg.get('subject')
            if subject:
                if subject not in subjects_activity:
                    subjects_activity[subject] = {'count': 0, 'recent_topics': []}
                subjects_activity[subject]['count'] += 1
                if msg.get('topic'):
                    subjects_activity[subject]['recent_topics'].append(msg.get('topic'))

        # Detect struggling areas
        struggling_subjects = []
        for subject, activity in subjects_activity.items():
            if activity['count'] < 5:  # Less than 5 messages in subject
                struggling_subjects.append(subject)

        # Generate AI insights
        api_key = os.environ.get('GEMINI_API_KEY')
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        analysis_prompt = f"""
        Analyze this student's learning data and provide teacher insights:
        
        Student: {student.get('name')} (Grade {student.get('grade_level')})
        Total XP: {student.get('total_xp', 0)}
        Streak: {student.get('streak_days', 0)} days
        Total Messages: {total_messages}
        Subjects Activity: {subjects_activity}
        
        Provide a brief analysis covering:
        1. Learning strengths
        2. Areas needing attention  
        3. Engagement level
        4. Recommended interventions
        
        Keep response concise and actionable for teachers.
        """
        
        response = await asyncio.to_thread(model.generate_content, analysis_prompt)
        
        return {
            "student_id": student_id,
            "student_name": student.get('name'),
            "grade_level": student.get('grade_level'),
            "total_xp": student.get('total_xp', 0),
            "streak_days": student.get('streak_days', 0),
            "level": student.get('level', 1),
            "total_messages": total_messages,
            "subjects_activity": subjects_activity,
            "struggling_subjects": struggling_subjects,
            "ai_insights": response.text if response else "Analysis unavailable",
            "last_active": student.get('last_active'),
            "recommended_actions": [
                "Encourage more practice in weak subjects",
                "Assign targeted practice tests",
                "Monitor daily engagement"
            ]
        }
    except Exception as e:
        logger.error(f"Error analyzing student performance: {str(e)}")
        return None

# Authentication Routes (existing)
@api_router.post("/auth/register/student")
async def register_student(student_data: StudentRegistration):
    """Register a new student"""
    try:
        # Check if email already exists
        existing_student = await db.student_profiles.find_one({"email": student_data.email})
        if existing_student:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(student_data.password)
        
        # Create student profile
        student_id = str(uuid.uuid4())
        student_dict = student_data.dict()
        student_dict.pop('password')  # Remove plain password
        student_dict['student_id'] = student_id
        student_dict['hashed_password'] = hashed_password
        
        student_obj = StudentProfile(**student_dict)
        await db.student_profiles.insert_one(student_obj.dict())
        
        # Create access token
        access_token = create_access_token(
            data={"sub": student_id, "user_type": UserType.STUDENT}
        )
        
        # Convert and clean response
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
        # Check if email already exists
        existing_teacher = await db.teachers.find_one({"email": teacher_data.email})
        if existing_teacher:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(teacher_data.password)
        
        # Create teacher profile
        teacher_id = str(uuid.uuid4())
        teacher_dict = teacher_data.dict()
        teacher_dict.pop('password')  # Remove plain password
        teacher_dict['teacher_id'] = teacher_id
        teacher_dict['hashed_password'] = hashed_password
        
        teacher_obj = Teacher(**teacher_dict)
        await db.teachers.insert_one(teacher_obj.dict())
        
        # Create access token
        access_token = create_access_token(
            data={"sub": teacher_id, "user_type": UserType.TEACHER}
        )
        
        # Convert and clean response
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
        else:  # Teacher
            user = await db.teachers.find_one({"email": login_data.email})
            if not user or not verify_password(login_data.password, user['hashed_password']):
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            
            user_id = user['teacher_id']
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id, "user_type": login_data.user_type}
        )
        
        # Convert and clean response
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

# V3 Teacher Routes
@api_router.get("/teacher/dashboard")
async def get_teacher_dashboard(current_user = Depends(get_current_user)):
    """Get comprehensive teacher dashboard with student analytics"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        teacher_id = current_user["user_id"]
        teacher = await db.teachers.find_one({"teacher_id": teacher_id})
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        # Get teacher's classes
        classes = await db.classrooms.find({"teacher_id": teacher_id, "is_active": True}).to_list(100)
        
        # Get all students assigned to teacher
        all_student_ids = []
        for classroom in classes:
            all_student_ids.extend(classroom.get('students', []))
        
        # Remove duplicates
        all_student_ids = list(set(all_student_ids))
        
        # Get student profiles
        students = await db.student_profiles.find({"student_id": {"$in": all_student_ids}}).to_list(100)
        
        # Get alerts for teacher
        alerts = await db.alerts.find({"teacher_id": teacher_id, "is_read": False}).sort("created_at", -1).limit(10).to_list(10)
        
        # Calculate teacher stats
        total_students = len(students)
        total_classes = len(classes)
        
        # Get recent student activity
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
                "total_students": total_students,
                "total_classes": total_classes,
                "active_alerts": len(alerts),
                "subjects_taught": teacher.get('subjects_taught', [])
            },
            "classes": [convert_objectid(cls) for cls in classes],
            "students": [convert_objectid(student) for student in students],
            "alerts": [convert_objectid(alert) for alert in alerts],
            "recent_activity": recent_activity
        }
    except Exception as e:
        logger.error(f"Error getting teacher dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get teacher dashboard")

@api_router.post("/teacher/classroom")
async def create_classroom(classroom_data: ClassroomCreate, current_user = Depends(get_current_user)):
    """Create a new classroom"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        class_id = str(uuid.uuid4())
        classroom_obj = Classroom(
            class_id=class_id,
            teacher_id=current_user["user_id"],
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

@api_router.post("/teacher/classroom/{class_id}/students")
async def assign_students_to_class(class_id: str, student_data: StudentAssign, current_user = Depends(get_current_user)):
    """Assign students to a classroom"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Verify classroom belongs to teacher
        classroom = await db.classrooms.find_one({"class_id": class_id, "teacher_id": current_user["user_id"]})
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")
        
        # Update classroom with new students
        await db.classrooms.update_one(
            {"class_id": class_id},
            {"$addToSet": {"students": {"$each": student_data.student_ids}}}
        )
        
        # Update students with assigned teacher
        await db.student_profiles.update_many(
            {"student_id": {"$in": student_data.student_ids}},
            {"$set": {"assigned_teacher": current_user["user_id"]}}
        )
        
        # Update teacher's students list
        await db.teachers.update_one(
            {"teacher_id": current_user["user_id"]},
            {"$addToSet": {"students": {"$each": student_data.student_ids}}}
        )
        
        return {"message": f"Assigned {len(student_data.student_ids)} students to classroom"}
    except Exception as e:
        logger.error(f"Error assigning students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assign students")

@api_router.get("/teacher/student/{student_id}/analytics")
async def get_student_analytics(student_id: str, current_user = Depends(get_current_user)):
    """Get detailed analytics for a specific student"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Verify student is assigned to teacher
        teacher = await db.teachers.find_one({"teacher_id": current_user["user_id"]})
        if not teacher or student_id not in teacher.get('students', []):
            raise HTTPException(status_code=403, detail="Student not assigned to you")
        
        analytics = await analyze_student_performance(student_id, current_user["user_id"])
        if not analytics:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting student analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get student analytics")

@api_router.post("/teacher/assignment")
async def create_assignment(assignment_data: AssignmentCreate, current_user = Depends(get_current_user)):
    """Create a new assignment"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        assignment_id = str(uuid.uuid4())
        assignment_obj = Assignment(
            assignment_id=assignment_id,
            teacher_id=current_user["user_id"],
            **assignment_data.dict()
        )
        
        await db.assignments.insert_one(assignment_obj.dict())
        
        return convert_objectid(assignment_obj.dict())
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create assignment")

@api_router.post("/teacher/note")
async def create_teacher_note(note_data: TeacherNoteCreate, current_user = Depends(get_current_user)):
    """Create a note about a student"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        note_id = str(uuid.uuid4())
        note_obj = TeacherNote(
            note_id=note_id,
            teacher_id=current_user["user_id"],
            **note_data.dict()
        )
        
        await db.teacher_notes.insert_one(note_obj.dict())
        
        return convert_objectid(note_obj.dict())
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create note")

@api_router.get("/teacher/students")
async def get_teacher_students(current_user = Depends(get_current_user)):
    """Get all students assigned to teacher with basic info"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        teacher = await db.teachers.find_one({"teacher_id": current_user["user_id"]})
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        student_ids = teacher.get('students', [])
        if not student_ids:
            return []
        
        students = await db.student_profiles.find({"student_id": {"$in": student_ids}}).to_list(100)
        
        # Add quick stats for each student
        student_list = []
        for student in students:
            # Get basic stats
            total_messages = await db.chat_messages.count_documents({"student_id": student['student_id']})
            last_message = await db.chat_messages.find_one(
                {"student_id": student['student_id']}, 
                sort=[("timestamp", -1)]
            )
            
            student_info = convert_objectid(student)
            student_info.pop('hashed_password', None)
            student_info['total_messages'] = total_messages
            student_info['last_activity'] = last_message['timestamp'] if last_message else student.get('last_active')
            
            student_list.append(student_info)
        
        return student_list
    except Exception as e:
        logger.error(f"Error getting teacher students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get students")

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

# Student Routes (existing functionality maintained)
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
        # Get student profile for context
        student_profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        
        # Get bot response
        bot_response = ""
        bot_type = f"{subject.value}_bot"
        
        if subject in subject_bots:
            bot_response = await subject_bots[subject].teach_subject(
                user_message, session_id, student_profile
            )
        else:
            bot_response = f"I'm here to help you with {subject.value}! What would you like to learn?"
        
        # Create and save the message
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
        
        # Check for alerts (V3 feature)
        await check_student_alerts(current_user["user_id"], student_profile)
        
        return convert_objectid(message_obj.dict())
        
    except Exception as e:
        logger.error(f"Error in chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history")
async def get_chat_history(subject: Optional[Subject] = None, current_user = Depends(get_current_user)):
    """Get chat history for current student"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        query = {"student_id": current_user["user_id"]}
        if subject:
            query["subject"] = subject
            
        messages = await db.chat_messages.find(query).sort("timestamp", 1).to_list(1000)
        return [convert_objectid(message) for message in messages]
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

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
        recent_sessions = await db.chat_sessions.find({"student_id": current_user["user_id"]}).sort("last_active", -1).limit(5).to_list(5)
        
        # Calculate study stats
        total_messages = await db.chat_messages.count_documents({"student_id": current_user["user_id"]})
        subjects_studied = await db.chat_messages.distinct("subject", {"student_id": current_user["user_id"]})
        
        # Get assignments for student
        assignments = await db.assignments.find({
            "$or": [
                {"student_ids": current_user["user_id"]},
                {"class_id": {"$in": []}}  # Class assignments handled separately
            ],
            "is_active": True
        }).sort("created_at", -1).limit(5).to_list(5)
        
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
                "messages": [convert_objectid(msg) for msg in recent_messages],
                "sessions": [convert_objectid(session) for session in recent_sessions]
            },
            "subjects_progress": subjects_studied,
            "assignments": [convert_objectid(assignment) for assignment in assignments]
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

# Alert system
async def check_student_alerts(student_id: str, student_profile: dict):
    """Check if student needs attention and create alerts for teachers"""
    try:
        if not student_profile.get('assigned_teacher'):
            return
        
        # Check for low activity
        recent_messages = await db.chat_messages.find({"student_id": student_id}).sort("timestamp", -1).limit(10).to_list(10)
        
        if len(recent_messages) < 3:  # Less than 3 messages recently
            # Create inactivity alert
            alert_id = str(uuid.uuid4())
            alert = Alert(
                alert_id=alert_id,
                teacher_id=student_profile['assigned_teacher'],
                student_id=student_id,
                alert_type=AlertType.INACTIVE,
                title="Low Student Activity",
                description=f"{student_profile['name']} has been less active recently"
            )
            
            # Check if similar alert already exists
            existing = await db.alerts.find_one({
                "teacher_id": student_profile['assigned_teacher'],
                "student_id": student_id,
                "alert_type": AlertType.INACTIVE,
                "is_read": False
            })
            
            if not existing:
                await db.alerts.insert_one(alert.dict())
                
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")

# Search students for teachers
@api_router.get("/teacher/search/students")
async def search_students(q: str, current_user = Depends(get_current_user)):
    """Search for students to add to classes"""
    if not current_user or current_user["user_type"] != UserType.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Search students by name or email
        students = await db.student_profiles.find({
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]
        }).limit(20).to_list(20)
        
        result = []
        for student in students:
            student_info = {
                "student_id": student['student_id'],
                "name": student['name'],
                "email": student['email'],
                "grade_level": student['grade_level'],
                "subjects": student.get('subjects', [])
            }
            result.append(student_info)
        
        return result
    except Exception as e:
        logger.error(f"Error searching students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search students")

# Health check routes
@api_router.get("/")
async def root():
    return {"message": "Project K - AI Educational Chatbot API v3.0 Complete"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "3.0"}

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
