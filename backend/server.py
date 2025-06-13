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

# Authentication Routes
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

@api_router.get("/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = current_user["user_id"]
    user_type = current_user["user_type"]
    
    try:
        if user_type == UserType.STUDENT:
            user = await db.student_profiles.find_one({"student_id": user_id})
        else:  # Teacher
            user = await db.teachers.find_one({"teacher_id": user_id})
        
        if user:
            user_response = convert_objectid(user)
            user_response.pop('hashed_password', None)
            return {"user": user_response, "user_type": user_type}
        
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user info")

# AI Bot Classes (simplified for V3)
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

# Student Routes (require authentication)
@api_router.get("/student/profile")
async def get_student_profile(current_user = Depends(get_current_user)):
    """Get current student profile"""
    if not current_user or current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        profile_response = convert_objectid(profile)
        profile_response.pop('hashed_password', None)
        return profile_response
    except Exception as e:
        logger.error(f"Error getting student profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

# Chat Routes
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
            "subjects_progress": subjects_studied
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

# Health check routes
@api_router.get("/")
async def root():
    return {"message": "Project K - AI Educational Chatbot API v3.0"}

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
