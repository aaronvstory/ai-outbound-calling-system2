#!/usr/bin/env python3
"""
AI Call Manager - CLI Version
Simple command-line interface for making AI-powered outbound calls using Synthflow
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import requests
from datetime import datetime
import argparse

class SynthflowCLI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('SYNTHFLOW_API_KEY')
        if not self.api_key:
            print("❌ Error: SYNTHFLOW_API_KEY not found!")
            print("Please set your API key:")
            print("  export SYNTHFLOW_API_KEY=your_api_key_here")
            print("  # or")
            print("  set SYNTHFLOW_API_KEY=your_api_key_here")
            sys.exit(1)
        
        self.base_url = "https://api.synthflow.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.db_path = "logs/calls.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        os.makedirs("logs", exist_ok=True)
        
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
    
    def make_call(self, phone_number, caller_name, caller_phone, account_action, additional_info=""):
        """Make an outbound call"""
        print(f"\n🤖 AI Call Manager - Making Call")
        print(f"📞 From: {caller_name} ({caller_phone})")
        print(f"📞 To: {phone_number}")
        print(f"📋 Action: {account_action}")
        print("-" * 50)
        
        # Generate call ID
        call_id = str(uuid.uuid4())
        
        # Save to database
        call_data = {
            'id': call_id,
            'phone_number': phone_number,
            'caller_name': caller_name,
            'caller_phone': caller_phone,
            'account_action': account_action,
            'additional_info': additional_info,
            'status': 'initiating'
        }
        
        self.save_call(call_data)
        
        # Prepare conversation prompt
        conversation_prompt = f"""
You are calling customer support on behalf of {caller_name}.

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

Remember: You are calling customer support, so be respectful and follow their verification procedures.
"""
        
        payload = {
            "phone_number": phone_number,
            "conversation_prompt": conversation_prompt,
            "voice_settings": {
                "voice_id": "default_professional",
                "speed": 1.0,
                "pitch": 1.0
            },
            "call_settings": {
                "max_duration": 600,
                "enable_recording": True,
                "enable_transcription": True
            }
        }
        
        try:
            print("🔄 Initiating call with Synthflow...")
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                synthflow_call_id = result.get('call_id')
                
                print(f"✅ Call initiated successfully!")
                print(f"📋 Call ID: {call_id}")
                print(f"🔗 Synthflow ID: {synthflow_call_id}")
                
                # Update database
                self.update_call(call_id, {
                    "status": "in_progress",
                    "call_id": synthflow_call_id
                })
                
                # Monitor call progress
                self.monitor_call(call_id, synthflow_call_id)
                
            else:
                error_msg = f"API call failed: {response.status_code}"
                print(f"❌ Error: {error_msg}")
                self.update_call(call_id, {
                    "status": "failed",
                    "error_message": error_msg
                })
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ Error: {error_msg}")
            self.update_call(call_id, {
                "status": "failed",
                "error_message": error_msg
            })
    
    def monitor_call(self, call_id, synthflow_call_id):
        """Monitor call progress with real-time updates"""
        print("\n🔄 Monitoring call progress...")
        print("Press Ctrl+C to stop monitoring (call will continue)")
        
        try:
            max_polls = 120  # 10 minutes
            poll_count = 0
            
            while poll_count < max_polls:
                time.sleep(5)
                poll_count += 1
                
                # Get call status
                try:
                    response = requests.get(
                        f"{self.base_url}/calls/{synthflow_call_id}",
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        status_result = response.json()
                        call_status = status_result.get('status', 'unknown')
                        
                        print(f"📊 Status: {call_status} (poll {poll_count}/120)")
                        
                        if call_status in ['completed', 'failed', 'no_answer', 'busy']:
                            print(f"\n🎯 Call completed with status: {call_status}")
                            
                            # Get transcript
                            transcript = self.get_transcript(synthflow_call_id)
                            success = self.analyze_success(transcript)
                            
                            # Update database
                            self.update_call(call_id, {
                                "status": call_status,
                                "completed_at": datetime.now().isoformat(),
                                "duration": status_result.get('duration', 0),
                                "transcript": transcript,
                                "success": success
                            })
                            
                            # Display results
                            self.display_call_results(call_id, call_status, success, transcript)
                            break
                            
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  Warning: Could not get status update: {e}")
                    continue
            
            if poll_count >= max_polls:
                print("⏰ Monitoring timeout reached")
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            print("Call may still be in progress. Check status later with:")
            print(f"python cli.py status {call_id}")
    
    def get_transcript(self, synthflow_call_id):
        """Get call transcript"""
        try:
            response = requests.get(
                f"{self.base_url}/calls/{synthflow_call_id}/transcript",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('transcript', '')
            else:
                return ""
                
        except Exception as e:
            print(f"⚠️  Could not retrieve transcript: {e}")
            return ""
    
    def analyze_success(self, transcript):
        """Analyze if call was successful"""
        if not transcript:
            return False
        
        transcript_lower = transcript.lower()
        
        success_phrases = [
            "account adjusted", "adjustment made", "change completed",
            "updated successfully", "modification complete", "done",
            "processed", "completed", "confirmed", "yes, that's done"
        ]
        
        failure_phrases = [
            "cannot do that", "unable to", "not authorized", "need verification",
            "callback required", "supervisor needed", "system down"
        ]
        
        success_score = sum(1 for phrase in success_phrases if phrase in transcript_lower)
        failure_score = sum(1 for phrase in failure_phrases if phrase in transcript_lower)
        
        return success_score > failure_score
    
    def display_call_results(self, call_id, status, success, transcript):
        """Display call results"""
        print("\n" + "="*60)
        print("📊 CALL RESULTS")
        print("="*60)
        print(f"📋 Call ID: {call_id}")
        print(f"📊 Status: {status}")
        print(f"🎯 Success: {'✅ YES' if success else '❌ NO'}")
        
        if transcript:
            print(f"\n📝 TRANSCRIPT:")
            print("-" * 40)
            print(transcript)
            print("-" * 40)
        
        print(f"\n💾 Full details saved to database")
        print("="*60)
    
    def save_call(self, call_data):
        """Save call to database"""
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
    
    def update_call(self, call_id, updates):
        """Update call in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(call_id)
            query = f"UPDATE calls SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
    
    def list_calls(self):
        """List all calls"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at, caller_name, phone_number, 
                       status, success, account_action 
                FROM calls ORDER BY created_at DESC LIMIT 20
            """)
            
            calls = cursor.fetchall()
            
            if not calls:
                print("📭 No calls found")
                return
            
            print("\n📋 RECENT CALLS")
            print("="*100)
            print(f"{'ID':<10} {'Time':<20} {'Caller':<20} {'To':<15} {'Status':<12} {'Success':<8} {'Action':<20}")
            print("-"*100)
            
            for call in calls:
                call_id, created_at, caller_name, phone_number, status, success, action = call
                created_time = datetime.fromisoformat(created_at).strftime('%m/%d %H:%M')
                success_icon = '✅' if success else '❌' if success is not None else '⏸️'
                action_short = action[:17] + "..." if len(action) > 20 else action
                
                print(f"{call_id[:8]:<10} {created_time:<20} {caller_name[:17]:<20} "
                      f"{phone_number:<15} {status:<12} {success_icon:<8} {action_short:<20}")
    
    def get_call_details(self, call_id):
        """Get detailed call information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calls WHERE id = ? OR id LIKE ?", (call_id, f"{call_id}%"))
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Call not found: {call_id}")
                return
            
            columns = [description[0] for description in cursor.description]
            call = dict(zip(columns, row))
            
            print(f"\n📋 CALL DETAILS")
            print("="*60)
            print(f"📋 ID: {call['id']}")
            print(f"📞 From: {call['caller_name']} ({call['caller_phone']})")
            print(f"📞 To: {call['phone_number']}")
            print(f"📋 Action: {call['account_action']}")
            print(f"📊 Status: {call['status']}")
            print(f"🎯 Success: {'✅ YES' if call['success'] else '❌ NO' if call['success'] is not None else '⏸️ UNKNOWN'}")
            print(f"⏰ Created: {call['created_at']}")
            
            if call['completed_at']:
                print(f"⏰ Completed: {call['completed_at']}")
            
            if call['duration']:
                print(f"⏱️  Duration: {call['duration']} seconds")
            
            if call['additional_info']:
                print(f"ℹ️  Additional Info: {call['additional_info']}")
            
            if call['transcript']:
                print(f"\n📝 TRANSCRIPT:")
                print("-" * 40)
                print(call['transcript'])
                print("-" * 40)
            
            if call['error_message']:
                print(f"❌ Error: {call['error_message']}")

def main():
    parser = argparse.ArgumentParser(description='AI Call Manager CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Call command
    call_parser = subparsers.add_parser('call', help='Make a new call')
    call_parser.add_argument('--name', required=True, help='Your name')
    call_parser.add_argument('--phone', required=True, help='Your phone number')
    call_parser.add_argument('--to', required=True, help='Destination phone number')
    call_parser.add_argument('--action', required=True, help='Account action to request')
    call_parser.add_argument('--info', help='Additional information')
    
    # List command
    subparsers.add_parser('list', help='List recent calls')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get call details')
    status_parser.add_argument('call_id', help='Call ID (or partial ID)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = SynthflowCLI()
    
    if args.command == 'call':
        cli.make_call(
            phone_number=args.to,
            caller_name=args.name,
            caller_phone=args.phone,
            account_action=args.action,
            additional_info=args.info or ""
        )
    elif args.command == 'list':
        cli.list_calls()
    elif args.command == 'status':
        cli.get_call_details(args.call_id)

if __name__ == '__main__':
    main()
