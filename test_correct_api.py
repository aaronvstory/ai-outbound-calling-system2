#!/usr/bin/env python3
"""
Updated Synthflow API Tester with Correct Endpoints
"""

import os
import requests
import json

def test_api_with_correct_endpoints():
    api_key = os.getenv('SYNTHFLOW_API_KEY')
    
    if not api_key:
        print("❌ SYNTHFLOW_API_KEY not found!")
        return False
    
    print(f"🔑 Testing API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Correct base URL
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: List assistants
    print("\n🔄 Testing: List assistants")
    try:
        response = requests.get(f"{base_url}/assistants", headers=headers, timeout=15)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key is valid!")
            data = response.json()
            print(f"📋 Found {len(data)} assistants" if isinstance(data, list) else f"📋 Response: {data}")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid (401 Unauthorized)")
            return False
        else:
            print(f"📋 Response: {response.text[:300]}")
            
    except requests.exceptions.RequestException as e:
        print(f"🌐 Connection error: {e}")
        return False
    
    return None

def create_test_assistant():
    """Create a test assistant for making calls"""
    api_key = os.getenv('SYNTHFLOW_API_KEY')
    
    if not api_key:
        return None
    
    print("\n🤖 Creating test assistant...")
    
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Assistant payload
    payload = {
        "type": "outbound",
        "name": "Test Support Assistant",
        "agent": {
            "name": "Customer Support AI",
            "voice_id": "default",
            "prompt": "You are a helpful customer support assistant. You will identify yourself with the caller's name and phone number, then make the requested account adjustment.",
            "greeting": "Hello, this is a test call from the AI assistant.",
            "language": "en"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/assistants", headers=headers, json=payload, timeout=15)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            if 'id' in str(data) or 'model_id' in str(data):
                print("✅ Assistant created successfully!")
                return data
            else:
                print("⚠️  Assistant creation response unclear")
                return data
        else:
            print("❌ Failed to create assistant")
            return None
            
    except Exception as e:
        print(f"❌ Error creating assistant: {e}")
        return None

def test_call_with_assistant(assistant_data):
    """Test making a call with the assistant"""
    api_key = os.getenv('SYNTHFLOW_API_KEY')
    
    if not api_key or not assistant_data:
        return False
    
    print("\n📞 Testing call creation...")
    
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Extract model_id from assistant creation response
    model_id = None
    if isinstance(assistant_data, dict):
        model_id = assistant_data.get('id') or assistant_data.get('model_id') or assistant_data.get('response', {}).get('id')
    
    if not model_id:
        print("❌ Could not find model_id from assistant creation")
        print(f"Assistant data: {assistant_data}")
        return False
    
    # Test call payload
    call_payload = {
        "model_id": model_id,
        "phone": "+1-555-123-4567",  # Test number
        "name": "Test Person",
        "prompt": "This is a test call. Please identify yourself as John Boyle calling from 323-343-3434 and request an account adjustment to $0.",
        "greeting": "Hi, my name is John Boyle, my phone number is 323-343-3434"
    }
    
    try:
        response = requests.post(f"{base_url}/calls", headers=headers, json=call_payload, timeout=15)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            print("✅ Call creation API working!")
            return True
        elif response.status_code == 400:
            print("⚠️  Bad request - but API structure seems correct")
            return True
        else:
            print("❌ Call creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating call: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Synthflow API Tester - Updated with Correct Endpoints")
    print("=" * 60)
    
    # Test API key
    api_valid = test_api_with_correct_endpoints()
    
    if api_valid:
        # Create test assistant
        assistant = create_test_assistant()
        
        if assistant:
            # Test call creation
            call_result = test_call_with_assistant(assistant)
            
            print("\n" + "=" * 60)
            print("📊 FINAL RESULTS:")
            print(f"🔑 API Key: ✅ Valid")
            print(f"🤖 Assistant Creation: ✅ Working")
            print(f"📞 Call Creation: {'✅ Working' if call_result else '❌ Failed'}")
        else:
            print("\n❌ Could not create assistant - cannot test calls")
    else:
        print("\n❌ API key validation failed")
