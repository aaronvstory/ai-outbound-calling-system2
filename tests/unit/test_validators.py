"""
Unit tests for validation utilities
"""
import pytest

from src.utils.validators import (
    validate_call_request,
    validate_phone_number,
    validate_email,
    sanitize_input
)

class TestCallRequestValidation:
    def test_valid_call_request(self):
        """Test validation of valid call request"""
        data = {
            'caller_name': 'John Doe',
            'caller_phone': '+1234567890',
            'phone_number': '+0987654321',
            'account_action': 'Test action',
            'additional_info': 'Additional info'
        }
        
        errors = validate_call_request(data)
        assert errors == []
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        data = {}
        
        errors = validate_call_request(data)
        assert len(errors) == 4
        assert 'caller_name is required' in errors
        assert 'caller_phone is required' in errors
        assert 'phone_number is required' in errors
        assert 'account_action is required' in errors
    
    def test_empty_required_fields(self):
        """Test validation with empty required fields"""
        data = {
            'caller_name': '',
            'caller_phone': '   ',
            'phone_number': '',
            'account_action': '   '
        }
        
        errors = validate_call_request(data)
        assert len(errors) == 4
    
    def test_invalid_phone_numbers(self):
        """Test validation with invalid phone numbers"""
        data = {
            'caller_name': 'John Doe',
            'caller_phone': 'invalid',
            'phone_number': '123',
            'account_action': 'Test action'
        }
        
        errors = validate_call_request(data)
        assert 'caller_phone must be a valid phone number' in errors
        assert 'phone_number must be a valid phone number' in errors
    
    def test_text_length_limits(self):
        """Test validation with text length limits"""
        data = {
            'caller_name': 'x' * 101,  # Too long
            'caller_phone': '+1234567890',
            'phone_number': '+0987654321',
            'account_action': 'x' * 1001,  # Too long
            'additional_info': 'x' * 2001  # Too long
        }
        
        errors = validate_call_request(data)
        assert 'caller_name must be less than 100 characters' in errors
        assert 'account_action must be less than 1000 characters' in errors
        assert 'additional_info must be less than 2000 characters' in errors

class TestPhoneNumberValidation:
    def test_valid_phone_numbers(self):
        """Test valid phone number formats"""
        valid_numbers = [
            '+1234567890',
            '1234567890',
            '+12345678901',
            '(123) 456-7890',
            '123-456-7890',
            '123.456.7890',
            '+1 (123) 456-7890'
        ]
        
        for number in valid_numbers:
            assert validate_phone_number(number), f"Should be valid: {number}"
    
    def test_invalid_phone_numbers(self):
        """Test invalid phone number formats"""
        invalid_numbers = [
            '',
            '123',
            '12345',
            'abc1234567',
            '+',
            '++1234567890',
            '123456789012345678'  # Too long
        ]
        
        for number in invalid_numbers:
            assert not validate_phone_number(number), f"Should be invalid: {number}"

class TestEmailValidation:
    def test_valid_emails(self):
        """Test valid email formats"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            assert validate_email(email), f"Should be valid: {email}"
    
    def test_invalid_emails(self):
        """Test invalid email formats"""
        invalid_emails = [
            '',
            'invalid',
            '@example.com',
            'user@',
            'user@domain',
            'user.domain.com',
            'user@domain.',
            'user name@domain.com'
        ]
        
        for email in invalid_emails:
            assert not validate_email(email), f"Should be invalid: {email}"

class TestInputSanitization:
    def test_sanitize_basic_text(self):
        """Test basic text sanitization"""
        text = "  Hello World  "
        result = sanitize_input(text)
        assert result == "Hello World"
    
    def test_sanitize_dangerous_characters(self):
        """Test removal of dangerous characters"""
        text = 'Hello <script>alert("xss")</script> World'
        result = sanitize_input(text)
        assert result == 'Hello scriptalert(xss)/script World'
    
    def test_sanitize_with_length_limit(self):
        """Test sanitization with length limit"""
        text = "This is a very long text that should be truncated"
        result = sanitize_input(text, max_length=20)
        assert result == "This is a very long "
        assert len(result) == 20
    
    def test_sanitize_empty_input(self):
        """Test sanitization of empty input"""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""
        assert sanitize_input("   ") == ""