#!/usr/bin/env python3
"""
Debug Call Issues - Figure out why calls aren't working
"""

import requests
import json

def debug_current_issues():
    print("🔍 Debugging Current Call Issues")
    print("=" * 60)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. Check assistants and their phone numbers
    print("1. Checking assistants...")
    try:
        response = requests.get("https://api.synthflow.ai/v2/assistants", headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            assistants = data.get('response', {}).get('assistants', [])
            print(f"Found {len(assistants)} assistants:")
            for i, assistant in enumerate(assistants[:3]):  # Show first 3
                print(f"  - {assistant.get('name', 'Unnamed')} (ID: {assistant.get('id', 'No ID')})")
                print(f"    Phone: {assistant.get('phone_number', 'No phone assigned')}")
        else:
            print(f"❌ Failed to get assistants: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Check phone numbers
    print("\n2. Checking available phone numbers...")
    try:
        response = requests.get("https://api.synthflow.ai/v2/phone_numbers", headers=headers, timeout=15)
        print(f"Phone numbers API status: {response.status_code}")
        print(f"Response: {response.text[:300]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Check recent calls and their actual status
    print("\n3. Checking recent call statuses...")
    try:
        # Get the problematic call from the screenshot
        call_id = "73748452-91db-4c20-a004-5b6bdf114a63"
        response = requests.get(f"https://api.synthflow.ai/v2/calls/{call_id}", headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"Call {call_id} details:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Failed to get call details: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. Test a simple call creation to see what happens
    print("\n4. Testing minimal call creation...")
    try:
        test_payload = {
            "model_id": "f621a20d-1d86-4465-bbae-0ce5ebe530eb",
            "phone": "+1-555-TEST-123",  # Obviously fake number
            "name": "Debug Test"
        }
        
        response = requests.post("https://api.synthflow.ai/v2/calls", headers=headers, json=test_payload, timeout=15)
        print(f"Test call creation status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    debug_current_issues()
