from fastapi import FastAPI, APIRouter, HTTPException
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"  
    HARD = "hard"

class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"

# Enhanced Models
class StudentProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    name: str
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

class StudentProfileCreate(BaseModel):
    name: str
    grade_level: GradeLevel
    subjects: List[Subject] = []
    learning_goals: List[str] = []
    study_hours_per_day: int = 2
    preferred_study_time: str = "evening"

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

class ChatMessageCreate(BaseModel):
    session_id: str
    student_id: str
    subject: Subject
    user_message: str

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

class ChatSessionCreate(BaseModel):
    student_id: str
    subject: Subject

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

class MindfulnessBot:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def provide_mindfulness_support(self, message: str, student_profile=None):
        """Provide mindfulness and stress management support"""
        
        profile_context = ""
        if student_profile:
            profile_context = f"Student: Grade {student_profile.get('grade_level')}, Stress Level: Based on recent activity"
            
        system_prompt = f"""You are the Mindfulness Bot of Project K, specialized in helping students manage stress, anxiety, and maintain mental well-being.

        {profile_context}
        
        Your capabilities:
        1. Guided breathing exercises (4-7-8 technique, box breathing)
        2. Short meditation sessions (1-5 minutes)
        3. Stress management techniques
        4. Study break activities
        5. Burnout detection and prevention
        6. Positive affirmations and motivation
        
        Available Activities:
        - "BREATHING_EXERCISE": Guide through breathing techniques
        - "MEDITATION": Short guided meditation
        - "STRESS_RELIEF": Quick stress reduction techniques
        - "STUDY_BREAK": Fun activities for study breaks
        - "MOTIVATION": Positive reinforcement and encouragement
        
        Always:
        - Be empathetic and understanding
        - Provide practical, actionable advice
        - Keep sessions age-appropriate for middle/high school students
        - Encourage healthy study habits
        - Recognize when to suggest taking breaks or seeking additional help
        
        If the student seems overwhelmed or mentions serious stress, gently suggest they also talk to a teacher, counselor, or parent."""
        
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
        
    async def generate_practice_questions(self, subject: Subject, topic: str, difficulty: DifficultyLevel, count: int = 5):
        """Generate adaptive practice questions"""
        
        system_prompt = f"""You are the Practice Test Bot of Project K. Generate {count} practice questions for:
        
        Subject: {subject.value.title()}
        Topic: {topic}
        Difficulty: {difficulty.value.title()}
        
        For each question, provide:
        1. Question text
        2. Question type (MCQ/Short Answer/Numerical)
        3. Options (if MCQ)
        4. Correct answer
        5. Detailed explanation
        6. Learning objective
        
        Format as JSON array:
        [
          {{
            "question_text": "...",
            "question_type": "mcq",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "...",
            "learning_objective": "..."
          }}
        ]
        
        Make questions NCERT curriculum aligned and age-appropriate."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await asyncio.to_thread(model.generate_content, system_prompt)
        
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
mindfulness_bot = MindfulnessBot()
practice_bot = PracticeTestBot()

# Routes - Student Profile Management
@api_router.post("/student/profile", response_model=StudentProfile)
async def create_student_profile(input: StudentProfileCreate):
    """Create a new student profile"""
    profile_dict = input.dict()
    student_id = str(uuid.uuid4())
    profile_dict['student_id'] = student_id
    profile_obj = StudentProfile(**profile_dict)
    await db.student_profiles.insert_one(profile_obj.dict())
    return profile_obj

@api_router.get("/student/profile/{student_id}", response_model=StudentProfile)
async def get_student_profile(student_id: str):
    """Get student profile"""
    profile = await db.student_profiles.find_one({"student_id": student_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return StudentProfile(**profile)

@api_router.put("/student/profile/{student_id}", response_model=StudentProfile)
async def update_student_profile(student_id: str, updates: Dict[str, Any]):
    """Update student profile"""
    updates['last_active'] = datetime.utcnow()
    result = await db.student_profiles.update_one(
        {"student_id": student_id}, 
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    profile = await db.student_profiles.find_one({"student_id": student_id})
    return StudentProfile(**profile)

# Enhanced Chat Routes
@api_router.post("/chat/session", response_model=ChatSession)
async def create_chat_session(input: ChatSessionCreate):
    """Create a new chat session for a subject"""
    session_dict = input.dict()
    session_id = str(uuid.uuid4())
    session_dict['session_id'] = session_id
    session_obj = ChatSession(**session_dict)
    await db.chat_sessions.insert_one(session_obj.dict())
    return session_obj

@api_router.post("/chat/message", response_model=ChatMessage)
async def send_chat_message(input: ChatMessageCreate):
    """Send a message and get AI response"""
    try:
        # Get student profile for context
        student_profile = await db.student_profiles.find_one({"student_id": input.student_id})
        
        # Get conversation history for context
        conversation_history = await db.chat_messages.find(
            {"session_id": input.session_id}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Let central brain analyze the message
        central_response = await central_brain.analyze_and_route(
            input.user_message, input.session_id, student_profile
        )
        
        # Determine routing based on subject or central brain analysis
        bot_response = ""
        bot_type = "central_brain"
        
        if input.subject in subject_bots:
            # Route to specific subject bot
            bot_response = await subject_bots[input.subject].teach_subject(
                input.user_message, input.session_id, student_profile, conversation_history
            )
            bot_type = f"{input.subject.value}_bot"
        elif "ROUTE_TO: mindfulness_bot" in central_response or "stress" in input.user_message.lower():
            # Route to mindfulness bot
            bot_response = await mindfulness_bot.provide_mindfulness_support(
                input.user_message, student_profile
            )
            bot_type = "mindfulness_bot"
        else:
            # Handle with central brain
            bot_response = central_response
            bot_type = "central_brain"
        
        # Create and save the message
        message_obj = ChatMessage(
            session_id=input.session_id,
            student_id=input.student_id,
            subject=input.subject,
            user_message=input.user_message,
            bot_response=bot_response,
            bot_type=bot_type
        )
        
        await db.chat_messages.insert_one(message_obj.dict())
        
        # Update session activity
        await db.chat_sessions.update_one(
            {"session_id": input.session_id},
            {
                "$set": {"last_active": datetime.utcnow()},
                "$inc": {"total_messages": 1}
            }
        )
        
        # Award XP for engagement
        if student_profile:
            xp_earned = 5  # Base XP for asking questions
            await db.student_profiles.update_one(
                {"student_id": input.student_id},
                {
                    "$inc": {"total_xp": xp_earned},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
        
        return message_obj
        
    except Exception as e:
        logger.error(f"Error in chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history/{student_id}")
async def get_chat_history_by_student(student_id: str, subject: Optional[Subject] = None):
    """Get chat history for a student, optionally filtered by subject"""
    query = {"student_id": student_id}
    if subject:
        query["subject"] = subject
        
    messages = await db.chat_messages.find(query).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**message) for message in messages]

@api_router.get("/chat/sessions/{student_id}")
async def get_student_sessions(student_id: str):
    """Get all chat sessions for a student"""
    sessions = await db.chat_sessions.find({"student_id": student_id}).sort("last_active", -1).to_list(100)
    return [ChatSession(**session) for session in sessions]

# Practice Test Routes
@api_router.post("/practice/generate")
async def generate_practice_test(subject: Subject, topic: str, difficulty: DifficultyLevel, count: int = 5):
    """Generate practice questions"""
    try:
        questions_text = await practice_bot.generate_practice_questions(subject, topic, difficulty, count)
        # Here you would parse the JSON and save to database
        return {"message": "Practice test generated", "questions": questions_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating practice test: {str(e)}")

# Mindfulness Routes
@api_router.post("/mindfulness/session")
async def start_mindfulness_session(input: dict):
    """Start a mindfulness session"""
    session = MindfulnessActivity(
        student_id=input["student_id"],
        activity_type=input["activity_type"],
        duration=input["duration"]
    )
    await db.mindfulness_activities.insert_one(session.dict())
    return session

@api_router.get("/mindfulness/activities/{student_id}")
async def get_mindfulness_history(student_id: str):
    """Get mindfulness activity history"""
    activities = await db.mindfulness_activities.find({"student_id": student_id}).sort("completed_at", -1).to_list(50)
    return [MindfulnessActivity(**activity) for activity in activities]

# Dashboard Routes
@api_router.get("/dashboard/{student_id}")
async def get_student_dashboard(student_id: str):
    """Get comprehensive dashboard data for a student"""
    profile = await db.student_profiles.find_one({"student_id": student_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get recent activity
    recent_messages = await db.chat_messages.find({"student_id": student_id}).sort("timestamp", -1).limit(10).to_list(10)
    recent_sessions = await db.chat_sessions.find({"student_id": student_id}).sort("last_active", -1).limit(5).to_list(5)
    
    # Calculate study stats
    total_messages = await db.chat_messages.count_documents({"student_id": student_id})
    subjects_studied = await db.chat_messages.distinct("subject", {"student_id": student_id})
    
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
        "subjects_progress": subjects_studied
    }

# Health check routes
@api_router.get("/")
async def root():
    return {"message": "Project K - AI Educational Chatbot API v2.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "2.0"}

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
