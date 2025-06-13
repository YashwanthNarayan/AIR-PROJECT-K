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
security = HTTPBearer()

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

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"  
    HARD = "hard"

class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"

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
    students: List[str] = []  # List of student IDs
    classes: List[str] = []   # List of class IDs
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
    total_study_time: int = 0  # in minutes
    streak_days: int = 0
    total_xp: int = 0
    level: int = 1
    badges: List[str] = []
    assigned_teacher: Optional[str] = None  # Teacher ID

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    student_id: str
    subject: Subject
    user_message: str
    bot_response: str
    bot_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    difficulty_level: Optional[DifficultyLevel] = None
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

class PracticeQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: Subject
    topic: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    question_text: str
    options: List[str] = []  # For MCQs
    correct_answer: str
    explanation: str
    learning_objectives: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PracticeAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    question_id: str
    student_answer: str
    is_correct: bool
    time_taken: int  # seconds
    hints_used: int = 0
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

class StudySession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    subject: Subject
    topic: str
    duration: int  # minutes
    activities: List[str] = []  # ["chat", "practice_test", "mindfulness"]
    xp_earned: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class MindfulnessActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    activity_type: str  # "breathing", "meditation", "stress_relief"
    duration: int  # minutes
    mood_before: Optional[int] = None  # 1-10 scale
    mood_after: Optional[int] = None   # 1-10 scale
    completed_at: datetime = Field(default_factory=datetime.utcnow)

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
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"user_id": user_id, "user_type": user_type}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Authentication Routes
@api_router.post("/auth/register/student")
async def register_student(student_data: StudentRegistration):
    """Register a new student"""
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": UserType.STUDENT,
        "user": student_obj
    }

@api_router.post("/auth/register/teacher")
async def register_teacher(teacher_data: TeacherRegistration):
    """Register a new teacher"""
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": UserType.TEACHER,
        "user": teacher_obj
    }

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    """Login for both students and teachers"""
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
    
    # Remove hashed_password from response
    user.pop('hashed_password', None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": login_data.user_type,
        "user": user
    }

@api_router.get("/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    user_id = current_user["user_id"]
    user_type = current_user["user_type"]
    
    if user_type == UserType.STUDENT:
        user = await db.student_profiles.find_one({"student_id": user_id})
        if user:
            user.pop('hashed_password', None)
            return {"user": user, "user_type": user_type}
    else:  # Teacher
        user = await db.teachers.find_one({"teacher_id": user_id})
        if user:
            user.pop('hashed_password', None)
            return {"user": user, "user_type": user_type}
    
    raise HTTPException(status_code=404, detail="User not found")

# AI Bot Classes (keeping existing functionality)
class CentralBrainBot:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def analyze_and_route(self, message: str, session_id: str, student_profile=None):
        """Analyze user message and determine which bot should handle it"""
        profile_context = ""
        if student_profile:
            profile_context = f"Student Profile: Grade {student_profile.get('grade_level')}, Subjects: {student_profile.get('subjects')}, Current Level: {student_profile.get('level', 1)}"
            
        system_prompt = f"""You are the Central Brain of Project K, an AI educational tutor system. 
        Your job is to analyze student messages and determine which subject-specific bot should handle them.
        
        {profile_context}
        
        Available subjects: Math, Physics, Chemistry, Biology, English, History, Geography
        Available activities: Study, Practice Tests, Mindfulness, Review
        
        Analyze the student's message and respond with:
        1. Subject: [Math/Physics/Chemistry/Biology/English/History/Geography/General]
        2. Topic: [specific topic if identifiable]
        3. Difficulty: [Easy/Medium/Hard] (based on grade level and content)
        4. Urgency: [Low/Medium/High] (based on keywords like "test tomorrow", "homework due", etc.)
        5. Mood: [Confused/Frustrated/Excited/Stressed/Neutral] (based on tone)
        6. Activity Type: [Study/Practice/Review/Mindfulness]
        
        Routing Rules:
        - Math questions: ROUTE_TO: math_bot
        - Physics questions: ROUTE_TO: physics_bot  
        - Chemistry questions: ROUTE_TO: chemistry_bot
        - Biology questions: ROUTE_TO: biology_bot
        - English/Literature questions: ROUTE_TO: english_bot
        - History questions: ROUTE_TO: history_bot
        - Geography questions: ROUTE_TO: geography_bot
        - Stress/overwhelm mentions: ROUTE_TO: mindfulness_bot
        - Practice test requests: ROUTE_TO: practice_bot
        - General conversation: Handle yourself with encouragement
        
        Always be encouraging and supportive. Remember, you're helping middle and high school students."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[])
        
        response = await asyncio.to_thread(
            chat.send_message,
            f"System: {system_prompt}\n\nUser: {message}"
        )
        
        return response.text

class SubjectBot:
    def __init__(self, subject: Subject):
        self.subject = subject
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def teach_subject(self, message: str, session_id: str, student_profile=None, conversation_history=None):
        """Teach subject using Socratic method with personalized approach"""
        
        # Subject-specific curriculum knowledge (NCERT-based)
        curriculum_data = {
            Subject.MATH: {
                "topics": ["Algebra", "Geometry", "Trigonometry", "Calculus", "Statistics", "Probability"],
                "approach": "Step-by-step problem solving with visual aids when possible"
            },
            Subject.PHYSICS: {
                "topics": ["Mechanics", "Thermodynamics", "Waves", "Optics", "Electricity", "Magnetism", "Modern Physics"],
                "approach": "Concept-based learning with real-world applications and experiments"
            },
            Subject.CHEMISTRY: {
                "topics": ["Atomic Structure", "Periodic Table", "Chemical Bonding", "Acids & Bases", "Organic Chemistry", "Physical Chemistry"],
                "approach": "Practical understanding with chemical equations and reactions"
            },
            Subject.BIOLOGY: {
                "topics": ["Cell Biology", "Genetics", "Evolution", "Ecology", "Human Physiology", "Plant Biology"],
                "approach": "Visual learning with diagrams and life processes"
            },
            Subject.ENGLISH: {
                "topics": ["Grammar", "Literature", "Poetry", "Essay Writing", "Reading Comprehension", "Creative Writing"],
                "approach": "Language skills development through practice and analysis"
            },
            Subject.HISTORY: {
                "topics": ["Ancient History", "Medieval History", "Modern History", "World Wars", "Indian Independence", "Civilizations"],
                "approach": "Timeline-based learning with cause-and-effect relationships"
            }
        }
        
        profile_context = ""
        if student_profile:
            profile_context = f"Student: Grade {student_profile.get('grade_level')}, Level {student_profile.get('level', 1)}, XP: {student_profile.get('total_xp', 0)}"
            
        history_context = ""
        if conversation_history:
            history_context = f"Previous conversation context: {conversation_history[-3:]}" # Last 3 messages
            
        curriculum = curriculum_data.get(self.subject, {"topics": [], "approach": "General teaching"})
        
        system_prompt = f"""You are the {self.subject.value.title()} Bot of Project K, a specialized AI tutor for middle and high school {self.subject.value}.

        {profile_context}
        
        Subject Focus: {self.subject.value.title()}
        Key Topics: {', '.join(curriculum['topics'])}
        Teaching Approach: {curriculum['approach']}
        
        {history_context}

        Teaching Philosophy:
        1. Use the Socratic method - ask guiding questions and give hints rather than direct answers
        2. If a student seems really stuck after 2-3 attempts, provide direct explanation
        3. Break complex problems into smaller, manageable steps
        4. Use real-world examples and visual descriptions when possible
        5. Always encourage and build confidence
        6. Adapt difficulty based on student's grade level and performance
        7. Reference NCERT curriculum when appropriate
        
        Response format:
        - Start with a brief encouraging comment
        - Ask a guiding question or give a hint
        - If they're stuck, provide a step-by-step explanation
        - End with a question to check understanding
        - Suggest related practice if appropriate
        
        Remember: You're helping students LEARN, not just getting answers. Make {self.subject.value} feel approachable and fun!"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[])
        
        response = await asyncio.to_thread(
            chat.send_message,
            f"System: {system_prompt}\n\nUser: {message}"
        )
        
        return response.text

# Initialize bots
central_brain = CentralBrainBot()
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
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    profile.pop('hashed_password', None)
    return profile

@api_router.put("/student/profile")
async def update_student_profile(updates: Dict[str, Any], current_user = Depends(get_current_user)):
    """Update current student profile"""
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updates['last_active'] = datetime.utcnow()
    result = await db.student_profiles.update_one(
        {"student_id": current_user["user_id"]}, 
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
    profile.pop('hashed_password', None)
    return profile

# Enhanced Chat Routes with Authentication
@api_router.post("/chat/session")
async def create_chat_session(subject: Subject, current_user = Depends(get_current_user)):
    """Create a new chat session for a subject"""
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_id = str(uuid.uuid4())
    session_obj = ChatSession(
        session_id=session_id,
        student_id=current_user["user_id"],
        subject=subject
    )
    await db.chat_sessions.insert_one(session_obj.dict())
    return session_obj

@api_router.post("/chat/message")
async def send_chat_message(session_id: str, user_message: str, subject: Subject, current_user = Depends(get_current_user)):
    """Send a message and get AI response"""
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get student profile for context
        student_profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
        
        # Get conversation history for context
        conversation_history = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Route to specific subject bot
        bot_response = ""
        bot_type = f"{subject.value}_bot"
        
        if subject in subject_bots:
            bot_response = await subject_bots[subject].teach_subject(
                user_message, session_id, student_profile, conversation_history
            )
        else:
            # Fallback to central brain
            bot_response = await central_brain.analyze_and_route(
                user_message, session_id, student_profile
            )
            bot_type = "central_brain"
        
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
            xp_earned = 5  # Base XP for asking questions
            await db.student_profiles.update_one(
                {"student_id": current_user["user_id"]},
                {
                    "$inc": {"total_xp": xp_earned},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
        
        return message_obj
        
    except Exception as e:
        logger.error(f"Error in chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history")
async def get_chat_history(subject: Optional[Subject] = None, current_user = Depends(get_current_user)):
    """Get chat history for current student, optionally filtered by subject"""
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {"student_id": current_user["user_id"]}
    if subject:
        query["subject"] = subject
        
    messages = await db.chat_messages.find(query).sort("timestamp", 1).to_list(1000)
    return messages

@api_router.get("/dashboard")
async def get_student_dashboard(current_user = Depends(get_current_user)):
    """Get comprehensive dashboard data for current student"""
    if current_user["user_type"] != UserType.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    profile = await db.student_profiles.find_one({"student_id": current_user["user_id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get recent activity
    recent_messages = await db.chat_messages.find({"student_id": current_user["user_id"]}).sort("timestamp", -1).limit(10).to_list(10)
    recent_sessions = await db.chat_sessions.find({"student_id": current_user["user_id"]}).sort("last_active", -1).limit(5).to_list(5)
    
    # Calculate study stats
    total_messages = await db.chat_messages.count_documents({"student_id": current_user["user_id"]})
    subjects_studied = await db.chat_messages.distinct("subject", {"student_id": current_user["user_id"]})
    
    profile.pop('hashed_password', None)
    
    return {
        "profile": profile,
        "stats": {
            "total_messages": total_messages,
            "subjects_studied": len(subjects_studied),
            "study_streak": profile.get("streak_days", 0),
            "total_xp": profile.get("total_xp", 0),
            "level": profile.get("level", 1)
        },
        "recent_activity": {
            "messages": recent_messages,
            "sessions": recent_sessions
        },
        "subjects_progress": subjects_studied
    }

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
