#!/usr/bin/env python3
"""
Test Real Call Creation with Sample Data
"""

import os
import sys
import requests
import json

# Add current directory to Python path
sys.path.insert(0, '.')

def test_real_call():
    """Test making a real call with sample data"""
    
    # Sample test data
    sample_data = {
        "caller_name": "John Boyle",
        "caller_phone": "323-343-3434",
        "phone_number": "1-800-266-2278",  # Comcast customer service
        "account_action": "I need you to make an adjustment on my account to $0",
        "additional_info": "Account number: 12345678, Date of birth: 01/15/1985"
    }
    
    print("🧪 Testing Real Call Creation")
    print("=" * 50)
    print(f"📞 Caller: {sample_data['caller_name']} ({sample_data['caller_phone']})")
    print(f"📞 Destination: {sample_data['phone_number']}")
    print(f"📋 Action: {sample_data['account_action']}")
    print(f"ℹ️  Additional Info: {sample_data['additional_info']}")
    print("=" * 50)
    
    # Set API key
    api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
    os.environ['SYNTHFLOW_API_KEY'] = api_key
    
    try:
        # Import the updated app
        from app import SynthflowAPI
        
        # Create API instance
        synthflow = SynthflowAPI(api_key)
        
        print("🔄 Creating call with Synthflow...")
        
        # Make the call
        result = synthflow.create_call(
            phone_number=sample_data['phone_number'],
            caller_name=sample_data['caller_name'],
            caller_phone=sample_data['caller_phone'],
            account_action=sample_data['account_action'],
            additional_info=sample_data['additional_info']
        )
        
        print("📊 RESULT:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            call_id = result.get('call_id')
            print(f"\n✅ Call initiated successfully!")
            print(f"📋 Call ID: {call_id}")
            print(f"🤖 Model ID: {result.get('model_id')}")
            
            # Monitor call for a bit
            print("\n🔄 Monitoring call (for 30 seconds)...")
            import time
            
            for i in range(6):  # Check 6 times over 30 seconds
                time.sleep(5)
                status_result = synthflow.get_call_status(call_id)
                print(f"📊 Status check {i+1}: {status_result}")
                
                if status_result.get('status') in ['completed', 'failed', 'no_answer', 'busy']:
                    print("📞 Call completed!")
                    break
                    
        else:
            print(f"\n❌ Call failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_real_call()
