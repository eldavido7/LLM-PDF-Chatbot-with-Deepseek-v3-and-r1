import requests
import os
from dotenv import load_dotenv

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    print("API key missing!")
    exit(1)

headers = {"Authorization": f"Bearer {deepseek_api_key}"}
response = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
print(f"Status: {response.status_code}")
print(response.json())
