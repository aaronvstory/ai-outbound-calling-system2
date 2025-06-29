# Implementation Plan - Detailed Technical Specifications

## Phase 1: Security & Code Quality Implementation

### 1.1 Environment Configuration System

#### Current Issues
- API keys hardcoded in `config.py`
- No environment separation (dev/staging/prod)
- Sensitive data in version control

#### Solution Implementation

**Environment Configuration (`config/settings.py`)**
```python
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    path: str
    backup_interval: int = 3600
    max_connections: int = 10

@dataclass
class SynthflowConfig:
    api_key: str
    base_url: str = "https://api.synthflow.ai/v2"
    timeout: int = 30
    retry_attempts: int = 3

@dataclass
class AppConfig:
    secret_key: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    log_level: str = "INFO"

class Settings:
    def __init__(self):
        self.database = DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "data/calls.db"),
            backup_interval=int(os.getenv("DB_BACKUP_INTERVAL", "3600")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10"))
        )
        
        self.synthflow = SynthflowConfig(
            api_key=self._get_required_env("SYNTHFLOW_API_KEY"),
            base_url=os.getenv("SYNTHFLOW_BASE_URL", "https://api.synthflow.ai/v2"),
            timeout=int(os.getenv("SYNTHFLOW_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("SYNTHFLOW_RETRY_ATTEMPTS", "3"))
        )
        
        self.app = AppConfig(
            secret_key=self._get_required_env("SECRET_KEY"),
            debug=os.getenv("DEBUG", "False").lower() == "true",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "5000")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

settings = Settings()
```

### 1.2 Modular Architecture Refactoring

#### Current Issues
- `app.py` contains 500+ lines with mixed concerns
- Database, API, and web logic intermingled
- Difficult to test and maintain

#### Solution: Clean Architecture Implementation

**Project Structure**
```
src/
├── api/
│   ├── __init__.py
│   ├── synthflow_client.py
│   └── exceptions.py
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── database.py
│   └── services.py
├── web/
│   ├── __init__.py
│   ├── routes.py
│   ├── websocket.py
│   └── middleware.py
├── utils/
│   ├── __init__.py
│   ├── logging.py
│   └── validators.py
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

**Core Models (`src/core/models.py`)**
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class CallStatus(Enum):
    PENDING = "pending"
    INITIATING = "initiating"
    DIALING = "dialing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    NO_ANSWER = "no_answer"
    BUSY = "busy"

@dataclass
class CallRequest:
    caller_name: str
    caller_phone: str
    phone_number: str
    account_action: str
    additional_info: str = ""
    
    def validate(self) -> None:
        """Validate call request data"""
        if not self.caller_name.strip():
            raise ValueError("Caller name is required")
        if not self.phone_number.strip():
            raise ValueError("Phone number is required")
        if not self.account_action.strip():
            raise ValueError("Account action is required")

@dataclass
class Call:
    id: str
    request: CallRequest
    status: CallStatus = CallStatus.PENDING
    synthflow_call_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    transcript: Optional[str] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Database Service (`src/core/database.py`)**
```python
import sqlite3
import threading
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import Call, CallStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseService:
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    caller_name TEXT NOT NULL,
                    caller_phone TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    account_action TEXT NOT NULL,
                    additional_info TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    synthflow_call_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration INTEGER,
                    transcript TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_caller_name ON calls(caller_name)")
    
    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
        else:
            self._local.connection.commit()
    
    def save_call(self, call: Call) -> bool:
        """Save call to database"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO calls (
                        id, caller_name, caller_phone, phone_number,
                        account_action, additional_info, status, synthflow_call_id,
                        created_at, completed_at, duration, transcript,
                        success, error_message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call.id, call.request.caller_name, call.request.caller_phone,
                    call.request.phone_number, call.request.account_action,
                    call.request.additional_info, call.status.value,
                    call.synthflow_call_id, call.created_at, call.completed_at,
                    call.duration, call.transcript, call.success,
                    call.error_message, json.dumps(call.metadata)
                ))
            logger.info(f"Saved call {call.id} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save call {call.id}: {e}")
            return False
    
    def get_call(self, call_id: str) -> Optional[Call]:
        """Get call by ID"""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM calls WHERE id = ?", (call_id,)
                ).fetchone()
                
                if row:
                    return self._row_to_call(row)
                return None
        except Exception as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            return None
    
    def get_calls(self, limit: int = 50, offset: int = 0, 
                  status_filter: Optional[CallStatus] = None) -> List[Call]:
        """Get calls with pagination and filtering"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM calls"
                params = []
                
                if status_filter:
                    query += " WHERE status = ?"
                    params.append(status_filter.value)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                rows = conn.execute(query, params).fetchall()
                return [self._row_to_call(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get calls: {e}")
            return []
    
    def update_call(self, call_id: str, updates: Dict[str, Any]) -> bool:
        """Update call with given changes"""
        try:
            if not updates:
                return True
            
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'status' and isinstance(value, CallStatus):
                    value = value.value
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(call_id)
            query = f"UPDATE calls SET {', '.join(set_clauses)} WHERE id = ?"
            
            with self._get_connection() as conn:
                conn.execute(query, values)
            
            logger.info(f"Updated call {call_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update call {call_id}: {e}")
            return False
    
    def _row_to_call(self, row: sqlite3.Row) -> Call:
        """Convert database row to Call object"""
        from .models import CallRequest
        import json
        
        request = CallRequest(
            caller_name=row['caller_name'],
            caller_phone=row['caller_phone'],
            phone_number=row['phone_number'],
            account_action=row['account_action'],
            additional_info=row['additional_info'] or ""
        )
        
        return Call(
            id=row['id'],
            request=request,
            status=CallStatus(row['status']),
            synthflow_call_id=row['synthflow_call_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            duration=row['duration'],
            transcript=row['transcript'],
            success=row['success'],
            error_message=row['error_message'],
            metadata=json.loads(row['metadata'] or '{}')
        )
```

### 1.3 Enhanced Error Handling & Logging

**Logging Configuration (`src/utils/logging.py`)**
```python
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure application logging"""
    
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Configure third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get logger for module"""
    return logging.getLogger(name)
```

**Custom Exceptions (`src/api/exceptions.py`)**
```python
class CallSystemException(Exception):
    """Base exception for call system"""
    pass

class SynthflowAPIException(CallSystemException):
    """Synthflow API related exceptions"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class ConfigurationException(CallSystemException):
    """Configuration related exceptions"""
    pass

class ValidationException(CallSystemException):
    """Data validation exceptions"""
    pass

class DatabaseException(CallSystemException):
    """Database operation exceptions"""
    pass
```

## Phase 2: Performance & Testing Implementation

### 2.1 Async Operations & Connection Pooling

**Async Synthflow Client (`src/api/synthflow_client.py`)**
```python
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from dataclasses import asdict

from ..core.models import Call, CallStatus
from ..config.settings import settings
from .exceptions import SynthflowAPIException
from ..utils.logging import get_logger

logger = get_logger(__name__)

class AsyncSynthflowClient:
    def __init__(self):
        self.base_url = settings.synthflow.base_url
        self.api_key = settings.synthflow.api_key
        self.timeout = settings.synthflow.timeout
        self.retry_attempts = settings.synthflow.retry_attempts
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if not self._session or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=timeout
            )
    
    async def create_call(self, call: Call) -> Dict[str, Any]:
        """Create call with Synthflow API"""
        await self._ensure_session()
        
        payload = {
            "model_id": settings.synthflow.default_assistant_id,
            "phone": call.request.phone_number,
            "name": call.request.caller_name,
            "prompt": self._build_prompt(call.request),
            "greeting": f"Hi, my name is {call.request.caller_name}, my phone number is {call.request.caller_phone}"
        }
        
        for attempt in range(self.retry_attempts):
            try:
                async with self._session.post(f"{self.base_url}/calls", json=payload) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    else:
                        raise SynthflowAPIException(
                            f"API call failed: {response.status}",
                            status_code=response.status,
                            response_data=response_data
                        )
            
            except aiohttp.ClientError as e:
                if attempt == self.retry_attempts - 1:
                    raise SynthflowAPIException(f"Connection error after {self.retry_attempts} attempts: {e}")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def get_call_status(self, synthflow_call_id: str) -> Dict[str, Any]:
        """Get call status from Synthflow"""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.base_url}/calls/{synthflow_call_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise SynthflowAPIException(
                        f"Failed to get call status: {response.status}",
                        status_code=response.status
                    )
        except aiohttp.ClientError as e:
            raise SynthflowAPIException(f"Connection error: {e}")
    
    def _build_prompt(self, request) -> str:
        """Build conversation prompt for the call"""
        return f"""You are calling customer support on behalf of {request.caller_name}.

CRITICAL INSTRUCTIONS:
1. IMMEDIATELY identify yourself: "Hello, my name is {request.caller_name}, and my phone number is {request.caller_phone}"
2. State your purpose clearly: "{request.account_action}"
3. Provide additional information when asked: {request.additional_info}
4. Be patient and polite with the support representative
5. Confirm when the requested action has been completed
6. Thank the representative before ending the call

CONVERSATION GOALS:
- Successfully complete: {request.account_action}
- Provide verification info as needed
- Get confirmation the action was performed
- Maintain professional, courteous tone throughout

Remember: You are the customer calling for support, so follow their verification procedures and be respectful."""
```

### 2.2 Comprehensive Test Suite

**Test Configuration (`tests/conftest.py`)**
```python
import pytest
import tempfile
import os
from pathlib import Path

from src.core.database import DatabaseService
from src.core.models import Call, CallRequest, CallStatus

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
```

**Unit Tests (`tests/unit/test_database.py`)**
```python
import pytest
from datetime import datetime

from src.core.models import CallStatus
from src.core.database import DatabaseService

class TestDatabaseService:
    def test_save_and_get_call(self, temp_db, sample_call):
        """Test saving and retrieving a call"""
        # Save call
        assert temp_db.save_call(sample_call) is True
        
        # Retrieve call
        retrieved_call = temp_db.get_call(sample_call.id)
        assert retrieved_call is not None
        assert retrieved_call.id == sample_call.id
        assert retrieved_call.request.caller_name == sample_call.request.caller_name
        assert retrieved_call.status == sample_call.status
    
    def test_update_call(self, temp_db, sample_call):
        """Test updating a call"""
        # Save initial call
        temp_db.save_call(sample_call)
        
        # Update call
        updates = {
            'status': CallStatus.COMPLETED,
            'success': True,
            'transcript': 'Test transcript'
        }
        assert temp_db.update_call(sample_call.id, updates) is True
        
        # Verify updates
        updated_call = temp_db.get_call(sample_call.id)
        assert updated_call.status == CallStatus.COMPLETED
        assert updated_call.success is True
        assert updated_call.transcript == 'Test transcript'
    
    def test_get_calls_with_filter(self, temp_db, sample_call):
        """Test getting calls with status filter"""
        # Save calls with different statuses
        call1 = sample_call
        call1.status = CallStatus.PENDING
        temp_db.save_call(call1)
        
        call2 = Call(id="test-call-456", request=sample_call.request, status=CallStatus.COMPLETED)
        temp_db.save_call(call2)
        
        # Test filter
        pending_calls = temp_db.get_calls(status_filter=CallStatus.PENDING)
        assert len(pending_calls) == 1
        assert pending_calls[0].status == CallStatus.PENDING
        
        completed_calls = temp_db.get_calls(status_filter=CallStatus.COMPLETED)
        assert len(completed_calls) == 1
        assert completed_calls[0].status == CallStatus.COMPLETED
```

**Integration Tests (`tests/integration/test_api.py`)**
```python
import pytest
from unittest.mock import AsyncMock, patch

from src.api.synthflow_client import AsyncSynthflowClient
from src.core.models import Call, CallRequest, CallStatus

class TestSynthflowIntegration:
    @pytest.mark.asyncio
    async def test_create_call_success(self, sample_call):
        """Test successful call creation"""
        mock_response = {
            'status': 'ok',
            'response': {
                'call_id': 'synthflow-123',
                'status': 'initiated'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            async with AsyncSynthflowClient() as client:
                result = await client.create_call(sample_call)
                
                assert result['status'] == 'ok'
                assert result['response']['call_id'] == 'synthflow-123'
    
    @pytest.mark.asyncio
    async def test_create_call_api_error(self, sample_call):
        """Test API error handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 400
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value={'error': 'Bad request'})
            
            async with AsyncSynthflowClient() as client:
                with pytest.raises(SynthflowAPIException) as exc_info:
                    await client.create_call(sample_call)
                
                assert exc_info.value.status_code == 400
```

## Phase 3: Advanced Features Implementation

### 3.1 Bulk Operations & Scheduling

**Call Scheduler Service (`src/core/scheduler.py`)**
```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .models import Call, CallRequest, CallStatus
from .database import DatabaseService
from ..api.synthflow_client import AsyncSynthflowClient
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ScheduledCall:
    call: Call
    scheduled_time: datetime
    retry_count: int = 0
    max_retries: int = 3

class CallScheduler:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.scheduled_calls: Dict[str, ScheduledCall] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the scheduler"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Call scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Call scheduler stopped")
    
    def schedule_call(self, call: Call, scheduled_time: datetime) -> bool:
        """Schedule a call for future execution"""
        try:
            scheduled_call = ScheduledCall(call=call, scheduled_time=scheduled_time)
            self.scheduled_calls[call.id] = scheduled_call
            
            # Save to database with scheduled status
            call.status = CallStatus.SCHEDULED
            call.metadata['scheduled_time'] = scheduled_time.isoformat()
            self.db_service.save_call(call)
            
            logger.info(f"Scheduled call {call.id} for {scheduled_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule call {call.id}: {e}")
            return False
    
    def schedule_bulk_calls(self, call_requests: List[CallRequest], 
                          scheduled_time: datetime, 
                          interval_minutes: int = 1) -> List[str]:
        """Schedule multiple calls with intervals"""
        scheduled_ids = []
        
        for i, request in enumerate(call_requests):
            call_time = scheduled_time + timedelta(minutes=i * interval_minutes)
            call = Call(
                id=f"bulk-{datetime.now().timestamp()}-{i}",
                request=request
            )
            
            if self.schedule_call(call, call_time):
                scheduled_ids.append(call.id)
        
        logger.info(f"Scheduled {len(scheduled_ids)} bulk calls")
        return scheduled_ids
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                current_time = datetime.now()
                calls_to_execute = []
                
                # Find calls ready for execution
                for call_id, scheduled_call in list(self.scheduled_calls.items()):
                    if scheduled_call.scheduled_time <= current_time:
                        calls_to_execute.append(scheduled_call)
                        del self.scheduled_calls[call_id]
                
                # Execute ready calls
                if calls_to_execute:
                    await self._execute_scheduled_calls(calls_to_execute)
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_scheduled_calls(self, scheduled_calls: List[ScheduledCall]):
        """Execute scheduled calls"""
        async with AsyncSynthflowClient() as client:
            tasks = []
            
            for scheduled_call in scheduled_calls:
                task = asyncio.create_task(
                    self._execute_single_call(client, scheduled_call)
                )
                tasks.append(task)
            
            # Execute calls concurrently (with reasonable limit)
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent calls
            
            async def limited_execution(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[limited_execution(task) for task in tasks],
                return_exceptions=True
            )
            
            logger.info(f"Executed {len(scheduled_calls)} scheduled calls")
    
    async def _execute_single_call(self, client: AsyncSynthflowClient, 
                                 scheduled_call: ScheduledCall):
        """Execute a single scheduled call"""
        call = scheduled_call.call
        
        try:
            # Update status to initiating
            call.status = CallStatus.INITIATING
            self.db_service.update_call(call.id, {'status': CallStatus.INITIATING})
            
            # Create call with Synthflow
            result = await client.create_call(call)
            
            if result.get('status') == 'ok':
                synthflow_call_id = result.get('response', {}).get('call_id')
                call.synthflow_call_id = synthflow_call_id
                call.status = CallStatus.DIALING
                
                self.db_service.update_call(call.id, {
                    'status': CallStatus.DIALING,
                    'synthflow_call_id': synthflow_call_id
                })
                
                logger.info(f"Successfully initiated scheduled call {call.id}")
            else:
                raise Exception(f"Synthflow API error: {result}")
                
        except Exception as e:
            logger.error(f"Failed to execute scheduled call {call.id}: {e}")
            
            # Handle retry logic
            if scheduled_call.retry_count < scheduled_call.max_retries:
                scheduled_call.retry_count += 1
                scheduled_call.scheduled_time = datetime.now() + timedelta(minutes=5)
                self.scheduled_calls[call.id] = scheduled_call
                logger.info(f"Rescheduled call {call.id} for retry {scheduled_call.retry_count}")
            else:
                call.status = CallStatus.FAILED
                call.error_message = f"Failed after {scheduled_call.max_retries} retries: {e}"
                self.db_service.update_call(call.id, {
                    'status': CallStatus.FAILED,
                    'error_message': call.error_message
                })
```

### 3.2 Analytics & Reporting System

**Analytics Service (`src/core/analytics.py`)**
```python
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from .database import DatabaseService
from .models import CallStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class CallMetrics:
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    average_duration: float
    total_duration: int

@dataclass
class TimeSeriesData:
    timestamp: datetime
    value: float
    label: str

class AnalyticsService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def get_call_metrics(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> CallMetrics:
        """Get overall call metrics for date range"""
        try:
            with self.db_service._get_connection() as conn:
                query = """
                    SELECT 
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_calls,
                        AVG(CASE WHEN duration IS NOT NULL THEN duration ELSE 0 END) as avg_duration,
                        SUM(CASE WHEN duration IS NOT NULL THEN duration ELSE 0 END) as total_duration
                    FROM calls
                """
                
                params = []
                if start_date or end_date:
                    conditions = []
                    if start_date:
                        conditions.append("created_at >= ?")
                        params.append(start_date.isoformat())
                    if end_date:
                        conditions.append("created_at <= ?")
                        params.append(end_date.isoformat())
                    query += " WHERE " + " AND ".join(conditions)
                
                result = conn.execute(query, params).fetchone()
                
                total_calls = result['total_calls'] or 0
                successful_calls = result['successful_calls'] or 0
                success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
                
                return CallMetrics(
                    total_calls=total_calls,
                    successful_calls=successful_calls,
                    failed_calls=result['failed_calls'] or 0,
                    success_rate=round(success_rate, 2),
                    average_duration=round(result['avg_duration'] or 0, 2),
                    total_duration=result['total_duration'] or 0
                )
                
        except Exception as e:
            logger.error(f"Error getting call metrics: {e}")
            return CallMetrics(0, 0, 0, 0.0, 0.0, 0)
    
    def get_success_rate_trend(self, days: int = 30) -> List[TimeSeriesData]:
        """Get success rate trend over time"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with self.db_service._get_connection() as conn:
                query = """
                    SELECT 
                        DATE(created_at) as call_date,
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
                    FROM calls
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY DATE(created_at)
                    ORDER BY call_date
                """
                
                results = conn.execute(query, [start_date.isoformat(), end_date.isoformat()]).fetchall()
                
                trend_data = []
                for row in results:
                    total = row['total_calls']
                    successful = row['successful_calls'] or 0
                    success_rate = (successful / total * 100) if total > 0 else 0
                    
                    trend_data.append(TimeSeriesData(
                        timestamp=datetime.fromisoformat(row['call_date']),
                        value=round(success_rate, 2),
                        label=f"{successful}/{total} calls"
                    ))
                
                return trend_data
                
        except Exception as e:
            logger.error(f"Error getting success rate trend: {e}")
            return []
    
    def get_call_volume_by_hour(self, days: int = 7) -> List[TimeSeriesData]:
        """Get call volume distribution by hour of day"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with self.db_service._get_connection() as conn:
                query = """
                    SELECT 
                        CAST(strftime('%H', created_at) AS INTEGER) as hour,
                        COUNT(*) as call_count
                    FROM calls
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY CAST(strftime('%H', created_at) AS INTEGER)
                    ORDER BY hour
                """
                
                results = conn.execute(query, [start_date.isoformat(), end_date.isoformat()]).fetchall()
                
                # Create 24-hour data (fill missing hours with 0)
                hourly_data = {i: 0 for i in range(24)}
                for row in results:
                    hourly_data[row['hour']] = row['call_count']
                
                return [
                    TimeSeriesData(
                        timestamp=datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0),
                        value=count,
                        label=f"{hour:02d}:00"
                    )
                    for hour, count in hourly_data.items()
                ]
                
        except Exception as e:
            logger.error(f"Error getting call volume by hour: {e}")
            return []
    
    def get_top_failure_reasons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common failure reasons"""
        try:
            with self.db_service._get_connection() as conn:
                query = """
                    SELECT 
                        error_message,
                        COUNT(*) as count,
                        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM calls WHERE status = 'failed'), 2) as percentage
                    FROM calls
                    WHERE status = 'failed' AND error_message IS NOT NULL
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT ?
                """
                
                results = conn.execute(query, [limit]).fetchall()
                
                return [
                    {
                        'reason': row['error_message'],
                        'count': row['count'],
                        'percentage': row['percentage']
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error getting failure reasons: {e}")
            return []
    
    def export_call_data(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        format: str = 'json') -> str:
        """Export call data in specified format"""
        try:
            calls = self.db_service.get_calls(limit=10000)  # Large limit for export
            
            if start_date or end_date:
                filtered_calls = []
                for call in calls:
                    if start_date and call.created_at < start_date:
                        continue
                    if end_date and call.created_at > end_date:
                        continue
                    filtered_calls.append(call)
                calls = filtered_calls
            
            if format.lower() == 'json':
                return self._export_as_json(calls)
            elif format.lower() == 'csv':
                return self._export_as_csv(calls)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting call data: {e}")
            return ""
    
    def _export_as_json(self, calls: List) -> str:
        """Export calls as JSON"""
        export_data = []
        
        for call in calls:
            export_data.append({
                'id': call.id,
                'caller_name': call.request.caller_name,
                'caller_phone': call.request.caller_phone,
                'phone_number': call.request.phone_number,
                'account_action': call.request.account_action,
                'additional_info': call.request.additional_info,
                'status': call.status.value,
                'created_at': call.created_at.isoformat(),
                'completed_at': call.completed_at.isoformat() if call.completed_at else None,
                'duration': call.duration,
                'success': call.success,
                'transcript': call.transcript,
                'error_message': call.error_message
            })
        
        return json.dumps(export_data, indent=2)
    
    def _export_as_csv(self, calls: List) -> str:
        """Export calls as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Caller Name', 'Caller Phone', 'Destination Phone',
            'Account Action', 'Additional Info', 'Status', 'Created At',
            'Completed At', 'Duration', 'Success', 'Error Message'
        ])
        
        # Write data
        for call in calls:
            writer.writerow([
                call.id,
                call.request.caller_name,
                call.request.caller_phone,
                call.request.phone_number,
                call.request.account_action,
                call.request.additional_info,
                call.status.value,
                call.created_at.isoformat(),
                call.completed_at.isoformat() if call.completed_at else '',
                call.duration or '',
                call.success or '',
                call.error_message or ''
            ])
        
        return output.getvalue()
```

This comprehensive implementation plan addresses all the major issues identified in the audit and provides a solid foundation for a production-ready system. The modular architecture, comprehensive testing, and advanced features will significantly improve the system's reliability, maintainability, and user experience.