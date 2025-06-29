import requests
import json

api_key = "MQu1Qm_jiZYeuE_KWWjMPIYBe0XmMx69IUVU5RLi1_I"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Test phone numbers endpoint
response = requests.get("https://api.synthflow.ai/v2/phone_numbers", headers=headers, timeout=10)
print(f"Phone numbers: {response.status_code}")
print(response.text)
