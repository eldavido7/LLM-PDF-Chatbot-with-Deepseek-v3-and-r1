import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key and base URL from environment variables
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = "https://api.deepseek.com/beta"

# Configure token limits
MAX_OUTPUT_TOKENS = 2000
MAX_CONTEXT_TOKENS = 12000

def query_deepseek_r1(prompt):
    """Send the prompt to DeepSeek R1 API and get the response."""
    try:
        # Print request details for debugging
        print(f"Sending request to: {deepseek_api_base}/chat/completions")
        print(f"API Key present: {'Yes' if deepseek_api_key else 'No'}")
        
        payload = {
            "model": "deepseek-reasoner",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        print(f"Request payload: {payload}")
        
        response = requests.post(
            f"{deepseek_api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        # Print raw response for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Raw response text: {response.text}")
        
        if response.status_code != 200:
            return f"Error: Non-200 status code: {response.status_code}, Response: {response.text}"
            
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError as json_err:
            return f"Error decoding JSON: {str(json_err)}, Raw response: {response.text}"
            
        return response_data['choices'][0]['message']['content']
    
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# Example usage
if __name__ == "__main__":
    test_prompt = "Summarize this text: Hello world"
    result = query_deepseek_r1(test_prompt)
    print("\nFinal result:", result)