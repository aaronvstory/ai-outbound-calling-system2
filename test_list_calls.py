#!/usr/bin/env python3
"""
Test Synthflow List Calls API to see actual call status
"""

import requests
import json

def test_list_calls():
    print("🔍 Testing Synthflow List Calls API")
    print("=" * 50)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get list of calls
        response = requests.get(
            "https://api.synthflow.ai/v2/calls",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📋 Calls found: {json.dumps(data, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_list_calls()
