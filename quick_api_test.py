import requests
import json

api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Test assistants endpoint
response = requests.get("https://api.synthflow.ai/v2/assistants", headers=headers, timeout=10)
print(f"Assistants: {response.status_code}")
print(response.text[:300] + "...")

# Test specific assistant
assistant_id = "f621a20d-1d86-4465-bbae-0ce5ebe530eb"
response = requests.get(f"https://api.synthflow.ai/v2/assistants/{assistant_id}", headers=headers, timeout=10)
print(f"\nAssistant details: {response.status_code}")
data = response.json() if response.status_code == 200 else {}
print(f"Phone number: {data.get('response', {}).get('phone_number', 'None')}")
