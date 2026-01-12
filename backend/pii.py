#!/usr/bin/env python3
"""
PII (Personally Identifiable Information) Handler
===================================================
Detects and masks PII before sending to external APIs.
"""

import re
from typing import Tuple

# Regex patterns for PII detection
PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone": re.compile(r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'),
}

# Placeholders for masked content
PLACEHOLDERS = {
    "email": "[EMAIL_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "ssn": "[SSN_REDACTED]",
}

def extract_email(text: str) -> str | None:
    """Extract email from text if present."""
    match = PATTERNS["email"].search(text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str | None:
    """Extract phone number from text if present."""
    match = PATTERNS["phone"].search(text)
    return match.group(0) if match else None

def mask_pii(text: str) -> Tuple[str, dict]:
    """
    Mask PII in text before sending to LLM.
    
    Args:
        text: Input text that may contain PII
        
    Returns:
        Tuple of (masked_text, mapping) where mapping allows restoration
    """
    mapping = {}
    masked_text = text
    
    for pii_type, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        for i, match in enumerate(matches):
            placeholder = f"{PLACEHOLDERS[pii_type]}_{i}"
            mapping[placeholder] = match
            masked_text = masked_text.replace(match, placeholder, 1)
    
    return masked_text, mapping


def unmask_pii(text: str, mapping: dict) -> str:
    """
    Restore original PII values in text (if needed).
    
    Args:
        text: Text with placeholders
        mapping: Mapping from mask_pii
        
    Returns:
        Text with restored PII values
    """
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    return bool(PATTERNS["email"].fullmatch(email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    Accepts various formats: (123) 456-7890, 123-456-7890, +1 123 456 7890, etc.
    """
    if not phone:
        return False
    # Remove common formatting characters for validation
    cleaned = re.sub(r'[\s\-\.\(\)\+]', '', phone)
    # Should be 10-11 digits (with optional country code)
    return bool(re.fullmatch(r'\d{10,11}', cleaned))


def contains_pii(text: str) -> bool:
    """Check if text contains any PII."""
    for pattern in PATTERNS.values():
        if pattern.search(text):
            return True
    return False
