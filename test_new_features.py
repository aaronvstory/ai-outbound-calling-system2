#!/usr/bin/env python3
"""
Test the new call management features
"""

import requests
import json

def test_phone_numbers():
    print("🔍 Testing phone numbers endpoint...")
    try:
        response = requests.get("http://localhost:5000/api/phone-numbers", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_cleanup():
    print("\n🧹 Testing cleanup endpoint...")
    try:
        response = requests.post("http://localhost:5000/api/calls/cleanup", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_phone_numbers()
    test_cleanup()
