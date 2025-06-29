#!/usr/bin/env python3
"""
Test Synthflow Get Specific Call Status
"""

import requests
import json

def test_specific_call():
    print("🔍 Testing Synthflow Get Call Status")
    print("=" * 50)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use the call_id from our recent debug test
    call_id = "67eae79c-3fb1-471f-9eba-9c2907768e77"
    
    try:
        # Get specific call status
        response = requests.get(
            f"https://api.synthflow.ai/v2/calls/{call_id}",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📋 Call details: {json.dumps(data, indent=2)}")
            
            # Check if this shows the actual call status
            if 'response' in data:
                call_info = data['response']
                print(f"\n🎯 Call Status: {call_info.get('status', 'unknown')}")
                print(f"📞 Phone: {call_info.get('phone', 'unknown')}")
                print(f"📝 Transcript: {call_info.get('transcript', 'No transcript yet')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_specific_call()
