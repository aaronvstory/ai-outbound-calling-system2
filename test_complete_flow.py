#!/usr/bin/env python3
"""
Complete Flow Test - Monitor the entire call process
"""

import requests
import json
import time

def test_complete_flow():
    print("🎯 Complete Call Flow Test")
    print("=" * 50)
    
    # Test call data
    call_data = {
        "caller_name": "John Boyle",
        "caller_phone": "323-343-3434",
        "phone_number": "1-555-123-4567",  # Use test number to avoid charges
        "account_action": "I need you to make an adjustment on my account to $0",
        "additional_info": "Account number: 12345678, DOB: 01/15/1985"
    }
    
    print(f"📞 Testing call from {call_data['caller_name']} to {call_data['phone_number']}")
    
    try:
        # Step 1: Create the call
        print("\n🔄 Step 1: Creating call...")
        response = requests.post(
            "http://localhost:5000/api/calls",
            headers={"Content-Type": "application/json"},
            json=call_data,
            timeout=30
        )
        
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to create call: {response.text}")
            return
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ Call creation failed: {result.get('error')}")
            return
        
        call_id = result['call_id']
        print(f"✅ Call created successfully! ID: {call_id}")
        
        # Step 2: Monitor the call
        print(f"\n🔄 Step 2: Monitoring call progress...")
        
        for i in range(12):  # Monitor for 1 minute
            time.sleep(5)
            
            try:
                status_response = requests.get(
                    f"http://localhost:5000/api/calls/{call_id}",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    call_info = status_data.get('call', {})
                    
                    print(f"📊 Check {i+1}: Status = {call_info.get('status', 'unknown')}")
                    
                    if call_info.get('transcript'):
                        print(f"📝 Transcript available: {len(call_info['transcript'])} chars")
                    
                    if call_info.get('status') in ['completed', 'failed', 'no_answer', 'busy']:
                        print(f"🏁 Call finished with status: {call_info['status']}")
                        if call_info.get('success') is not None:
                            print(f"🎯 Success: {'✅ YES' if call_info['success'] else '❌ NO'}")
                        break
                else:
                    print(f"⚠️  Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  Status check error: {e}")
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == '__main__':
    test_complete_flow()
