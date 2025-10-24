import json
import requests
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key and base URL from environment variables
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = (
    "https://openrouter.ai/api/v1/chat/completions"  # use this for OpenRouter API
)
deepseek_api_base = (
    "https://api.deepseek.com/chat/completions"  # use this for actual DeepSeek API
)

# Configure token limits
MAX_OUTPUT_TOKENS = 2000  # Optimized for Render free tier
MAX_CONTEXT_TOKENS = 12000  # Slightly under max for efficiency and to avoid errors


def query_deepseek(prompt):
    """
    Sends a prompt to DeepSeek AI and returns the response.
    """
    headers = {
        "Authorization": f"Bearer {deepseek_api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.7,
        "top_p": 0.9,
        "context_length": MAX_CONTEXT_TOKENS,
    }

    try:
        print(f"Sending prompt to DeepSeek: {prompt[:100]}...")
        response = requests.post(deepseek_api_base, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()

        if (
            "choices" in result
            and result["choices"]
            and "message" in result["choices"][0]
            and "content" in result["choices"][0]["message"]
            and result["choices"][0]["message"]["content"].strip()
        ):
            content = result["choices"][0]["message"]["content"]
            print(f"DeepSeek raw response content: {content[:200]}...")

            # Wrap response into JSON format expected by the app
            return json.dumps({"answer": content})
        else:
            logging.error(
                "DeepSeek API returned an empty or invalid response structure."
            )
            logging.error(f"Full response: {result}")
            return json.dumps(
                {
                    "answer": "I apologize, but I couldn't generate a proper response. Can you send that message again?"
                }
            )
    except requests.RequestException as e:
        logging.error(f"DeepSeek API request failed: {e}")
        return json.dumps(
            {"answer": f"I'm having technical difficulties right now: {str(e)}"}
        )
    except Exception as e:
        logging.error(f"Unexpected error querying DeepSeek: {e}")
        return json.dumps({"answer": f"An unexpected error occurred: {str(e)}"})


def query_deepseek_r1(prompt):
    """Send the prompt to DeepSeek R1 API and get the response."""
    try:
        response = requests.post(
            deepseek_api_base,
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-reasoner",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.7,
                "top_p": 0.9,
            },
        )
        response_data = response.json()

        if response.status_code != 200:
            raise Exception(f"Error querying DeepSeek R1: {response_data}")

        if (
            "choices" in response_data
            and response_data["choices"]
            and "message" in response_data["choices"][0]
            and "content" in response_data["choices"][0]["message"]
        ):
            content = response_data["choices"][0]["message"]["content"]
            return json.dumps({"answer": content})

        raise Exception(f"Unexpected response structure: {response_data}")
    except Exception as e:
        logging.error(f"Error querying DeepSeek R1: {e}")
        return json.dumps({"answer": f"Error occurred: {str(e)}"})


def process_deepseek_response(response):
    """
    Extracts the answer text from DeepSeek's response.

    Handles multiple formats:
    - Direct dict: {"answer": "text"}
    - JSON string: '{"answer": "text"}'
    - Code blocks: ```json\n{"answer": "text"}\n```
    - Nested JSON: {"answer": "{\"answer\": \"text\"}"}
    - Empty/malformed responses

    Args:
        response: Response from DeepSeek API (dict, str, or None)

    Returns:
        str: Cleaned answer text or error message
    """
    EMPTY_RESPONSE_MSG = "I apologize, but I couldn't generate a proper response. Can you send that message again?"

    # Handle None/empty
    if not response:
        return EMPTY_RESPONSE_MSG

    try:
        # Convert to string for uniform processing
        if isinstance(response, dict):
            response = json.dumps(response)

        response_str = str(response).strip()

        if not response_str:
            return EMPTY_RESPONSE_MSG

        # Remove code block wrappers (```json ... ``` or ``` ... ```)
        if response_str.startswith("```"):
            lines = response_str.split("\n")
            # Remove first line (```json or ```) and last line (```)
            response_str = "\n".join(lines[1:-1]).strip()

        # Try to parse as JSON (handles both direct JSON and nested JSON strings)
        answer = response_str
        max_depth = 3  # Prevent infinite loops on circular structures

        for _ in range(max_depth):
            # If it looks like JSON, try to parse it
            if answer.startswith("{") and answer.endswith("}"):
                try:
                    parsed = json.loads(answer)
                    if isinstance(parsed, dict) and "answer" in parsed:
                        answer = parsed["answer"]
                        # If answer is still a dict/list, convert back to string
                        if isinstance(answer, (dict, list)):
                            answer = json.dumps(answer)
                        continue
                    else:
                        # JSON parsed but no "answer" key, use the JSON string
                        break
                except json.JSONDecodeError:
                    # Not valid JSON, treat as plain text
                    break
            else:
                # Doesn't look like JSON, we're done
                break

        # Final cleanup
        answer = str(answer).strip()

        # Remove markdown bold/italic formatting
        answer = answer.replace("**", "").replace("*", "")

        # Check if we ended up with empty content
        if not answer or answer in ['""', "''", "{}", "[]"]:
            return EMPTY_RESPONSE_MSG

        return answer

    except Exception as e:
        logger.error(f"Error processing DeepSeek response: {e}", exc_info=True)
        logger.debug(f"Problematic response: {str(response)[:500]}")
        return EMPTY_RESPONSE_MSG
