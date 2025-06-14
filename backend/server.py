from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import google.generativeai as genai
from enum import Enum
import jwt
import bcrypt
import json
import random
import string

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
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

class UserType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"  
    HARD = "hard"
    MIXED = "mixed"

class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    user_type: UserType
    grade_level: Optional[GradeLevel] = None
    school_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    user_type: UserType
    grade_level: Optional[GradeLevel] = None
    school_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True

# Enhanced Student Models
class StudentProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    student_id: str
    name: str
    email: str
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
    joined_classes: List[str] = []

class TeacherProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    teacher_id: str
    name: str
    email: str
    school_name: str
    subjects_taught: List[Subject] = []
    classes_created: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

# Class Management Models
class ClassRoom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    join_code: str
    teacher_id: str
    subject: Subject
    class_name: str
    grade_level: GradeLevel
    description: Optional[str] = None
    students: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class JoinClassRequest(BaseModel):
    join_code: str

# Chat and Learning Models
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

# Practice Test Models
class PracticeQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: Subject
    topics: List[str]
    question_type: QuestionType
    difficulty: DifficultyLevel
    question_text: str
    options: List[str] = []  # For MCQs
    correct_answer: str
    explanation: str
    learning_objectives: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PracticeTestRequest(BaseModel):
    subject: Subject
    topics: List[str]
    difficulty: DifficultyLevel
    question_count: int = Field(ge=5, le=50)

class PracticeAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    test_id: str
    questions: List[str]
    student_answers: Dict[str, str]
    score: float
    time_taken: int  # seconds
    completed_at: datetime = Field(default_factory=datetime.utcnow)

# Notification Models
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: str
    sender_id: Optional[str] = None
    title: str
    message: str
    type: str  # "system", "teacher_message", "reminder", "achievement"
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Calendar Models
class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    title: str
    description: Optional[str] = None
    event_type: str  # "study_session", "practice_test", "assignment", "exam"
    subject: Optional[Subject] = None
    start_time: datetime
    end_time: datetime
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Mindfulness Models
class MindfulnessActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    activity_type: str  # "breathing", "meditation", "stress_relief", "study_break"
    duration: int  # minutes
    mood_before: Optional[int] = None  # 1-10 scale
    mood_after: Optional[int] = None   # 1-10 scale
    completed_at: datetime = Field(default_factory=datetime.utcnow)

# Utility Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_join_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# AI Bot Classes
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
            },
            Subject.GEOGRAPHY: {
                "topics": ["Physical Geography", "Human Geography", "Climate", "Maps", "Natural Resources", "Population"],
                "approach": "Map-based learning with real-world connections"
            }
        }
        
        profile_context = ""
        if student_profile:
            profile_context = f"Student: Grade {student_profile.get('grade_level')}, Level {student_profile.get('level', 1)}, XP: {student_profile.get('total_xp', 0)}"
            
        curriculum = curriculum_data.get(self.subject, {"topics": [], "approach": "General teaching"})
        
        system_prompt = f"""You are the {self.subject.value.title()} Bot of Project K, a specialized AI tutor for middle and high school {self.subject.value}.

        {profile_context}
        
        Subject Focus: {self.subject.value.title()}
        Key Topics: {', '.join(curriculum['topics'])}
        Teaching Approach: {curriculum['approach']}

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

class PracticeTestBot:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def generate_practice_questions(self, subject: Subject, topics: List[str], difficulty: DifficultyLevel, count: int = 5):
        """Generate adaptive practice questions"""
        
        system_prompt = f"""You are the Practice Test Bot of Project K. Generate {count} practice questions for:
        
        Subject: {subject.value.title()}
        Topics: {', '.join(topics)}
        Difficulty: {difficulty.value.title()}
        
        For each question, provide:
        1. Question text
        2. Question type (MCQ/Short Answer/Numerical)
        3. Options (if MCQ, provide 4 options)
        4. Correct answer
        5. Detailed explanation
        6. Learning objective
        
        Format as JSON array:
        [
          {{
            "question_text": "...",
            "question_type": "mcq",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "correct_answer": "A. Option 1",
            "explanation": "...",
            "learning_objective": "..."
          }}
        ]
        
        Make questions NCERT curriculum aligned and age-appropriate. Ensure variety in question types and difficulty within the specified level."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await asyncio.to_thread(model.generate_content, system_prompt)
        
        try:
            # Extract JSON from response
            response_text = response.text
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            json_str = response_text[start_idx:end_idx]
            questions_data = json.loads(json_str)
            
            # Create PracticeQuestion objects
            questions = []
            for q_data in questions_data:
                question = PracticeQuestion(
                    subject=subject,
                    topics=topics,
                    question_type=QuestionType(q_data.get('question_type', 'mcq')),
                    difficulty=difficulty,
                    question_text=q_data['question_text'],
                    options=q_data.get('options', []),
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data['explanation'],
                    learning_objectives=[q_data.get('learning_objective', '')]
                )
                questions.append(question)
            
            return questions
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to simple questions if JSON parsing fails
            return await self._generate_fallback_questions(subject, topics, difficulty, count)

    async def _generate_fallback_questions(self, subject: Subject, topics: List[str], difficulty: DifficultyLevel, count: int):
        """Generate fallback questions when JSON parsing fails"""
        questions = []
        for i in range(count):
            question = PracticeQuestion(
                subject=subject,
                topics=topics,
                question_type=QuestionType.MCQ,
                difficulty=difficulty,
                question_text=f"Sample {subject.value} question {i+1} on {', '.join(topics)}",
                options=["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                correct_answer="A. Option 1",
                explanation="This is a sample explanation.",
                learning_objectives=["Practice basic concepts"]
            )
            questions.append(question)
        return questions

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
practice_bot = PracticeTestBot()

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user (student or teacher)"""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        user_type=user_data.user_type,
        grade_level=user_data.grade_level,
        school_name=user_data.school_name
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict['password'] = hashed_password
    await db.users.insert_one(user_dict)
    
    # Create profile based on user type
    if user_data.user_type == UserType.STUDENT:
        student_profile = StudentProfile(
            user_id=user.id,
            student_id=user.id,
            name=user_data.name,
            email=user_data.email,
            grade_level=user_data.grade_level
        )
        await db.student_profiles.insert_one(student_profile.dict())
    else:
        teacher_profile = TeacherProfile(
            user_id=user.id,
            teacher_id=user.id,
            name=user_data.name,
            email=user_data.email,
            school_name=user_data.school_name or "Unknown School"
        )
        await db.teacher_profiles.insert_one(teacher_profile.dict())
    
    # Create access token
    access_token = create_access_token({"sub": user.id, "email": user.email, "user_type": user_data.user_type})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "user_type": user_data.user_type
    }

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    """Login user"""
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc or not verify_password(login_data.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = User(**user_doc)
    
    # Update last login
    await db.users.update_one(
        {"email": login_data.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token = create_access_token({"sub": user.id, "email": user.email, "user_type": user.user_type})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "user_type": user.user_type
    }

# Student Routes
@api_router.get("/student/profile")
async def get_student_profile(token_data: dict = Depends(verify_token)):
    """Get current student profile"""
    if token_data.get('user_type') != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    profile = await db.student_profiles.find_one({"user_id": token_data['sub']})
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    return StudentProfile(**profile)

@api_router.put("/student/profile")
async def update_student_profile(updates: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Update student profile"""
    if token_data.get('user_type') != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    updates['last_active'] = datetime.utcnow()
    result = await db.student_profiles.update_one(
        {"user_id": token_data['sub']}, 
        {"$set": updates}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    profile = await db.student_profiles.find_one({"user_id": token_data['sub']})
    return StudentProfile(**profile)

# Teacher Routes
@api_router.get("/teacher/profile")
async def get_teacher_profile(token_data: dict = Depends(verify_token)):
    """Get current teacher profile"""
    if token_data.get('user_type') != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    profile = await db.teacher_profiles.find_one({"user_id": token_data['sub']})
    if not profile:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    
    return TeacherProfile(**profile)

# Class Management Routes
@api_router.post("/teacher/classes")
async def create_class(class_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Create a new class"""
    if token_data.get('user_type') != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Generate unique join code
    join_code = generate_join_code()
    while await db.classrooms.find_one({"join_code": join_code}):
        join_code = generate_join_code()
    
    classroom = ClassRoom(
        class_id=str(uuid.uuid4()),
        join_code=join_code,
        teacher_id=token_data['sub'],
        subject=Subject(class_data['subject']),
        class_name=class_data['class_name'],
        grade_level=GradeLevel(class_data['grade_level']),
        description=class_data.get('description', '')
    )
    
    await db.classrooms.insert_one(classroom.dict())
    
    # Update teacher's classes
    await db.teacher_profiles.update_one(
        {"user_id": token_data['sub']},
        {"$push": {"classes_created": classroom.class_id}}
    )
    
    return classroom

@api_router.get("/teacher/classes")
async def get_teacher_classes(token_data: dict = Depends(verify_token)):
    """Get all classes created by teacher"""
    if token_data.get('user_type') != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    classes = await db.classrooms.find({"teacher_id": token_data['sub']}).to_list(100)
    return [ClassRoom(**cls) for cls in classes]

@api_router.post("/student/join-class")
async def join_class(request: JoinClassRequest, token_data: dict = Depends(verify_token)):
    """Student joins a class using join code"""
    if token_data.get('user_type') != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Find class by join code
    classroom = await db.classrooms.find_one({"join_code": request.join_code, "is_active": True})
    if not classroom:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    # Add student to class
    student_id = token_data['sub']
    if student_id not in classroom['students']:
        await db.classrooms.update_one(
            {"join_code": request.join_code},
            {"$push": {"students": student_id}}
        )
        
        # Update student's joined classes
        await db.student_profiles.update_one(
            {"user_id": student_id},
            {"$push": {"joined_classes": classroom['class_id']}}
        )
    
    return {"message": "Successfully joined class", "class": ClassRoom(**classroom)}

@api_router.get("/student/classes")
async def get_student_classes(token_data: dict = Depends(verify_token)):
    """Get all classes joined by student"""
    if token_data.get('user_type') != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    student_profile = await db.student_profiles.find_one({"user_id": token_data['sub']})
    if not student_profile:
        return []
    
    class_ids = student_profile.get('joined_classes', [])
    classes = await db.classrooms.find({"class_id": {"$in": class_ids}}).to_list(100)
    return [ClassRoom(**cls) for cls in classes]

# Chat Routes
@api_router.post("/chat/session")
async def create_chat_session(session_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Create a new chat session"""
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        student_id=token_data['sub'],
        subject=Subject(session_data['subject'])
    )
    await db.chat_sessions.insert_one(session.dict())
    return session

@api_router.post("/chat/message")
async def send_chat_message(message_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Send a message and get AI response"""
    try:
        # Get student profile for context
        student_profile = await db.student_profiles.find_one({"user_id": token_data['sub']})
        
        # Get conversation history for context
        conversation_history = await db.chat_messages.find(
            {"session_id": message_data['session_id']}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        subject = Subject(message_data['subject'])
        user_message = message_data['user_message']
        
        # Route to appropriate subject bot
        if subject in subject_bots:
            bot_response = await subject_bots[subject].teach_subject(
                user_message, message_data['session_id'], student_profile, conversation_history
            )
            bot_type = f"{subject.value}_bot"
        else:
            # Handle with central brain
            central_response = await central_brain.analyze_and_route(
                user_message, message_data['session_id'], student_profile
            )
            bot_response = central_response
            bot_type = "central_brain"
        
        # Create and save the message
        message_obj = ChatMessage(
            session_id=message_data['session_id'],
            student_id=token_data['sub'],
            subject=subject,
            user_message=user_message,
            bot_response=bot_response,
            bot_type=bot_type
        )
        
        await db.chat_messages.insert_one(message_obj.dict())
        
        # Update session activity
        await db.chat_sessions.update_one(
            {"session_id": message_data['session_id']},
            {
                "$set": {"last_active": datetime.utcnow()},
                "$inc": {"total_messages": 1}
            }
        )
        
        # Award XP for engagement
        if student_profile:
            xp_earned = 5  # Base XP for asking questions
            await db.student_profiles.update_one(
                {"user_id": token_data['sub']},
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
async def get_chat_history(subject: Optional[str] = None, token_data: dict = Depends(verify_token)):
    """Get chat history for a student, optionally filtered by subject"""
    query = {"student_id": token_data['sub']}
    if subject:
        query["subject"] = subject
        
    messages = await db.chat_messages.find(query).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**message) for message in messages]

# Practice Test Routes
@api_router.post("/practice/generate")
async def generate_practice_test(request: PracticeTestRequest, token_data: dict = Depends(verify_token)):
    """Generate practice questions"""
    try:
        questions = await practice_bot.generate_practice_questions(
            request.subject, request.topics, request.difficulty, request.question_count
        )
        
        # Store questions in database
        question_ids = []
        for question in questions:
            await db.practice_questions.insert_one(question.dict())
            question_ids.append(question.id)
        
        return {
            "test_id": str(uuid.uuid4()),
            "questions": questions,
            "total_questions": len(questions)
        }
    except Exception as e:
        logger.error(f"Error generating practice test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating practice test: {str(e)}")

@api_router.post("/practice/submit")
async def submit_practice_test(test_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Submit practice test answers"""
    try:
        # Calculate score
        total_questions = len(test_data['questions'])
        correct_answers = 0
        
        for question_id, student_answer in test_data['student_answers'].items():
            question = await db.practice_questions.find_one({"id": question_id})
            if question and question['correct_answer'].lower() == student_answer.lower():
                correct_answers += 1
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Create attempt record
        attempt = PracticeAttempt(
            student_id=token_data['sub'],
            test_id=test_data['test_id'],
            questions=test_data['questions'],
            student_answers=test_data['student_answers'],
            score=score,
            time_taken=test_data.get('time_taken', 0)
        )
        
        await db.practice_attempts.insert_one(attempt.dict())
        
        # Award XP based on score
        xp_earned = int(score / 10) * 5  # 5 XP per 10% score
        await db.student_profiles.update_one(
            {"user_id": token_data['sub']},
            {"$inc": {"total_xp": xp_earned}}
        )
        
        return {
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "xp_earned": xp_earned
        }
        
    except Exception as e:
        logger.error(f"Error submitting practice test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting practice test: {str(e)}")

# Mindfulness Routes
@api_router.post("/mindfulness/session")
async def start_mindfulness_session(session_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Start a mindfulness session"""
    session = MindfulnessActivity(
        student_id=token_data['sub'],
        activity_type=session_data['activity_type'],
        duration=session_data['duration'],
        mood_before=session_data.get('mood_before'),
        mood_after=session_data.get('mood_after')
    )
    await db.mindfulness_activities.insert_one(session.dict())
    
    # Award XP for mindfulness activity
    await db.student_profiles.update_one(
        {"user_id": token_data['sub']},
        {"$inc": {"total_xp": 10}}  # 10 XP for mindfulness
    )
    
    return session

@api_router.get("/mindfulness/activities")
async def get_mindfulness_history(token_data: dict = Depends(verify_token)):
    """Get mindfulness activity history"""
    activities = await db.mindfulness_activities.find({"student_id": token_data['sub']}).sort("completed_at", -1).to_list(50)
    return [MindfulnessActivity(**activity) for activity in activities]

# Notification Routes
@api_router.get("/notifications")
async def get_notifications(token_data: dict = Depends(verify_token)):
    """Get user notifications"""
    notifications = await db.notifications.find({"recipient_id": token_data['sub']}).sort("created_at", -1).to_list(50)
    return [Notification(**notification) for notification in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, token_data: dict = Depends(verify_token)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notification_id, "recipient_id": token_data['sub']},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

# Calendar Routes
@api_router.post("/calendar/events")
async def create_calendar_event(event_data: Dict[str, Any], token_data: dict = Depends(verify_token)):
    """Create a calendar event"""
    event = CalendarEvent(
        student_id=token_data['sub'],
        title=event_data['title'],
        description=event_data.get('description'),
        event_type=event_data['event_type'],
        subject=Subject(event_data['subject']) if event_data.get('subject') else None,
        start_time=datetime.fromisoformat(event_data['start_time']),
        end_time=datetime.fromisoformat(event_data['end_time'])
    )
    
    await db.calendar_events.insert_one(event.dict())
    return event

@api_router.get("/calendar/events")
async def get_calendar_events(token_data: dict = Depends(verify_token)):
    """Get user's calendar events"""
    events = await db.calendar_events.find({"student_id": token_data['sub']}).sort("start_time", 1).to_list(100)
    return [CalendarEvent(**event) for event in events]

# Dashboard Routes
@api_router.get("/dashboard")
async def get_student_dashboard(token_data: dict = Depends(verify_token)):
    """Get comprehensive dashboard data for a student"""
    if token_data.get('user_type') != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    profile = await db.student_profiles.find_one({"user_id": token_data['sub']})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get recent activity
    recent_messages = await db.chat_messages.find({"student_id": token_data['sub']}).sort("timestamp", -1).limit(10).to_list(10)
    recent_sessions = await db.chat_sessions.find({"student_id": token_data['sub']}).sort("last_active", -1).limit(5).to_list(5)
    
    # Calculate study stats
    total_messages = await db.chat_messages.count_documents({"student_id": token_data['sub']})
    subjects_studied = await db.chat_messages.distinct("subject", {"student_id": token_data['sub']})
    
    # Get today's events
    today = datetime.now().date()
    today_events = await db.calendar_events.find({
        "student_id": token_data['sub'],
        "start_time": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(10)
    
    # Get notifications
    notifications = await db.notifications.find({"recipient_id": token_data['sub'], "is_read": False}).to_list(10)
    
    return {
        "profile": StudentProfile(**profile),
        "stats": {
            "total_messages": total_messages,
            "subjects_studied": len(subjects_studied),
            "study_streak": profile.get("streak_days", 0),
            "total_xp": profile.get("total_xp", 0),
            "level": profile.get("level", 1)
        },
        "recent_activity": {
            "messages": [ChatMessage(**msg) for msg in recent_messages],
            "sessions": [ChatSession(**session) for session in recent_sessions]
        },
        "today_events": [CalendarEvent(**event) for event in today_events],
        "notifications": [Notification(**notification) for notification in notifications],
        "subjects_progress": subjects_studied
    }

@api_router.get("/teacher/dashboard")
async def get_teacher_dashboard(token_data: dict = Depends(verify_token)):
    """Get comprehensive dashboard data for a teacher"""
    if token_data.get('user_type') != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    profile = await db.teacher_profiles.find_one({"user_id": token_data['sub']})
    if not profile:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get teacher's classes
    classes = await db.classrooms.find({"teacher_id": token_data['sub']}).to_list(100)
    
    # Get analytics for all students in teacher's classes
    all_student_ids = []
    for cls in classes:
        all_student_ids.extend(cls.get('students', []))
    
    # Get student activity data
    total_students = len(set(all_student_ids))
    recent_activity = await db.chat_messages.find(
        {"student_id": {"$in": all_student_ids}}
    ).sort("timestamp", -1).limit(20).to_list(20)
    
    return {
        "profile": TeacherProfile(**profile),
        "classes": [ClassRoom(**cls) for cls in classes],
        "stats": {
            "total_classes": len(classes),
            "total_students": total_students,
            "recent_activity_count": len(recent_activity)
        },
        "recent_activity": [ChatMessage(**msg) for msg in recent_activity]
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
