#!/usr/bin/env python3
"""
Debug Synthflow Call Creation - Check if calls are actually being made
"""

import requests
import json

def debug_synthflow():
    print("🔍 Debugging Synthflow Call Creation")
    print("=" * 50)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Create assistant
    print("Step 1: Creating assistant...")
    assistant_payload = {
        "type": "outbound",
        "name": "Debug Test Assistant",
        "agent": {
            "name": "Test AI",
            "voice_id": "default",
            "prompt": "You are a test assistant. Say 'This is a test call' and hang up.",
            "greeting": "Hi, this is a test call",
            "language": "en"
        }
    }
    
    try:
        response = requests.post(
            "https://api.synthflow.ai/v2/assistants",
            headers=headers,
            json=assistant_payload,
            timeout=30
        )
        
        print(f"Assistant creation status: {response.status_code}")
        print(f"Assistant response: {response.text}")
        
        if response.status_code != 200:
            print("❌ Failed to create assistant")
            return
        
        data = response.json()
        if data.get('status') != 'ok':
            print(f"❌ Assistant creation failed: {data}")
            return
        
        model_id = data['response']['model_id']
        print(f"✅ Assistant created: {model_id}")
        
        # Step 2: Check if we can make a call
        print(f"\nStep 2: Attempting to create call...")
        call_payload = {
            "model_id": model_id,
            "phone": "+1-555-123-4567",  # Test number
            "name": "Test Person",
            "prompt": "This is a test call. Please identify yourself and then end the call.",
            "greeting": "Hi, this is a test call from the AI system"
        }
        
        call_response = requests.post(
            "https://api.synthflow.ai/v2/calls",
            headers=headers,
            json=call_payload,
            timeout=30
        )
        
        print(f"Call creation status: {call_response.status_code}")
        print(f"Call response: {call_response.text}")
        
        if call_response.status_code == 200:
            call_data = call_response.json()
            print(f"✅ Call response received: {call_data}")
            
            # Check if there's a call ID in the response
            if 'response' in call_data:
                print(f"📋 Call details: {call_data['response']}")
        else:
            print(f"❌ Call creation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    debug_synthflow()
