#!/usr/bin/env python3
"""
Tests for Onboarding Nudge Behavior
====================================
Tests that the chat assistant nudges users toward onboarding completion
without being annoying.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from backend.routers.chat import should_nudge_onboarding, get_nudge_message, OnboardingState


class TestNudgeLogic:
    """Test the nudge decision logic."""
    
    def test_no_nudge_when_complete(self):
        """Test that completed onboarding never triggers nudge."""
        onboarding = OnboardingState(
            name="John",
            email="john@example.com",
            phone="123-456-7890",
            completed=True
        )
        
        # Should not nudge regardless of message count
        for count in [1, 3, 5, 10, 20]:
            assert not should_nudge_onboarding(count, onboarding)
    
    def test_nudge_at_message_3(self):
        """Test that first nudge happens at message 3."""
        onboarding = OnboardingState()  # Empty
        
        # No nudge for first 2 messages
        assert not should_nudge_onboarding(1, onboarding)
        assert not should_nudge_onboarding(2, onboarding)
        
        # Nudge at message 3
        assert should_nudge_onboarding(3, onboarding)
    
    def test_nudge_frequency(self):
        """Test that nudges happen every 4 messages after the first."""
        onboarding = OnboardingState()  # Empty
        
        # After message 3, should nudge every 4 messages
        # Message 3: nudge, then 7, 11, 15, etc.
        expected_nudges = [3, 7, 11, 15, 19]
        expected_no_nudges = [1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14]
        
        for count in expected_nudges:
            assert should_nudge_onboarding(count, onboarding), f"Should nudge at {count}"
        
        for count in expected_no_nudges:
            assert not should_nudge_onboarding(count, onboarding), f"Should NOT nudge at {count}"
    
    def test_max_one_nudge_per_4_messages(self):
        """Test that we don't over-nudge."""
        onboarding = OnboardingState()
        
        # Count nudges in first 20 messages
        nudge_count = sum(1 for i in range(1, 21) if should_nudge_onboarding(i, onboarding))
        
        # Should be at most 5 nudges in 20 messages (roughly 1 per 4)
        assert nudge_count <= 5
        assert nudge_count >= 1  # At least one nudge should happen


class TestNudgeMessages:
    """Test the nudge message content."""
    
    def test_initial_nudge_message(self):
        """Test message when no info provided yet."""
        onboarding = OnboardingState()
        message = get_nudge_message(onboarding)
        
        assert len(message) > 0
        # Should mention name, email, phone
        assert "name" in message.lower() or "email" in message.lower() or "phone" in message.lower()
    
    def test_partial_nudge_for_name_only(self):
        """Test message when only name is provided."""
        onboarding = OnboardingState(name="John")
        message = get_nudge_message(onboarding)
        
        # Should thank them for name and ask for email
        assert "john" in message.lower() or "email" in message.lower()
    
    def test_partial_nudge_for_name_and_email(self):
        """Test message when name and email provided."""
        onboarding = OnboardingState(name="John", email="john@test.com")
        message = get_nudge_message(onboarding)
        
        # Should ask for phone
        assert "phone" in message.lower()
    
    def test_no_nudge_message_when_complete(self):
        """Test that completed onboarding returns empty message."""
        onboarding = OnboardingState(
            name="John",
            email="john@example.com",
            phone="123-456-7890",
            completed=True
        )
        message = get_nudge_message(onboarding)
        
        # Should return empty string
        assert message == ""
    
    def test_nudge_message_is_gentle(self):
        """Test that nudge messages are not aggressive."""
        onboarding = OnboardingState()
        message = get_nudge_message(onboarding)
        
        # Should use gentle language
        gentle_indicators = ["by the way", "would you like", "when you're ready", "if you'd like"]
        has_gentle_tone = any(indicator in message.lower() for indicator in gentle_indicators)
        
        assert has_gentle_tone or "💡" in message  # Emoji indicates gentle suggestion


class TestNudgeIntegration:
    """Integration tests for nudge behavior in chat flow."""
    
    def test_nudge_respects_user_progress(self):
        """Test that nudge content changes as user provides info."""
        states = [
            OnboardingState(),
            OnboardingState(name="John"),
            OnboardingState(name="John", email="john@test.com"),
            OnboardingState(name="John", email="john@test.com", phone="123-456-7890", completed=True),
        ]
        
        messages = [get_nudge_message(state) for state in states]
        
        # Each state should produce different message (or empty for complete)
        assert messages[0] != messages[1]  # Empty vs name only
        assert messages[1] != messages[2]  # Name only vs name+email
        assert messages[3] == ""  # Complete = no nudge


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
