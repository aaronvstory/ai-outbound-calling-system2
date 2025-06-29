import requests
import json

# Quick diagnostic check
api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

print("🔍 SYNTHFLOW DIAGNOSTIC CHECK")
print("=" * 40)

# Check assistant
response = requests.get(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", headers=headers, timeout=10)
if response.status_code == 200:
    data = response.json()
    if 'response' in data and 'assistants' in data['response'] and data['response']['assistants']:
        assistant = data['response']['assistants'][0]
        phone = assistant.get('phone_number', '').strip()
        
        print(f"📋 Assistant ID: {assistant.get('model_id')}")
        print(f"📋 Name: {assistant.get('name')}")
        print(f"📞 Phone Number: '{phone}'")
        print(f"📞 Caller ID: '{assistant.get('caller_id_number', '')}'")
        
        if not phone:
            print("\n❌ PROBLEM: No phone number assigned!")
            print("This is why calls get stuck in queue.")
            print("\n🔧 SOLUTION:")
            print("1. Go to Synthflow dashboard")
            print("2. Edit this assistant")
            print("3. Assign phone number +13203310678")
            print("4. Save the configuration")
        else:
            print(f"\n✅ Phone number is assigned: {phone}")
    else:
        print("❌ Assistant not found or invalid response")
else:
    print(f"❌ Failed to get assistant: {response.status_code}")
    print(response.text)
