#!/usr/bin/env python3
"""
Tests for Fallback Behavior
============================
Tests that the system handles unknown questions and API failures gracefully.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from backend.fallback import get_fallback_response, FALLBACK_RESPONSES, SIMPLE_FAQ


class TestFallbackResponses:
    """Test fallback response generation."""
    
    def test_api_error_fallback(self):
        """Test response when API has an error."""
        response = get_fallback_response("System status check", "api_error")
        
        assert response is not None
        assert len(response) > 0
        # Should indicate connection issues
        assert "trouble" in response.lower() or "connection" in response.lower() or "try again" in response.lower()
    
    def test_rate_limited_fallback(self):
        """Test response when API is rate limited."""
        response = get_fallback_response("Status check", "rate_limited")
        
        assert response is not None
        assert "many requests" in response.lower() or "try again" in response.lower()
    
    def test_unknown_question_fallback(self):
        """Test response for unknown questions."""
        response = get_fallback_response("What is the weather like?", "unknown")
        
        assert response is not None
        # Should indicate lack of information
        assert "don't have" in response.lower() or "help you with" in response.lower()
    
    def test_greeting_detection(self):
        """Test that greetings are handled specially."""
        greetings = ["hello", "hi there", "hey", "good morning"]
        
        for greeting in greetings:
            response = get_fallback_response(greeting, "api_error")
            # Should return a greeting response, not an error
            assert "welcome" in response.lower() or "hello" in response.lower() or "help" in response.lower()


class TestSimpleFAQ:
    """Test simple FAQ matching without LLM."""
    
    def test_services_keyword(self):
        """Test that 'services' keyword triggers FAQ response."""
        response = get_fallback_response("What services do you offer?", "api_error")
        
        # Should mention some services
        assert any(keyword in response.lower() for keyword in 
                   ["services", "tax", "business", "financial", "capital"])
    
    def test_tax_keyword(self):
        """Test that 'tax' keyword triggers relevant response."""
        response = get_fallback_response("Tell me about tax credits", "api_error")
        
        # Should mention tax-related content
        assert "tax" in response.lower() or "r&d" in response.lower() or "credit" in response.lower()
    
    def test_about_keyword(self):
        """Test that 'about' keyword triggers company info."""
        response = get_fallback_response("Tell me about the company", "api_error")
        
        # Should include company information
        assert "occams" in response.lower() or "advisory" in response.lower() or "global" in response.lower()


class TestSafeResponses:
    """Test that all fallback responses are safe and appropriate."""
    
    def test_no_hallucination(self):
        """Test that fallback responses don't make up information."""
        # For a random question, fallback should not pretend to know
        response = get_fallback_response("What is the CEO's favorite color?", "unknown")
        
        # Should not make up an answer
        assert "don't have" in response.lower() or "not sure" in response.lower() or "help you with" in response.lower()
    
    def test_fallback_suggests_alternatives(self):
        """Test that fallback responses suggest what the assistant CAN help with."""
        response = get_fallback_response("random nonsense question", "unknown")
        
        # Should suggest alternatives or redirect
        assert "help" in response.lower() or "services" in response.lower() or "occams" in response.lower()
    
    def test_all_canned_responses_exist(self):
        """Test that all required canned responses are defined."""
        required_keys = ["api_error", "rate_limited", "unknown_question", "greeting"]
        
        for key in required_keys:
            assert key in FALLBACK_RESPONSES
            assert len(FALLBACK_RESPONSES[key]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])