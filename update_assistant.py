import requests
import json

api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Update assistant with phone number
assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
phone_number = "+13203310678"

# Get current assistant details first
response = requests.get(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", headers=headers, timeout=10)
if response.status_code == 200:
    current_data = response.json()['response']
    print(f"Current assistant data: {json.dumps(current_data, indent=2)[:500]}...")
    
    # Update with phone number
    update_data = {
        "phone_number": phone_number
    }
    
    # Try PUT request to update
    response = requests.put(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", 
                           headers=headers, json=update_data, timeout=10)
    print(f"\nUpdate response: {response.status_code}")
    print(response.text)
    
    # Also try PATCH
    if response.status_code != 200:
        response = requests.patch(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", 
                                 headers=headers, json=update_data, timeout=10)
        print(f"\nPATCH response: {response.status_code}")
        print(response.text)
else:
    print(f"Failed to get assistant: {response.status_code}")
    print(response.text)
