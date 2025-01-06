import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key from the environment variable
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = "https://api.deepseek.com/beta"

def query_deepseek(prompt):
    """Send the prompt to DeepSeek API and get the response."""
    try:
        response = requests.post(
            f"{deepseek_api_base}/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "prompt": prompt,
                "max_tokens": 150
            }
        )
        response_data = response.json()
        if response.status_code != 200:
            raise Exception(f"Error querying DeepSeek: {response_data}")
        return response_data['choices'][0]['text']
    except Exception as e:
        print(f"Error querying DeepSeek: {e}")
        return None
