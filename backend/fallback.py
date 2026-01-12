#!/usr/bin/env python3
"""
Fallback Handler
=================
Provides responses when OpenAI API is unavailable.
"""

import os
COMPANY_NAME = os.getenv("COMPANY_NAME")

# Canned responses for common scenarios
FALLBACK_RESPONSES = {
    "api_error": (
        "I'm having trouble connecting to my AI backend right now. "
        "You can still complete your onboarding using the form, "
        "or try again in a moment. Is there anything specific about "
        f"{COMPANY_NAME} I can help you with?"
    ),
    "rate_limited": (
        "I'm receiving many requests right now. Please try again in a moment. "
        "In the meantime, feel free to explore our services or complete your onboarding."
    ),
    "unknown_question": (
        "I don't have specific information about that topic. "
        f"I can help you with questions about {COMPANY_NAME}'s services, "
        "including tax credits, business incubation, capital markets, "
        "and financial technology solutions. What would you like to know?"
    ),
    "greeting": (
        f"Hello! Welcome to {COMPANY_NAME}. I'm here to help you learn about "
        "our services and assist with your onboarding. How can I help you today?"
    ),
    "onboarding_prompt": (
        "To get personalized assistance, I can help you complete a quick onboarding. "
        "Just share your name, email, and phone number when you're ready. "
        "Is there anything about our services you'd like to know first?"
    ),
}

# Simple keyword-based FAQ (used when API is down)
SIMPLE_FAQ = {
    "services": (
        f"{COMPANY_NAME} offers four main service pillars:\n"
        "1. **Business Services & Growth Incubation (BSGI)** - Help setting up and managing your business\n"
        "2. **Financial Technology & Payment Solutions (FTPS)** - Digital payment and fintech solutions\n"
        "3. **Capital Markets & Investment Banking (CMIB)** - Investment and capital services\n"
        "4. **Tax Credits** - R&D tax credits with carryforwards up to 20 years"
    ),
    "tax": (
        f"{COMPANY_NAME} helps businesses claim R&D tax credits. "
        "Benefits include offsetting future income tax with carryforwards up to 20 years. "
        "This is available across all industries, from software to retail."
    ),
    "about": (
        f"{COMPANY_NAME} is a Global Financing Advisory & Professional Services firm. "
        "They've been recognized by Fortune as one of America's Most Innovative Companies (2023) "
        "and listed in the Financial Times' Americas' Fastest-Growing Companies multiple times."
    ),
    "contact": (
        f"You can reach {COMPANY_NAME} through their website at occamsadvisory.com. "
        "They typically respond within 2-4 business hours. "
        "Would you like to complete onboarding to get personalized assistance?"
    ),
}


def get_fallback_response(
    query: str,
    error_type: str = "api_error"
) -> str:
    """
    Get a fallback response when AI is unavailable.
    
    Args:
        query: User's question
        error_type: Type of error (api_error, rate_limited, unknown)
        onboarding_complete: Whether user has completed onboarding
        
    Returns:
        Appropriate fallback response
    """
    query_lower = query.lower()
    
    # Check for greetings
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
    if any(g in query_lower for g in greetings):
        return FALLBACK_RESPONSES["greeting"]
    
    # Try to match FAQ keywords
    for keyword, response in SIMPLE_FAQ.items():
        if keyword in query_lower:
            return response
    
    # Return error-specific response
    if error_type == "rate_limited":
        return FALLBACK_RESPONSES["rate_limited"]
    elif error_type == "unknown":
        return FALLBACK_RESPONSES["unknown_question"]
    else:
        return FALLBACK_RESPONSES["api_error"]