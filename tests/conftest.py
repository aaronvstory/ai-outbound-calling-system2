"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import os
from pathlib import Path

from src.core.database import DatabaseService
from src.core.models import Call, CallRequest, CallStatus
from src.web.app import create_app

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_service = DatabaseService(db_path)
    yield db_service
    
    # Cleanup
    os.unlink(db_path)

@pytest.fixture
def sample_call_request():
    """Sample call request for testing"""
    return CallRequest(
        caller_name="John Doe",
        caller_phone="+1234567890",
        phone_number="+0987654321",
        account_action="Test account adjustment",
        additional_info="Account: 12345"
    )

@pytest.fixture
def sample_call(sample_call_request):
    """Sample call object for testing"""
    return Call(
        id="test-call-123",
        request=sample_call_request,
        status=CallStatus.PENDING
    )

@pytest.fixture
def app():
    """Create Flask app for testing"""
    config_override = {
        'TESTING': True,
        'DATABASE_PATH': ':memory:',
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config_override)
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()