#!/usr/bin/env python3
"""
Test the Web API Endpoint
"""

import requests
import json

# Test data
test_call_data = {
    "caller_name": "John Boyle",
    "caller_phone": "323-343-3434", 
    "phone_number": "1-800-266-2278",
    "account_action": "I need you to make an adjustment on my account to $0",
    "additional_info": "Account number: 12345678, Date of birth: 01/15/1985"
}

print("🧪 Testing Web API Endpoint")
print("=" * 40)

try:
    # Make API call to web interface
    response = requests.post(
        "http://localhost:5000/api/calls",
        headers={"Content-Type": "application/json"},
        json=test_call_data,
        timeout=30
    )
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Web interface call creation working!")
            call_id = data.get('call_id')
            print(f"📋 Call ID: {call_id}")
        else:
            print(f"❌ Call failed: {data.get('error')}")
    else:
        print("❌ HTTP request failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
