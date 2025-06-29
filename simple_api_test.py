#!/usr/bin/env python3
"""
Simple API Test to Debug Synthflow Issues
"""

import requests
import json

def test_basic_api():
    """Test basic API access"""
    print("🔍 Testing Synthflow Basic API Access")
    print("=" * 50)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Get assistants
    print("Step 1: Testing API key with /assistants endpoint...")
    try:
        response = requests.get(f"{base_url}/assistants", headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key works!")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"❌ API Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False
    
    # Test 2: Try to create a simple call
    print("\nStep 2: Testing call creation...")
    assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"  # Your existing assistant
    
    call_payload = {
        "model_id": assistant_id,
        "phone": "+15551234567",  # Test number
        "name": "Test Caller",
        "prompt": "This is a test call. Please identify yourself and hang up.",
        "greeting": "Hi, this is a test call"
    }
    
    try:
        response = requests.post(f"{base_url}/calls", headers=headers, json=call_payload, timeout=15)
        print(f"Call Status Code: {response.status_code}")
        print(f"Call Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            call_id = data.get('response', {}).get('call_id') or data.get('call_id')
            if call_id:
                print(f"✅ Call created with ID: {call_id}")
                return call_id
        else:
            print(f"❌ Call creation failed")
            return False
    except Exception as e:
        print(f"❌ Call creation error: {e}")
        return False

def test_phone_numbers():
    """Test getting phone numbers"""
    print("\nStep 3: Testing phone numbers endpoint...")
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{base_url}/phone_numbers", headers=headers, timeout=15)
        print(f"Phone Numbers Status: {response.status_code}")
        print(f"Phone Numbers Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Phone numbers data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Phone numbers error")
    except Exception as e:
        print(f"❌ Phone numbers error: {e}")

def test_assistant_details():
    """Test getting assistant details"""
    print("\nStep 4: Testing assistant details...")
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    base_url = "https://api.synthflow.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
    
    try:
        response = requests.get(f"{base_url}/assistants/{assistant_id}", headers=headers, timeout=15)
        print(f"Assistant Status: {response.status_code}")
        print(f"Assistant Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Assistant data: {json.dumps(data, indent=2)[:1000]}...")
            
            # Check if phone number is assigned
            assistant_data = data.get('response', data)
            phone_number = assistant_data.get('phone_number')
            print(f"📞 Assistant phone number: {phone_number}")
            
            if not phone_number:
                print("⚠️  WARNING: Assistant has no phone number assigned!")
                print("This could be why outbound calls are not working.")
            
        else:
            print(f"❌ Assistant details error")
    except Exception as e:
        print(f"❌ Assistant details error: {e}")

if __name__ == '__main__':
    print("🧪 Synthflow Comprehensive API Test")
    print("=" * 60)
    
    # Run all tests
    call_id = test_basic_api()
    test_phone_numbers()
    test_assistant_details()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print("- Check the results above for any warnings or errors")
    print("- Pay special attention to phone number assignments")
    print("- Look for any 'queue' status issues in call responses")
