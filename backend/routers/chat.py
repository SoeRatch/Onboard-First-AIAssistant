#!/usr/bin/env python3
"""
Chat Endpoint
==============
Handles chat messages with RAG-based responses and onboarding nudges.
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.pii import extract_email, extract_phone, mask_pii
from backend.fallback import get_fallback_response

router = APIRouter()

class OnboardingState(BaseModel):
    """Current onboarding state."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    completed: bool = False

def should_nudge_onboarding(message_count: int, onboarding: OnboardingState) -> bool:
    """
    Determine if we should nudge the user about onboarding.
    Strategy: Nudge once every 3-4 messages, but not if already complete.
    """
    if onboarding.completed:
        return False
    
    # Nudge on message 3, then every 4 messages after
    if message_count == 3:
        return True
    if message_count > 3 and (message_count - 3) % 4 == 0:
        return True
    
    return False

def get_nudge_message(onboarding: OnboardingState) -> str:
    """Get an appropriate nudge message based on onboarding state."""
    if not onboarding.name and not onboarding.email and not onboarding.phone:
        return (
            "\n\n💡 *By the way, if you'd like personalized assistance, "
            "I can help you get started with a quick onboarding - "
            "just share your name, email, and phone number when you're ready.*"
        )
    elif onboarding.name and not onboarding.email:
        return (
            f"\n\n💡 *Thanks for sharing your name, {onboarding.name}! "
            "Would you like to complete your profile with an email so we can "
            "provide more personalized assistance?*"
        )
    elif onboarding.name and onboarding.email and not onboarding.phone:
        return (
            "\n\n💡 *You're almost done with onboarding! "
            "Just need your phone number to complete your profile.*"
        )
    return ""



class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str
    session_id: str
    onboarding: OnboardingState = OnboardingState()
    message_count: int = 0  # Messages in this session

class ChatResponse(BaseModel):
    """Chat response to frontend."""
    response: str
    sources: list[str] = []  # URLs of sources used
    detected_info: dict = {}  # Any PII detected for onboarding
    should_nudge: bool = False

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, fast_request: Request):
    """
    Handle a chat message.
    
    Flow:
    1. Check for PII in message (for onboarding)
    2. Mask PII before processing
    3. Call RAGEngine for grounded answering
    4. Add nudge if appropriate
    """
    message = request.message.strip()
    if not message:
        # Raise 400 which means bad request
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Detect any PII for onboarding
    detected_info = {}
    email = extract_email(message)
    phone = extract_phone(message)
    
    if email:
        detected_info["email"] = email
    if phone:
        detected_info["phone"] = phone
    
    # Check for name (heuristic)
    name_patterns = ["i'm ", "i am ", "my name is ", "call me "]
    message_lower = message.lower()
    for pattern in name_patterns:
        if pattern in message_lower:
            idx = message_lower.find(pattern) + len(pattern)
            potential_name = message[idx:].split()[0].strip(".,!?")
            if potential_name and len(potential_name) > 1:
                detected_info["name"] = potential_name.capitalize()
                break
    
    # Mask PII before processing
    masked_message, pii_mapping = mask_pii(message)
    
    # Use the new hybrid RAG engine
    try:
        
        rag = fast_request.app.state.rag_engine
        result = rag.answer_query(masked_message)
        response_text = result["response"]
        sources = result["sources"]
    except Exception as e:
        print(f"Chat error: {e}")
        response_text = get_fallback_response(message, "api_error")
        sources = []
    
    # Check if we should add onboarding nudge
    should_nudge = should_nudge_onboarding(request.message_count, request.onboarding)
    if should_nudge:
        response_text += get_nudge_message(request.onboarding)
    
    return ChatResponse(
        response=response_text,
        sources=sources,
        detected_info=detected_info,
        should_nudge=should_nudge
    )
