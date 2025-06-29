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
        # Store phone number configurations
        self.phone_number = "+13203310678"  # The actual phone number
        self.phone_number_sid = None  # Will be retrieved/set later
        self.assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
    
    def get_assistant_phone_config(self):
        """Get the current phone configuration for the assistant"""
        try:
            response = requests.get(
                f"{self.base_url}/assistants/{self.assistant_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_data = data.get('response', {})
                
                # Handle the response structure - it's nested under assistants array
                if 'assistants' in assistant_data and assistant_data['assistants']:
                    assistant = assistant_data['assistants'][0]
                    phone_number = assistant.get('phone_number', '')
                    caller_id = assistant.get('caller_id_number', '')
                    
                    logger.info(f"Assistant phone config - Number: {phone_number}, Caller ID: {caller_id}")
                    
                    return {
                        "phone_number": phone_number,
                        "caller_id_number": caller_id,
                        "has_phone": bool(phone_number.strip())
                    }
                
                return {"error": "Assistant not found in response"}
            else:
                return {"error": f"Failed to get assistant: {response.status_code} - {response.text}"}
                
        except Exception as e:
            logger.error(f"Error getting assistant phone config: {str(e)}")
            return {"error": str(e)}
    
    def create_assistant_with_phone(self):
        """Create a new assistant with phone number properly configured"""
        try:
            payload = {
                "type": "outbound",
                "name": "Customer Support Assistant - With Phone",
                "phone_number": self.phone_number,  # Try assigning phone directly
                "agent": {
                    "name": "Customer Support AI",
                    "voice_id": "default",
                    "prompt": "You are a helpful customer support assistant calling on behalf of the caller. Always start by identifying yourself with the caller's name and phone number, then make the requested account adjustment politely and professionally.",
                    "greeting": "Hello, this is a customer support call.",
                    "language": "en"
                }
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
                    assistant_data = data['response']
                    model_id = assistant_data.get('model_id')
                    assigned_phone = assistant_data.get('phone_number', '')
                    
                    logger.info(f"Created assistant {model_id} with phone {assigned_phone}")
                    
                    if model_id:
                        # Update the class to use this new assistant
                        self.assistant_id = model_id
                        return {"success": True, "model_id": model_id, "phone_number": assigned_phone}
                
                return {"error": f"Unexpected response format: {data}"}
            else:
                logger.error(f"Assistant creation failed: {response.status_code} - {response.text}")
                return {"error": f"Failed to create assistant: {response.status_code} - {response.text}"}
                
        except Exception as e:
            logger.error(f"Exception creating assistant: {str(e)}")
            return {"error": f"Exception: {str(e)}"}
    
    def create_call(self, phone_number, caller_name, caller_phone, account_action, additional_info=""):
        """Create an outbound call with proper error handling for phone number issues"""
        try:
            # First, check if the assistant has a phone number configured
            phone_config = self.get_assistant_phone_config()
            
            if 'error' in phone_config:
                return {"error": f"Failed to check assistant configuration: {phone_config['error']}"}
            
            if not phone_config.get('has_phone'):
                logger.warning("Assistant has no phone number. Attempting to create new assistant with phone.")
                
                # Try to create a new assistant with phone number
                new_assistant = self.create_assistant_with_phone()
                if 'error' in new_assistant:
                    return {"error": f"Cannot make calls without phone number. Assistant creation failed: {new_assistant['error']}"}
                
                logger.info(f"Created new assistant with phone: {new_assistant}")
            
            # Build the dynamic prompt for this specific call
            dynamic_prompt = f"""You are calling customer support on behalf of {caller_name}.

CRITICAL INSTRUCTIONS:
1. IMMEDIATELY identify yourself: "Hello, my name is {caller_name}, and my phone number is {caller_phone}"
2. State your purpose clearly: "{account_action}"
3. Provide additional information when asked: {additional_info}
4. Be patient and polite with the support representative
5. Confirm when the requested action has been completed
6. Thank the representative before ending the call

IMPORTANT CONTEXT:
- You are calling FROM: {self.phone_number}
- You are calling TO: {phone_number}
- Caller you represent: {caller_name} ({caller_phone})
- Requested action: {account_action}

CONVERSATION GOALS:
- Successfully complete: {account_action}
- Provide verification info as needed
- Get confirmation the action was performed
- Maintain professional, courteous tone throughout

Remember: You are the customer calling for support, so follow their verification procedures and be respectful."""

            # Create the call payload - simplified based on API requirements
            call_payload = {
                "model_id": self.assistant_id,
                "phone": phone_number,
                "name": caller_name,
                "prompt": dynamic_prompt,
                "greeting": f"Hello, my name is {caller_name}, and my phone number is {caller_phone}"
            }
            
            logger.info(f"Creating call from assistant {self.assistant_id} to {phone_number}")
            logger.debug(f"Call payload: {json.dumps(call_payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=call_payload,
                timeout=30
            )
            
            logger.info(f"Call API response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                call_id = None
                if data.get('status') == 'ok' and 'response' in data:
                    call_id = data['response'].get('call_id')
                elif 'call_id' in data:
                    call_id = data['call_id']
                elif '_id' in data:
                    call_id = data['_id']
                
                if call_id:
                    return {
                        "success": True,
                        "call_id": call_id,
                        "model_id": self.assistant_id,
                        "status": "initiated",
                        "phone_config": phone_config,
                        "raw_response": data
                    }
                else:
                    return {"error": f"No call_id in response: {data}"}
            else:
                error_msg = f"Call creation failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Provide specific guidance based on error
                if "phone" in response.text.lower() and "number" in response.text.lower():
                    error_msg += "\n\nThis appears to be a phone number configuration issue. Please check:\n1. Phone number is purchased and active in Synthflow\n2. Assistant has phone number properly assigned\n3. Phone number format is correct"
                
                return {"error": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in create_call: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_call_status(self, call_id):
        """Get the status of a specific call with better error handling"""
        try:
            response = requests.get(
                f"{self.base_url}/calls/{call_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle the response structure properly
                if data.get('status') == 'ok' and 'response' in data:
                    return {"success": True, "data": data['response']}
                else:
                    return {"success": True, "data": data}
            elif response.status_code == 404:
                return {"error": "Call not found - it may have been deleted or the ID is incorrect"}
            else:
                return {"error": f"Failed to get call status: {response.status_code} - {response.text}"}
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return {"error": str(e)}
    
    def get_call_transcript(self, call_id):
        """Get the transcript of a completed call"""
        try:
            status_result = self.get_call_status(call_id)
            
            if 'error' in status_result:
                return status_result
            
            call_data = status_result['data']
            transcript = call_data.get('transcript', '')
            
            return {"success": True, "transcript": transcript}
                
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return {"error": str(e)}
    
    def terminate_call(self, call_id):
        """Terminate an active call"""
        # Note: Synthflow API may not support call termination
        # This is a placeholder that marks calls as terminated locally
        try:
            logger.info(f"Attempting to terminate call {call_id}")
            
            # Synthflow doesn't appear to have a termination endpoint
            # So we'll mark it as terminated in our local database only
            return {
                "success": True, 
                "message": "Call marked as terminated locally",
                "note": "Synthflow API doesn't support real-time call termination"
            }
                
        except Exception as e:
            logger.error(f"Error terminating call: {str(e)}")
            return {"error": str(e)}

class CallDatabase:
    def __init__(self, db_path="logs/calls.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database"""
        try:
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
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
                        model_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        duration INTEGER,
                        transcript TEXT,
                        success BOOLEAN,
                        error_message TEXT,
                        phone_config TEXT
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
