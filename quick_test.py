#!/usr/bin/env python3
"""
Quick Test - Just check if the API key is working now
"""

import requests
import json

try:
    print("🧪 Quick API Test")
    
    # Simple test call
    test_data = {
        "caller_name": "Test User",
        "caller_phone": "555-1234",
        "phone_number": "555-5678",
        "account_action": "Test call",
        "additional_info": ""
    }
    
    response = requests.post(
        "http://localhost:5000/api/calls",
        headers={"Content-Type": "application/json"},
        json=test_data,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
