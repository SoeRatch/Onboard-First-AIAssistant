#!/usr/bin/env python3
"""
Tests for Email and Phone Validation
=====================================
Tests the PII module's validation functions.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from pii import validate_email, validate_phone, mask_pii, extract_email, extract_phone


class TestEmailValidation:
    """Test email validation function."""
    
    def test_valid_emails(self):
        """Test that valid emails pass validation."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+filter@gmail.com",
            "name@sub.domain.co.uk",
            "first.last@company.io",
            "user123@test.gov",
        ]
        for email in valid_emails:
            assert validate_email(email), f"Should be valid: {email}"
    
    def test_invalid_emails(self):
        """Test that invalid emails fail validation."""
        invalid_emails = [
            "",
            "not-an-email",
            "@nodomain.com",
            "noat.domain.com",
            "spaces in@email.com",
            "missing@tld",
            "double@@at.com",
            None,
        ]
        for email in invalid_emails:
            if email is not None:
                assert not validate_email(email), f"Should be invalid: {email}"
    
    def test_email_edge_cases(self):
        """Test edge cases for email validation."""
        # Very long email
        long_email = "a" * 100 + "@example.com"
        assert validate_email(long_email)
        
        # Single character local part
        assert validate_email("a@b.co")


class TestPhoneValidation:
    """Test phone number validation function."""
    
    def test_valid_phones(self):
        """Test that valid phone numbers pass validation."""
        valid_phones = [
            "1234567890",
            "123-456-7890",
            "(123) 456-7890",
            "123.456.7890",
            "+1 123 456 7890",
            "11234567890",  # With country code
        ]
        for phone in valid_phones:
            assert validate_phone(phone), f"Should be valid: {phone}"
    
    def test_invalid_phones(self):
        """Test that invalid phone numbers fail validation."""
        invalid_phones = [
            "",
            "123",
            "12345",
            "123456789",  # 9 digits
            "123456789012",  # 12 digits
            "abcdefghij",
            "123-abc-7890",
            None,
        ]
        for phone in invalid_phones:
            if phone is not None:
                assert not validate_phone(phone), f"Should be invalid: {phone}"
    
    def test_phone_with_formatting(self):
        """Test phones with various formatting."""
        formatted_phones = [
            "(555) 123-4567",
            "555.123.4567",
            "555 123 4567",
            "+1-555-123-4567",
        ]
        for phone in formatted_phones:
            assert validate_phone(phone), f"Should handle formatting: {phone}"


class TestPIIMasking:
    """Test PII masking functions."""
    
    def test_mask_email(self):
        """Test that emails are masked correctly."""
        text = "Contact me at john@example.com for details"
        masked, mapping = mask_pii(text)
        
        assert "john@example.com" not in masked
        assert "[EMAIL_REDACTED]" in masked
        assert len(mapping) == 1
    
    def test_mask_phone(self):
        """Test that phone numbers are masked correctly."""
        text = "Call me at 123-456-7890"
        masked, mapping = mask_pii(text)
        
        assert "123-456-7890" not in masked
        assert "[PHONE_REDACTED]" in masked
        assert len(mapping) == 1
    
    def test_mask_multiple_pii(self):
        """Test masking multiple PII in one text."""
        text = "Email: test@test.com, Phone: (555) 123-4567"
        masked, mapping = mask_pii(text)
        
        assert "test@test.com" not in masked
        assert "(555) 123-4567" not in masked
        assert len(mapping) == 2
    
    def test_no_pii(self):
        """Test text with no PII."""
        text = "Hello, how can I help you today?"
        masked, mapping = mask_pii(text)
        
        assert masked == text
        assert len(mapping) == 0


class TestPIIExtraction:
    """Test PII extraction functions."""
    
    def test_extract_email(self):
        """Test email extraction from text."""
        text = "My email is john@example.com, please contact me"
        email = extract_email(text)
        assert email == "john@example.com"
    
    def test_extract_phone(self):
        """Test phone extraction from text."""
        text = "You can reach me at 555-123-4567"
        phone = extract_phone(text)
        assert phone == "555-123-4567"
    
    def test_no_email_found(self):
        """Test when no email is in text."""
        text = "No email here"
        assert extract_email(text) is None
    
    def test_no_phone_found(self):
        """Test when no phone is in text."""
        text = "No phone number here"
        assert extract_phone(text) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
