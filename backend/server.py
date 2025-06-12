from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import google.generativeai as genai

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

# Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_message: str
    bot_response: str
    bot_type: str  # "central_brain", "math_bot", etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    difficulty_level: Optional[str] = None
    topic: Optional[str] = None

class ChatMessageCreate(BaseModel):
    session_id: str
    user_message: str

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    student_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_messages: int = 0
    current_subject: Optional[str] = None

class ChatSessionCreate(BaseModel):
    student_name: Optional[str] = None

# AI Chat Classes
class CentralBrainBot:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def analyze_and_route(self, message: str, session_id: str):
        """Analyze user message and determine which bot should handle it"""
        system_prompt = """You are the Central Brain of Project K, an AI educational tutor system. 
            Your job is to analyze student messages and determine which subject-specific bot should handle them.
            
            Available subjects: Math, Physics (coming soon), Chemistry (coming soon)
            
            Analyze the student's message and respond with:
            1. Subject: [Math/Physics/Chemistry/General]
            2. Topic: [specific topic if identifiable]
            3. Difficulty: [Elementary/Middle/High School/Advanced]
            4. Urgency: [Low/Medium/High] (based on keywords like "test tomorrow", "homework due", etc.)
            5. Mood: [Confused/Frustrated/Excited/Neutral] (based on tone)
            
            If it's a math question, respond with: ROUTE_TO: math_bot
            If it's general conversation or non-subject specific, handle it yourself with encouragement.
            
            Always be encouraging and supportive. Remember, you're helping middle and high school students."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[])
        
        response = await asyncio.to_thread(
            chat.send_message,
            f"System: {system_prompt}\n\nUser: {message}"
        )
        
        return response.text

class MathBot:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
    async def teach_math(self, message: str, session_id: str):
        """Teach math using Socratic method with fallback to direct explanations"""
        system_prompt = """You are the Math Bot of Project K, a specialized AI tutor for middle and high school mathematics.

            Teaching Philosophy:
            1. Use the Socratic method - ask guiding questions and give hints rather than direct answers
            2. If a student seems really stuck after 2-3 attempts, provide direct explanation
            3. Break complex problems into smaller, manageable steps
            4. Use real-world examples when possible
            5. Always encourage and build confidence
            
            Topics you cover:
            - Algebra (linear equations, quadratics, polynomials)
            - Geometry (area, perimeter, angles, triangles)
            - Trigonometry (basic ratios, unit circle)
            - Pre-Calculus (functions, limits)
            - Statistics (mean, median, mode, probability)
            
            Response format:
            - Start with a brief encouraging comment
            - Ask a guiding question or give a hint
            - If they're stuck, provide a step-by-step explanation
            - End with a question to check understanding
            
            Remember: You're helping students LEARN, not just getting answers. Make math feel approachable and fun!"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[])
        
        response = await asyncio.to_thread(
            chat.send_message,
            f"System: {system_prompt}\n\nUser: {message}"
        )
        
        return response.text

# Initialize bots
central_brain = CentralBrainBot()
math_bot = MathBot()

# Routes
@api_router.post("/chat/session", response_model=ChatSession)
async def create_chat_session(input: ChatSessionCreate):
    """Create a new chat session for a student"""
    session_dict = input.dict()
    session_id = str(uuid.uuid4())
    session_dict['session_id'] = session_id
    session_obj = ChatSession(**session_dict)
    await db.chat_sessions.insert_one(session_obj.dict())
    return session_obj

@api_router.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get chat session details"""
    session = await db.chat_sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSession(**session)

@api_router.post("/chat/message", response_model=ChatMessage)
async def send_chat_message(input: ChatMessageCreate):
    """Send a message and get AI response"""
    try:
        # First, let the central brain analyze the message
        central_response = await central_brain.analyze_and_route(input.user_message, input.session_id)
        
        # Determine which bot should handle this
        if "ROUTE_TO: math_bot" in central_response:
            # Route to math bot
            bot_response = await math_bot.teach_math(input.user_message, input.session_id)
            bot_type = "math_bot"
        else:
            # Handle with central brain
            bot_response = central_response
            bot_type = "central_brain"
        
        # Create and save the message
        message_obj = ChatMessage(
            session_id=input.session_id,
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
        
        return message_obj
        
    except Exception as e:
        logger.error(f"Error in chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**message) for message in messages]

@api_router.get("/chat/sessions", response_model=List[ChatSession])
async def get_all_sessions():
    """Get all chat sessions"""
    sessions = await db.chat_sessions.find().sort("last_active", -1).to_list(100)
    return [ChatSession(**session) for session in sessions]

# Welcome and quick actions
@api_router.get("/welcome/{session_id}")
async def get_welcome_message(session_id: str):
    """Get personalized welcome message"""
    # Simple welcome for now - can be enhanced with mood detection later
    return {
        "message": "👋 Welcome to Project K! I'm your AI tutor, ready to help you learn and grow. What would you like to study today?",
        "quick_actions": [
            {"text": "Help with Math", "action": "math_help"},
            {"text": "Start Studying", "action": "study_now"},
            {"text": "Review Previous Topics", "action": "review"},
            {"text": "Take a Practice Quiz", "action": "quiz"}
        ]
    }

# Health check routes
@api_router.get("/")
async def root():
    return {"message": "Project K - AI Educational Chatbot API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

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
