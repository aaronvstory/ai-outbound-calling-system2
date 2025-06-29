"""
Unit tests for core models
"""
import pytest
from datetime import datetime

from src.core.models import CallRequest, Call, CallStatus

class TestCallRequest:
    def test_create_call_request(self):
        """Test creating a call request"""
        request = CallRequest(
            caller_name="John Doe",
            caller_phone="+1234567890",
            phone_number="+0987654321",
            account_action="Test action"
        )
        
        assert request.caller_name == "John Doe"
        assert request.caller_phone == "+1234567890"
        assert request.phone_number == "+0987654321"
        assert request.account_action == "Test action"
        assert request.additional_info == ""
    
    def test_validate_call_request_success(self):
        """Test successful validation"""
        request = CallRequest(
            caller_name="John Doe",
            caller_phone="+1234567890",
            phone_number="+0987654321",
            account_action="Test action"
        )
        
        # Should not raise exception
        request.validate()
    
    def test_validate_call_request_empty_name(self):
        """Test validation with empty name"""
        request = CallRequest(
            caller_name="",
            caller_phone="+1234567890",
            phone_number="+0987654321",
            account_action="Test action"
        )
        
        with pytest.raises(ValueError, match="Caller name is required"):
            request.validate()
    
    def test_validate_call_request_empty_phone(self):
        """Test validation with empty phone"""
        request = CallRequest(
            caller_name="John Doe",
            caller_phone="+1234567890",
            phone_number="",
            account_action="Test action"
        )
        
        with pytest.raises(ValueError, match="Phone number is required"):
            request.validate()
    
    def test_validate_call_request_empty_action(self):
        """Test validation with empty action"""
        request = CallRequest(
            caller_name="John Doe",
            caller_phone="+1234567890",
            phone_number="+0987654321",
            account_action=""
        )
        
        with pytest.raises(ValueError, match="Account action is required"):
            request.validate()

class TestCall:
    def test_create_call(self, sample_call_request):
        """Test creating a call"""
        call = Call(
            id="test-123",
            request=sample_call_request
        )
        
        assert call.id == "test-123"
        assert call.request == sample_call_request
        assert call.status == CallStatus.PENDING
        assert call.synthflow_call_id is None
        assert isinstance(call.created_at, datetime)
        assert call.completed_at is None
        assert call.duration is None
        assert call.transcript is None
        assert call.success is None
        assert call.error_message is None
        assert call.metadata == {}
    
    def test_call_status_enum(self):
        """Test call status enum values"""
        assert CallStatus.PENDING.value == "pending"
        assert CallStatus.INITIATING.value == "initiating"
        assert CallStatus.DIALING.value == "dialing"
        assert CallStatus.IN_PROGRESS.value == "in_progress"
        assert CallStatus.COMPLETED.value == "completed"
        assert CallStatus.FAILED.value == "failed"
        assert CallStatus.TERMINATED.value == "terminated"
        assert CallStatus.NO_ANSWER.value == "no_answer"
        assert CallStatus.BUSY.value == "busy"