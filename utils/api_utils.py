import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key and base URL from environment variables
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = "https://openrouter.ai/api/v1/chat/completions"

# Configure token limits
MAX_OUTPUT_TOKENS = 2000  # Optimized for Render free tier
MAX_CONTEXT_TOKENS = 12000  # Slightly under max for efficiency and to avoid errors


def query_deepseek(prompt):
    """Send the prompt to DeepSeek Chat API and get the response."""
    try:
        response = requests.post(
            f"{deepseek_api_base}",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat:free",
                "prompt": prompt,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.7,  # Balanced creativity
                "top_p": 0.9,  # Nucleus sampling for better responses
                "context_length": MAX_CONTEXT_TOKENS,
            },
        )
        response_data = response.json()
        if response.status_code != 200:
            raise Exception(f"Error querying DeepSeek: {response_data}")
        return response_data["choices"][0]["text"]
    except Exception as e:
        print(f"Error querying DeepSeek: {e}")
        return None


def query_deepseek_r1(prompt):
    """Send the prompt to DeepSeek R1 API and get the response."""
    try:
        response = requests.post(
            f"{deepseek_api_base}",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-r1:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.7,  # Balanced creativity
                "top_p": 0.9,  # Nucleus sampling for better responses
            },
        )
        response_data = response.json()
        if response.status_code != 200:
            raise Exception(f"Error querying DeepSeek R1: {response_data}")
        return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error querying DeepSeek R1: {e}")
        return None
