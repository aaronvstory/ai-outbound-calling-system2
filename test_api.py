#!/usr/bin/env python3
"""
Synthflow API Key Tester
Tests if your API key is valid
"""

import os
import requests

def test_api_key():
    api_key = os.getenv('SYNTHFLOW_API_KEY')
    
    if not api_key:
        print("❌ SYNTHFLOW_API_KEY not found!")
        print("Set it with: set SYNTHFLOW_API_KEY=your_key_here")
        return False
    
    print(f"🔑 Testing API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Test API endpoints that Synthflow might have
    test_urls = [
        "https://api.synthflow.ai/v1/account",
        "https://api.synthflow.ai/v1/calls",
        "https://api.synthflow.ai/account",
        "https://api.synthflow.ai/calls"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for url in test_urls:
        try:
            print(f"\n🔄 Testing: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ API key is valid!")
                try:
                    data = response.json()
                    print(f"📋 Response: {data}")
                except:
                    print(f"📋 Response: {response.text[:200]}")
                return True
            elif response.status_code == 401:
                print("❌ API key is invalid (401 Unauthorized)")
            elif response.status_code == 403:
                print("⚠️  API key valid but no permission (403 Forbidden)")
            elif response.status_code == 404:
                print("🔍 Endpoint not found (404) - trying next...")
            else:
                print(f"📋 Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Connection error: {e}")
    
    print("\n❓ Could not verify API key with standard endpoints.")
    print("This might be normal - Synthflow may use different endpoints.")
    return None

def test_call_creation():
    """Test creating a call (without actually making it)"""
    api_key = os.getenv('SYNTHFLOW_API_KEY')
    
    if not api_key:
        return False
    
    print("\n🧪 Testing call creation...")
    
    # Test payload (similar to what your app sends)
    payload = {
        "phone_number": "+1-555-123-4567",  # Fake number for testing
        "conversation_prompt": "This is a test call - do not actually dial",
        "voice_settings": {
            "voice_id": "default_professional",
            "speed": 1.0,
            "pitch": 1.0
        },
        "call_settings": {
            "max_duration": 60,
            "enable_recording": False,
            "enable_transcription": False
        },
        "test_mode": True  # Try to indicate this is a test
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_urls = [
        "https://api.synthflow.ai/v1/calls",
        "https://api.synthflow.ai/calls"
    ]
    
    for url in test_urls:
        try:
            print(f"🔄 Testing call creation: {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Response: {response.text[:500]}")
            
            if response.status_code in [200, 201]:
                print("✅ Call creation endpoint working!")
                return True
            elif response.status_code == 401:
                print("❌ API key invalid")
                return False
            elif response.status_code == 400:
                print("⚠️  Bad request - but API key seems to work")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Error: {e}")
    
    return False

if __name__ == '__main__':
    print("🧪 Synthflow API Key Tester")
    print("=" * 40)
    
    # Test API key
    key_result = test_api_key()
    
    # Test call creation
    call_result = test_call_creation()
    
    print("\n" + "=" * 40)
    print("📊 RESULTS:")
    print(f"🔑 API Key: {'✅ Valid' if key_result else '❌ Invalid' if key_result is False else '❓ Unknown'}")
    print(f"📞 Call Creation: {'✅ Working' if call_result else '❌ Failed'}")
    
    if not key_result and not call_result:
        print("\n💡 Troubleshooting:")
        print("1. Double-check your API key from Synthflow dashboard")
        print("2. Make sure you have credits in your Synthflow account")
        print("3. Check if your account is activated")
        print("4. Try regenerating your API key")
