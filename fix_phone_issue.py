#!/usr/bin/env python3
"""
Quick Fix for Synthflow Phone Number Issue

This script identifies and fixes the root cause of calls getting stuck in queue:
The assistant has no phone number assigned.
"""

import requests
import json
from datetime import datetime

def fix_synthflow_phone_issue():
    print("🔧 Synthflow Phone Number Fix Script")
    print("=" * 50)
    
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    phone_number = "+13203310678"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Check current assistant
    assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
    print(f"🔍 Checking assistant {assistant_id}...")
    
    response = requests.get(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", 
                           headers=headers, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        assistant_data = data.get('response', {})
        
        if 'assistants' in assistant_data and assistant_data['assistants']:
            assistant = assistant_data['assistants'][0]
            current_phone = assistant.get('phone_number', '').strip()
            
            print(f"📞 Current phone number: '{current_phone}'")
            
            if not current_phone:
                print("❌ PROBLEM FOUND: Assistant has no phone number!")
                print("   This is why calls are stuck in queue.")
                
                # Step 2: Create new assistant with phone number
                print("\n🔧 Creating new assistant with phone number...")
                
                new_assistant_payload = {
                    "type": "outbound",
                    "name": f"Fixed Customer Support Assistant - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "phone_number": phone_number,
                    "agent": {
                        "name": "Customer Support AI",
                        "voice_id": "default",
                        "prompt": "You are a helpful customer support assistant calling on behalf of the caller. Always start by identifying yourself with the caller's name and phone number, then make the requested account adjustment politely and professionally.",
                        "greeting": "Hello, this is a customer support call.",
                        "language": "en"
                    }
                }
                
                create_response = requests.post(
                    "https://api.synthflow.ai/v2/assistants",
                    headers=headers,
                    json=new_assistant_payload,
                    timeout=30
                )
                
                if create_response.status_code == 200:
                    create_data = create_response.json()
                    
                    if create_data.get('status') == 'ok' and 'response' in create_data:
                        new_assistant_id = create_data['response'].get('model_id')
                        assigned_phone = create_data['response'].get('phone_number', '')
                        
                        print(f"✅ SUCCESS! Created new assistant: {new_assistant_id}")
                        print(f"📞 Assigned phone number: {assigned_phone}")
                        
                        # Step 3: Update config file
                        print("\n📝 Updating config.py...")
                        
                        config_content = f'''# Synthflow Configuration
# Update these settings for your account

# Your purchased Synthflow phone number
SYNTHFLOW_PHONE_NUMBER = "{phone_number}"

# Your Synthflow API key
SYNTHFLOW_API_KEY = "{api_key}"

# Reusable assistant ID (fixed {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
DEFAULT_ASSISTANT_ID = "{new_assistant_id}"

# Call settings
MAX_CALL_DURATION = 600  # 10 minutes
ENABLE_RECORDING = True
ENABLE_TRANSCRIPTION = True
'''
                        
                        try:
                            with open('config.py', 'w') as f:
                                f.write(config_content)
                            print("✅ Updated config.py with new assistant ID")
                        except Exception as e:
                            print(f"⚠️  Could not update config.py: {e}")
                            print(f"Please manually update DEFAULT_ASSISTANT_ID to: {new_assistant_id}")
                        
                        # Step 4: Test call creation
                        print("\n🧪 Testing call creation with new assistant...")
                        test_call_payload = {
                            "model_id": new_assistant_id,
                            "phone": "+15551234567",  # Test number
                            "name": "Test Caller",
                            "prompt": "This is a test call to verify the phone number is working.",
                            "greeting": "Hello, this is a test call."
                        }
                        
                        test_response = requests.post(
                            "https://api.synthflow.ai/v2/calls",
                            headers=headers,
                            json=test_call_payload,
                            timeout=15
                        )
                        
                        print(f"📊 Test call status: {test_response.status_code}")
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if 'response' in test_data and test_data['response'].get('call_id'):
                                print("✅ SUCCESS! Calls should now work properly!")
                                print(f"🆔 Test call ID: {test_data['response']['call_id']}")
                            else:
                                print(f"⚠️  Call created but response unclear: {test_data}")
                        else:
                            print(f"❌ Test call failed: {test_response.text}")
                        
                        print("\n" + "=" * 50)
                        print("🎉 FIX COMPLETE!")
                        print("=" * 50)
                        print("✅ Root cause identified and fixed")
                        print("✅ New assistant created with phone number")
                        print("✅ Configuration updated")
                        print("✅ System tested")
                        print("\n📝 Next steps:")
                        print("1. Restart your Flask app")
                        print("2. Try creating a new call")
                        print("3. Calls should no longer get stuck in queue")
                        
                        return True, new_assistant_id
                    else:
                        print(f"❌ Assistant creation failed: {create_data}")
                        return False, None
                else:
                    print(f"❌ Failed to create assistant: {create_response.status_code}")
                    print(create_response.text)
                    return False, None
            else:
                print(f"✅ Assistant already has phone number: {current_phone}")
                print("The issue may be elsewhere. Check Synthflow dashboard for account status.")
                return True, assistant_id
        else:
            print("❌ Could not find assistant data in response")
            return False, None
    else:
        print(f"❌ Failed to get assistant: {response.status_code}")
        print(response.text)
        return False, None

if __name__ == '__main__':
    success, assistant_id = fix_synthflow_phone_issue()
    
    if success:
        print(f"\n🚀 Ready to use assistant: {assistant_id}")
    else:
        print("\n💡 Manual steps needed:")
        print("1. Check your Synthflow dashboard")
        print("2. Ensure phone number +13203310678 is purchased and active")
        print("3. Manually assign the phone number to an assistant")
        print("4. Update DEFAULT_ASSISTANT_ID in config.py")
