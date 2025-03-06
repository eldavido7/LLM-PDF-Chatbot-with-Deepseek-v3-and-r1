import json
import requests
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key and base URL from environment variables
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = "https://openrouter.ai/api/v1/chat/completions"

# Configure token limits
MAX_OUTPUT_TOKENS = 2000  # Optimized for Render free tier
MAX_CONTEXT_TOKENS = 12000  # Slightly under max for efficiency and to avoid errors


# def query_deepseek(prompt):
#     """Send the prompt to DeepSeek Chat API and get the response."""
#     try:
#         response = requests.post(
#             f"{deepseek_api_base}",
#             headers={
#                 "Authorization": f"Bearer {deepseek_api_key}",
#                 "Content-Type": "application/json",
#             },
#             json={
#                 "model": "deepseek/deepseek-chat:free",
#                 "prompt": prompt,
#                 "max_tokens": MAX_OUTPUT_TOKENS,
#                 "temperature": 0.7,  # Balanced creativity
#                 "top_p": 0.9,  # Nucleus sampling for better responses
#                 "context_length": MAX_CONTEXT_TOKENS,
#             },
#         )
#         response_data = response.json()
#         if response.status_code != 200:
#             raise Exception(f"Error querying DeepSeek: {response_data}")
#         return response_data["choices"][0]["text"]
#     except Exception as e:
#         print(f"Error querying DeepSeek: {e}")
#         return None


def query_deepseek(prompt):
    """
    Sends a prompt to DeepSeek AI and returns the response.
    """
    headers = {
        "Authorization": f"Bearer {deepseek_api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek/deepseek-chat:free",
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


# def query_deepseek_r1(prompt):
#     """Send the prompt to DeepSeek R1 API and get the response."""
#     try:
#         response = requests.post(
#             f"{deepseek_api_base}",
#             headers={
#                 "Authorization": f"Bearer {deepseek_api_key}",
#                 "Content-Type": "application/json",
#             },
#             json={
#                 "model": "deepseek/deepseek-r1:free",
#                 "messages": [{"role": "user", "content": prompt}],
#                 "max_tokens": MAX_OUTPUT_TOKENS,
#                 "temperature": 0.7,  # Balanced creativity
#                 "top_p": 0.9,  # Nucleus sampling for better responses
#             },
#         )
#         response_data = response.json()
#         if response.status_code != 200:
#             raise Exception(f"Error querying DeepSeek R1: {response_data}")
#         return response_data["choices"][0]["message"]["content"]
#     except Exception as e:
#         print(f"Error querying DeepSeek R1: {e}")
#         return None


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
                "model": "deepseek/deepseek-r1:free",
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
    Extracts the actual answer from DeepSeek's response, handling multiple formats and edge cases.
    """
    # Handle empty responses
    if not response:
        return "I apologize, but I couldn't generate a proper response. Can you send that message again?"

    print(
        f"Processing response type: {type(response)}, content: {str(response)[:200]}..."
    )

    # If we have an empty answer, return a default message
    if response == '{"answer": ""}' or response == {"answer": ""}:
        return "I apologize, but I couldn't generate a proper response. Can you send that message again?"

    # Direct check for simple JSON object with just an answer key (your specific case)
    if isinstance(response, dict) and len(response) == 1 and "answer" in response:
        answer_text = response["answer"]
        # Remove any asterisks from the response
        if isinstance(answer_text, str):
            answer_text = answer_text.replace("*", "")
            return answer_text.strip()

        # NEW CHECK: Handle the case where the response is a string representation of JSON with an answer key
        if (
            isinstance(response, str)
            and response.strip().startswith("{")
            and response.strip().endswith("}")
        ):
            try:
                json_obj = json.loads(response)
                if "answer" in json_obj:
                    answer_text = json_obj["answer"]
                    if isinstance(answer_text, str):
                        answer_text = answer_text.replace("*", "")
                        return answer_text.strip()
            except json.JSONDecodeError:
                pass

    # Handle code block format (```json {...} ```)
    if isinstance(response, str) and "```json" in response:
        try:
            # Extract content between ```json and ```
            json_content = response.split("```json")[1].split("```")[0].strip()
            parsed_json = json.loads(json_content)
            if "answer" in parsed_json:
                answer_text = parsed_json["answer"]
                # Remove any asterisks
                if isinstance(answer_text, str):
                    answer_text = answer_text.replace("*", "")
                    return answer_text.strip()
        except:
            pass

    try:
        # If response is already a dictionary
        if isinstance(response, dict):
            if "answer" in response:
                answer_content = response["answer"]

                # Check for code blocks in the answer string
                if isinstance(answer_content, str) and "```json" in answer_content:
                    try:
                        # Extract content between ```json and ```
                        json_content = (
                            answer_content.split("```json")[1].split("```")[0].strip()
                        )
                        parsed_json = json.loads(json_content)
                        if "answer" in parsed_json:
                            answer_text = parsed_json["answer"]
                            # Remove any asterisks
                            if isinstance(answer_text, str):
                                answer_text = answer_text.replace("*", "")
                                return answer_text.strip()
                    except:
                        pass

                if isinstance(answer_content, str):
                    # Try to parse the answer as JSON if it looks like JSON
                    if answer_content.strip().startswith(
                        "{"
                    ) and answer_content.strip().endswith("}"):
                        try:
                            inner_dict = json.loads(answer_content)
                            if "answer" in inner_dict:
                                answer_text = inner_dict["answer"]
                                # Remove any asterisks
                                if isinstance(answer_text, str):
                                    answer_text = answer_text.replace("*", "")
                                    return answer_text.strip()
                        except:
                            pass
                    # Otherwise return it directly with asterisks removed
                    answer_text = answer_content
                    if isinstance(answer_text, str):
                        answer_text = answer_text.replace("*", "")
                        return answer_text.strip()
                elif isinstance(answer_content, dict) and "answer" in answer_content:
                    answer_text = answer_content["answer"]
                    # Remove any asterisks
                    if isinstance(answer_text, str):
                        answer_text = answer_text.replace("**", "")
                        return answer_text.strip()

            # If we get here, return the string representation with asterisks removed
            result = str(response)
            return result.replace("*", "").strip()

        # If response is a string
        if isinstance(response, str):
            # Check for empty content
            if not response.strip():
                return "I apologize, but I couldn't generate a proper response. Can you send that message again?"

            # Try to parse it as JSON
            try:
                # Check if it's already a simple JSON string with just an answer key
                if response.strip().startswith(
                    '{"answer":'
                ) and response.strip().endswith("}"):
                    response_dict = json.loads(response)
                    if "answer" in response_dict:
                        answer_content = response_dict["answer"]
                        # Extra check for empty answer
                        if not answer_content or answer_content.strip() == "":
                            return "I apologize, but I couldn't generate a proper response. Can you send that message again?"
                        # Remove any asterisks
                        if isinstance(answer_content, str):
                            answer_content = answer_content.replace("*", "")
                        return answer_content.strip()

                # Otherwise proceed with normal parsing
                response_dict = json.loads(response)

                # If it has an answer key, process that
                if "answer" in response_dict:
                    answer_content = response_dict["answer"]

                    # Extra check for empty answer
                    if not answer_content or (
                        isinstance(answer_content, str) and answer_content.strip() == ""
                    ):
                        return "I apologize, but I couldn't generate a proper response. Can you send that message again?"

                    # Check for code blocks in the answer string
                    if isinstance(answer_content, str) and "```json" in answer_content:
                        try:
                            # Extract content between ```json and ```
                            json_content = (
                                answer_content.split("```json")[1]
                                .split("```")[0]
                                .strip()
                            )
                            parsed_json = json.loads(json_content)
                            if "answer" in parsed_json:
                                answer_text = parsed_json["answer"]
                                # Remove any asterisks
                                if isinstance(answer_text, str):
                                    answer_text = answer_text.replace("*", "")
                                    return answer_text.strip()
                        except:
                            pass

                    # If the answer is a string that looks like JSON
                    if isinstance(
                        answer_content, str
                    ) and answer_content.strip().startswith("{"):
                        try:
                            inner_dict = json.loads(answer_content)
                            if "answer" in inner_dict:
                                answer_text = inner_dict["answer"]
                                # Remove any asterisks
                                if isinstance(answer_text, str):
                                    answer_text = answer_text.replace("*", "")
                                    return answer_text.strip()
                        except:
                            # If it fails to parse as JSON, return the string directly with asterisks removed
                            if isinstance(answer_content, str):
                                answer_content = answer_content.replace("*", "")
                            return answer_content.strip()
                    # If answer is already a dict
                    elif (
                        isinstance(answer_content, dict) and "answer" in answer_content
                    ):
                        answer_text = answer_content["answer"]
                        # Remove any asterisks
                        if isinstance(answer_text, str):
                            answer_text = answer_text.replace("*", "")
                            return answer_text.strip()
                    # Otherwise return the answer string directly with asterisks removed
                    else:
                        if isinstance(answer_content, str):
                            answer_content = answer_content.replace("*", "")
                        return answer_content.strip()

                # Fallback: return any content we can find with asterisks removed
                result = str(response_dict)
                return result.replace("*", "").strip()

            except json.JSONDecodeError:
                # If not JSON, return the raw string if it's not empty, with asterisks removed
                if response.strip():
                    return response.strip().replace("*", "")

    except Exception as e:
        print(f"Error processing DeepSeek response: {e}")

    return "I'm not sure how to answer that."
