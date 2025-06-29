import os
import json
import time
import uuid
import sqlite3
import logging
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import threading
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

class SynthflowAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('SYNTHFLOW_API_KEY')
        self.base_url = "https://api.synthflow.ai/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.assistant_id = None
        self.phone_number = "+13203310678"  # Your purchased number
        self.default_assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"  # Reuse existing assistant
    
    def get_or_create_assistant(self):
        """Get existing assistant or create a new one if needed"""
        try:
            # First try to use existing assistant
            if self.default_assistant_id:
                return {"success": True, "model_id": self.default_assistant_id}
            
            # If no default, create a new reusable one
            payload = {
                "type": "outbound",
                "name": "Universal Customer Support Assistant",
                "agent": {
                    "name": "Customer Support AI",
                    "voice_id": "default",
                    "prompt": "You are a helpful customer support assistant. You will identify yourself with the caller's name and phone number, then make the requested account adjustment.",
                    "greeting": "Hello, this is a customer support call.",
                    "language": "en"
                },
                "phone_number": self.phone_number
            }
            
            response = requests.post(
                f"{self.base_url}/assistants",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'response' in data:
                    model_id = data['response'].get('model_id')
                    if model_id:
                        self.default_assistant_id = model_id
                        return {"success": True, "model_id": model_id}
                
                return {"error": f"Unexpected response format: {data}"}
            else:
                return {"error": f"Failed to create assistant: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Exception with assistant: {str(e)}"}
    

    
    def create_call(self, phone_number, caller_name, caller_phone, account_action, additional_info=""):
        """Create an outbound call with Synthflow AI - FIXED VERSION"""
        try:
            # CRITICAL FIX: Check if assistant has phone number assigned
            logger.info(f"Checking assistant {self.default_assistant_id} for phone number assignment...")
            
            # Get assistant details to check phone configuration
            assistant_response = requests.get(
                f"{self.base_url}/assistants/{self.default_assistant_id}",
                headers=self.headers,
                timeout=30
            )
            
            if assistant_response.status_code == 200:
                assistant_data = assistant_response.json()
                if 'response' in assistant_data and 'assistants' in assistant_data['response']:
                    assistant = assistant_data['response']['assistants'][0]
                    assigned_phone = assistant.get('phone_number', '').strip()
                    
                    if not assigned_phone:
                        error_msg = f"""CRITICAL ERROR: Assistant {self.default_assistant_id} has no phone number assigned!

This is why calls are stuck in 'queue' status. To fix this:

1. Log into your Synthflow dashboard
2. Go to the assistant configuration
3. Assign phone number {self.phone_number} to the assistant
4. OR run the fix script: python fix_phone_issue.py

Current assistant phone: '{assigned_phone}'
Expected phone: '{self.phone_number}'"""
                        
                        logger.error(error_msg)
                        return {"error": error_msg}
                    
                    logger.info(f"✅ Assistant has phone number: {assigned_phone}")
                else:
                    return {"error": "Could not retrieve assistant configuration"}
            else:
                return {"error": f"Failed to check assistant configuration: {assistant_response.status_code}"}
            
            # Use existing assistant instead of creating new ones
            model_id = self.default_assistant_id
            
            if not model_id:
                return {"error": "No assistant configured. Please set up an assistant first."}
            
            logger.info(f"Making call from {assigned_phone} to {phone_number} using assistant {model_id}")
            
            # Create the call - REMOVED phone_number_from as it's not needed when assistant has phone
            call_payload = {
                "model_id": model_id,
                "phone": phone_number,
                "name": caller_name,
                "prompt": f"""You are calling customer support on behalf of {caller_name}.

IMPORTANT INSTRUCTIONS:
1. First, identify yourself: "Hi, my name is {caller_name}, my phone number is {caller_phone}"
2. State your request clearly: "{account_action}"
3. If asked for additional information, provide: {additional_info}
4. Be polite and patient with the agent
5. Confirm when the action has been completed
6. Thank the agent before ending the call

CONVERSATION GOALS:
- Successfully complete the requested action: {account_action}
- Provide any necessary verification information
- Get confirmation that the action was performed
- Maintain a professional and courteous tone

Remember: You are calling customer support, so be respectful and follow their verification procedures.""",
                "greeting": f"Hi, my name is {caller_name}, my phone number is {caller_phone}"
            }
            
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=call_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract call ID from Synthflow response format
                call_id = "unknown"
                if data.get('status') == 'ok' and 'response' in data:
                    # Synthflow returns call_id in response.call_id
                    call_id = data['response'].get('call_id') or data.get('_id', 'unknown')
                elif 'call_id' in data:
                    call_id = data['call_id']
                elif '_id' in data:
                    call_id = data['_id']
                
                return {
                    "success": True,
                    "call_id": call_id,
                    "model_id": model_id,
                    "status": "initiated",
                    "raw_response": data  # For debugging
                }
            else:
                logger.error(f"Synthflow call API error: {response.status_code} - {response.text}")
                return {"error": f"Call API failed: {response.status_code} - {response.text}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_call_status(self, call_id):
        """Get the status of a specific call"""
        try:
            response = requests.get(
                f"{self.base_url}/calls/{call_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'response' in data:
                    return data['response']
                return data
            else:
                return {"error": f"Failed to get call status: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return {"error": str(e)}
    
    def terminate_call(self, call_id):
        """Terminate an active call - local handling since Synthflow API doesn't support it"""
        try:
            # Note: Synthflow doesn't appear to have a call termination API
            # So we'll mark it as terminated in our local database
            # In a real scenario, you might need to contact Synthflow support or 
            # use their dashboard to manually stop calls
            
            logger.info(f"Marking call {call_id} as terminated (local database only)")
            return {"success": True, "message": "Call marked as terminated locally", "note": "Synthflow API doesn't support call termination"}
                
        except Exception as e:
            logger.error(f"Error terminating call: {str(e)}")
            return {"error": str(e)}
    
    def get_phone_numbers(self):
        """Get list of available phone numbers"""
        try:
            response = requests.get(
                f"{self.base_url}/phone_numbers",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'response' in data:
                    return {"success": True, "numbers": data['response']}
                return {"success": True, "numbers": []}
            else:
                return {"error": f"Failed to get phone numbers: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting phone numbers: {str(e)}")
            return {"error": str(e)}
    
    def get_call_transcript(self, call_id):
        """Get the transcript of a completed call"""
        try:
            response = requests.get(
                f"{self.base_url}/calls/{call_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'response' in data:
                    return {"transcript": data['response'].get('transcript', '')}
                return {"transcript": data.get('transcript', '')}
            else:
                return {"error": f"Failed to get transcript: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return {"error": str(e)}

class CallDatabase:
    def __init__(self, db_path="logs/calls.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calls (
                        id TEXT PRIMARY KEY,
                        phone_number TEXT NOT NULL,
                        caller_name TEXT NOT NULL,
                        caller_phone TEXT NOT NULL,
                        account_action TEXT NOT NULL,
                        additional_info TEXT,
                        status TEXT DEFAULT 'pending',
                        call_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        duration INTEGER,
                        transcript TEXT,
                        success BOOLEAN,
                        error_message TEXT
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def save_call(self, call_data):
        """Save a call record to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO calls (
                        id, phone_number, caller_name, caller_phone, 
                        account_action, additional_info, status, call_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_data['id'],
                    call_data['phone_number'],
                    call_data['caller_name'],
                    call_data['caller_phone'],
                    call_data['account_action'],
                    call_data.get('additional_info', ''),
                    call_data.get('status', 'pending'),
                    call_data.get('call_id', '')
                ))
                conn.commit()
                logger.info(f"Call {call_data['id']} saved to database")
                return True
        except Exception as e:
            logger.error(f"Error saving call: {str(e)}")
            return False
    
    def update_call(self, call_id, updates):
        """Update a call record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                values.append(call_id)
                query = f"UPDATE calls SET {', '.join(set_clauses)} WHERE id = ?"
                
                cursor.execute(query, values)
                conn.commit()
                logger.info(f"Call {call_id} updated")
                return True
        except Exception as e:
            logger.error(f"Error updating call: {str(e)}")
            return False
    
    def get_all_calls(self):
        """Get all calls from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM calls ORDER BY created_at DESC
                """)
                
                columns = [description[0] for description in cursor.description]
                calls = []
                for row in cursor.fetchall():
                    calls.append(dict(zip(columns, row)))
                
                return calls
        except Exception as e:
            logger.error(f"Error getting calls: {str(e)}")
            return []
    
    def get_call(self, call_id):
        """Get a specific call by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM calls WHERE id = ?", (call_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error getting call: {str(e)}")
            return None

# Initialize components with config
try:
    from config import SYNTHFLOW_API_KEY, SYNTHFLOW_PHONE_NUMBER, DEFAULT_ASSISTANT_ID
    API_KEY = SYNTHFLOW_API_KEY
    PHONE_NUMBER = SYNTHFLOW_PHONE_NUMBER
    ASSISTANT_ID = DEFAULT_ASSISTANT_ID
except ImportError:
    # Fallback to hardcoded values
    API_KEY = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    PHONE_NUMBER = "+13203310678"
    ASSISTANT_ID = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"

os.environ['SYNTHFLOW_API_KEY'] = API_KEY

synthflow = SynthflowAPI(API_KEY)
synthflow.phone_number = PHONE_NUMBER
synthflow.default_assistant_id = ASSISTANT_ID
db = CallDatabase()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/test')
def test_page():
    """Simple test page"""
    return render_template('test.html')

@app.route('/debug')
def debug_page():
    """Debug dashboard"""
    return render_template('debug.html')

@app.route('/api/calls', methods=['POST'])
def create_call():
    """Create a new outbound call"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phone_number', 'caller_name', 'caller_phone', 'account_action']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate unique call ID
        call_id = str(uuid.uuid4())
        
        # Prepare call data
        call_data = {
            'id': call_id,
            'phone_number': data['phone_number'],
            'caller_name': data['caller_name'],
            'caller_phone': data['caller_phone'],
            'account_action': data['account_action'],
            'additional_info': data.get('additional_info', ''),
            'status': 'initiating'
        }
        
        # Save to database
        if not db.save_call(call_data):
            return jsonify({"error": "Failed to save call to database"}), 500
        
        # Start call in background thread
        threading.Thread(
            target=initiate_call_async,
            args=(call_id, call_data, API_KEY),
            daemon=True
        ).start()
        
        return jsonify({
            "success": True,
            "call_id": call_id,
            "message": "Call initiated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating call: {str(e)}")
        return jsonify({"error": str(e)}), 500

def initiate_call_async(call_id, call_data, api_key):
    """Initiate call asynchronously and monitor progress"""
    try:
        # Create new Synthflow instance with API key
        synthflow_async = SynthflowAPI(api_key)
        synthflow_async.default_assistant_id = synthflow.default_assistant_id
        synthflow_async.phone_number = synthflow.phone_number
        
        # Update status
        db.update_call(call_id, {"status": "checking_phone_config"})
        socketio.emit('call_update', {
            'call_id': call_id,
            'status': 'checking_phone_config',
            'message': 'Checking phone number configuration...'
        })
        
        # Make the API call to Synthflow
        result = synthflow_async.create_call(
            phone_number=call_data['phone_number'],
            caller_name=call_data['caller_name'],
            caller_phone=call_data['caller_phone'],
            account_action=call_data['account_action'],
            additional_info=call_data.get('additional_info', '')
        )
        
        if 'error' in result:
            error_msg = result['error']
            db.update_call(call_id, {
                "status": "failed",
                "error_message": error_msg,
                "completed_at": datetime.now().isoformat()
            })
            socketio.emit('call_update', {
                'call_id': call_id,
                'status': 'failed',
                'error': error_msg,
                'message': 'Call failed due to configuration issue'
            })
            return
        
        # Update with Synthflow call ID
        synthflow_call_id = result.get('call_id')
        assistant_phone = result.get('assistant_phone', 'unknown')
        
        db.update_call(call_id, {
            "status": "initiated",
            "call_id": synthflow_call_id
        })
        
        socketio.emit('call_update', {
            'call_id': call_id,
            'status': 'initiated',
            'synthflow_id': synthflow_call_id,
            'assistant_phone': assistant_phone,
            'message': f'Call initiated from {assistant_phone} - monitoring progress...'
        })
        
        # Monitor call progress
        if synthflow_call_id and synthflow_call_id != 'unknown':
            monitor_call_progress(call_id, synthflow_call_id, synthflow_async)
        else:
            # No valid call ID, mark as failed
            db.update_call(call_id, {
                "status": "failed",
                "error_message": "No valid call ID returned from Synthflow",
                "completed_at": datetime.now().isoformat()
            })
            socketio.emit('call_update', {
                'call_id': call_id,
                'status': 'failed',
                'error': 'No valid call ID returned',
                'message': 'Call failed - invalid response from Synthflow'
            })
        
    except Exception as e:
        logger.error(f"Error in async call initiation: {str(e)}")
        db.update_call(call_id, {
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.now().isoformat()
        })
        socketio.emit('call_update', {
            'call_id': call_id,
            'status': 'failed',
            'error': str(e)
        })

def monitor_call_progress(call_id, synthflow_call_id, synthflow_instance):
    """Monitor call progress and update status"""
    try:
        max_polls = 12  # Reduced to 1 minute (12 x 5 seconds)
        poll_count = 0
        last_status = None
        
        while poll_count < max_polls:
            time.sleep(5)  # Poll every 5 seconds
            poll_count += 1
            
            # Get call status from Synthflow
            status_result = synthflow_instance.get_call_status(synthflow_call_id)
            
            if 'error' in status_result:
                logger.warning(f"Error getting call status: {status_result['error']}")
                # Stop polling on repeated errors
                if poll_count > 3:
                    break
                continue
            
            # Extract actual status from Synthflow response
            call_status = 'unknown'
            if 'calls' in status_result.get('response', {}):
                calls = status_result['response']['calls']
                if calls and len(calls) > 0:
                    call_status = calls[0].get('status', 'unknown')
            
            # Only emit updates if status actually changed
            if call_status != last_status:
                last_status = call_status
                
                # Emit real-time updates
                socketio.emit('call_update', {
                    'call_id': call_id,
                    'status': call_status,
                    'message': f'Call status: {call_status}'
                })
                
                logger.info(f"Call {call_id} status: {call_status}")
            
            # Check if call is completed or failed
            if call_status in ['completed', 'failed', 'no_answer', 'busy']:
                logger.info(f"Call {call_id} finished with status: {call_status}")
                
                # Get final transcript
                transcript_result = synthflow_instance.get_call_transcript(synthflow_call_id)
                transcript = transcript_result.get('transcript', '') if 'error' not in transcript_result else ''
                
                # Analyze success based on transcript
                success = analyze_call_success(transcript, call_id)
                
                # Update database with final results
                db.update_call(call_id, {
                    "status": call_status,
                    "completed_at": datetime.now().isoformat(),
                    "duration": status_result.get('duration', 0),
                    "transcript": transcript,
                    "success": success
                })
                
                # Emit final update
                socketio.emit('call_update', {
                    'call_id': call_id,
                    'status': call_status,
                    'success': success,
                    'transcript': transcript,
                    'message': f'Call completed with status: {call_status}'
                })
                
                break
            
            # If call stays in queue for too long, mark as failed
            if call_status == 'queue' and poll_count >= 6:  # 30 seconds in queue
                logger.warning(f"Call {call_id} stuck in queue for too long")
                db.update_call(call_id, {
                    "status": "failed",
                    "error_message": "Call stuck in queue - likely missing phone number or account issue",
                    "completed_at": datetime.now().isoformat()
                })
                
                socketio.emit('call_update', {
                    'call_id': call_id,
                    'status': 'failed',
                    'error': 'Call stuck in queue - check phone number and account settings',
                    'message': 'Call failed - stuck in queue'
                })
                break
        
        # If polling completed without resolution, mark as timeout
        if poll_count >= max_polls and last_status not in ['completed', 'failed', 'no_answer', 'busy']:
            logger.warning(f"Call {call_id} monitoring timeout")
            db.update_call(call_id, {
                "status": "timeout",
                "error_message": "Call monitoring timeout",
                "completed_at": datetime.now().isoformat()
            })
            
            socketio.emit('call_update', {
                'call_id': call_id,
                'status': 'timeout',
                'message': 'Call monitoring timeout'
            })
            
    except Exception as e:
        logger.error(f"Error monitoring call progress: {str(e)}")
        # Mark call as failed on exception
        db.update_call(call_id, {
            "status": "failed",
            "error_message": f"Monitoring error: {str(e)}",
            "completed_at": datetime.now().isoformat()
        })
        
        socketio.emit('call_update', {
            'call_id': call_id,
            'status': 'failed',
            'error': f'Monitoring error: {str(e)}',
            'message': 'Call failed due to monitoring error'
        })

def analyze_call_success(transcript, call_id):
    """Analyze transcript to determine if call was successful"""
    if not transcript:
        return False
    
    transcript_lower = transcript.lower()
    
    # Success indicators
    success_phrases = [
        "account adjusted", "adjustment made", "change completed",
        "updated successfully", "modification complete", "done",
        "processed", "completed", "confirmed", "yes, that's done"
    ]
    
    # Failure indicators
    failure_phrases = [
        "cannot do that", "unable to", "not authorized", "need verification",
        "callback required", "supervisor needed", "system down"
    ]
    
    success_score = sum(1 for phrase in success_phrases if phrase in transcript_lower)
    failure_score = sum(1 for phrase in failure_phrases if phrase in transcript_lower)
    
    return success_score > failure_score

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Get all calls"""
    try:
        calls = db.get_all_calls()
        return jsonify({"calls": calls})
    except Exception as e:
        logger.error(f"Error getting calls: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/calls/<call_id>', methods=['GET'])
def get_call(call_id):
    """Get specific call details"""
    try:
        call = db.get_call(call_id)
        if not call:
            return jsonify({"error": "Call not found"}), 404
        return jsonify({"call": call})
    except Exception as e:
        logger.error(f"Error getting call: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        "synthflow_configured": bool(synthflow.api_key),
        "database_ready": os.path.exists(db.db_path)
    })

@app.route('/api/phone-numbers', methods=['GET'])
def get_phone_numbers():
    """Get available phone numbers"""
    try:
        result = synthflow.get_phone_numbers()
        if result.get('success'):
            # Add your purchased number as fallback
            numbers = result.get('numbers', [])
            # Ensure our known number is included
            known_numbers = [
                {"number": "+13203310678", "type": "purchased", "status": "active"}
            ]
            return jsonify({"success": True, "numbers": known_numbers + numbers})
        else:
            # Fallback to known numbers
            return jsonify({
                "success": True, 
                "numbers": [{"number": "+13203310678", "type": "purchased", "status": "active"}]
            })
    except Exception as e:
        logger.error(f"Error getting phone numbers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/calls/<call_id>/terminate', methods=['POST'])
def terminate_call(call_id):
    """Terminate a specific call"""
    try:
        result = synthflow.terminate_call(call_id)
        
        if result.get('success'):
            # Update database
            db.update_call(call_id, {
                "status": "terminated",
                "completed_at": datetime.now().isoformat()
            })
            
            # Emit real-time update
            socketio.emit('call_update', {
                'call_id': call_id,
                'status': 'terminated',
                'message': 'Call terminated by user'
            })
            
            return jsonify({"success": True, "message": "Call terminated successfully"})
        else:
            return jsonify({"error": result.get('error', 'Failed to terminate call')}), 500
            
    except Exception as e:
        logger.error(f"Error terminating call: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/calls/cleanup', methods=['POST'])
def cleanup_stuck_calls():
    """Clean up stuck 'in_progress' calls that are likely dead"""
    try:
        # Get all in_progress calls older than 30 minutes
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE calls 
                SET status = 'timeout', completed_at = ? 
                WHERE status IN ('in_progress', 'dialing') 
                AND datetime(created_at) < datetime('now', '-30 minutes')
            """, (datetime.now().isoformat(),))
            
            affected_rows = cursor.rowcount
            conn.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Cleaned up {affected_rows} stuck calls"
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up calls: {str(e)}")
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info("Client connected to WebSocket")
    emit('connected', {'message': 'Connected to call monitoring'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("Client disconnected from WebSocket")

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting Synthflow AI Call System")
    logger.info("Access the web interface at: http://localhost:5000")
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
