#!/usr/bin/env python3
"""
Onboarding Endpoint
====================
Handles user onboarding - validates and stores user information locally.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from backend.pii import validate_email, validate_phone

from dotenv import load_dotenv
load_dotenv()
COMPANY_NAME = os.getenv('COMPANY_NAME')

# Paths
BACKEND_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
USERS_FILE = DATA_DIR / "users.json"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"

router = APIRouter()

def ensure_data_files():
    """Ensure data files exist."""
    DATA_DIR.mkdir(exist_ok=True)
    
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]", encoding="utf-8")
    
    if not CHAT_HISTORY_FILE.exists():
        CHAT_HISTORY_FILE.write_text("{}", encoding="utf-8")


class OnboardingRequest(BaseModel):
    """Onboarding request with user details."""
    name: str
    email: str
    phone: str
    session_id: str
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be less than 100 characters")
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        v = v.strip().lower()
        if not validate_email(v):
            raise ValueError("Invalid email format")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone_field(cls, v: str) -> str:
        v = v.strip()
        if not validate_phone(v):
            raise ValueError("Invalid phone format. Use format: (123) 456-7890 or 123-456-7890")
        return v


class OnboardingResponse(BaseModel):
    """Response after successful onboarding."""
    success: bool
    message: str
    user_id: str


class ValidationErrorResponse(BaseModel):
    """Response when validation fails."""
    success: bool = False
    errors: dict[str, str]


def load_users() -> list[dict]:
    """Load existing users from file."""
    ensure_data_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return []


def save_users(users: list[dict]):
    """Save users to file."""
    ensure_data_files()
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def generate_user_id(email: str) -> str:
    """Generate a simple user ID from email."""
    import hashlib
    return hashlib.md5(email.encode()).hexdigest()[:12]


@router.post("/onboard")
async def onboard_user(request: OnboardingRequest):
    """
    Complete user onboarding.
    
    Validates and stores user information locally.
    Returns user ID on success.
    """
    try:
        # Load existing users
        users = load_users()
        
        # Check if email already registered
        existing = next((u for u in users if u["email"] == request.email), None)
        if existing:
            return OnboardingResponse(
                success=True,
                message=f"Welcome back, {existing['name']}! You're already registered.",
                user_id=existing["id"]
            )
        
        # Create new user
        user_id = generate_user_id(request.email)
        new_user = {
            "id": user_id,
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "session_id": request.session_id,
            "created_at": datetime.now().isoformat(),
            "source": "chat_onboarding"
        }
        
        users.append(new_user)
        save_users(users)
        
        return OnboardingResponse(
            success=True,
            message=f"Welcome to {COMPANY_NAME}, {request.name}! Your onboarding is complete.",
            user_id=user_id
        )
        
    except ValueError as e:
        # Validation errors from Pydantic
        raise HTTPException(status_code=422, detail=str(e))


class ChatHistoryEntry(BaseModel):
    """A single chat message entry."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


@router.post("/chat-history/{session_id}")
async def save_chat_history(session_id: str, messages: list[ChatHistoryEntry]):
    """Save chat history for a session."""
    ensure_data_files()
    
    try:
        history = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
    except:
        history = {}
    
    history[session_id] = [msg.model_dump() for msg in messages]
    
    CHAT_HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
    
    return {"success": True, "session_id": session_id}


@router.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    ensure_data_files()
    
    try:
        history = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
        return {"messages": history.get(session_id, [])}
    except:
        return {"messages": []}


@router.get("/users")
async def list_users():
    """List all onboarded users (for demo purposes)."""
    users = load_users()
    # Return sanitized list (no full email/phone)
    return {
        "count": len(users),
        "users": [
            {
                "id": u["id"],
                "name": u["name"],
                "email": u["email"][:3] + "***@" + u["email"].split("@")[1],
                "created_at": u["created_at"]
            }
            for u in users
        ]
    }
