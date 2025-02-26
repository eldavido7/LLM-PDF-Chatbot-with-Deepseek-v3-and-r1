import os
import json
import uuid
from flask_compress import Compress
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from utils.api_utils import query_deepseek
from utils.drive_utils import (
    authenticate_google_drive,
    upload_file_to_drive,
)
from flask_cors import CORS

from utils.pdf_utils import extract_pdf_tables, extract_pdf_text, summarize_text

# Initialize Flask application
app = Flask(__name__)
Compress(app)  # Enable response compression

# Set max request size to 10MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB limit

# Apply rate limiting (200 requests per minute per IP)
limiter = Limiter(get_remote_address, app=app, default_limits=["20 per minute"])


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Max size allowed is 10MB."}), 413


# Enable CORS for all routes
CORS(app)


# Production security headers
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


# Load environment variables
load_dotenv()

# Environment-specific configuration
ENV = os.getenv("ENV", "production")
DEBUG = ENV == "development"
PORT = int(os.getenv("PORT", 10000))  # Deployment uses PORT env variable

# Create directories
CONTENT_DIR = "content"
UPLOAD_DIR = "uploads"
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize Google Drive service based on environment
if ENV == "production":
    drive_service = authenticate_google_drive()
else:
    drive_service = None


@app.route("/upload", methods=["POST"])
def upload_pdf():
    # max_size = 1 * 1024 * 1024
    # if request.content_length > max_size:
    #     return jsonify({"error": "File too large. Maximum size is 1MB"}), 413

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

    try:
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        # Use a secure filename to handle Unicode filenames safely
        safe_filename = str(uuid.uuid4()) + ".pdf"
        local_pdf_path = os.path.join("temp", safe_filename)
        file.save(local_pdf_path)

        # Process file
        pdf_text = extract_pdf_text(local_pdf_path)
        pdf_tables = extract_pdf_tables(local_pdf_path)

        if not pdf_text and not pdf_tables:
            os.remove(local_pdf_path)  # Cleanup before returning error
            return jsonify({"error": "Failed to extract content from PDF"}), 500

        # Upload to Drive only in production
        drive_file_id = None
        if ENV == "production":
            drive_file_id = upload_file_to_drive(
                drive_service, local_pdf_path, file.filename
            )

        # Clean up temp file
        os.remove(local_pdf_path)

        # Save extracted content
        session_id = str(uuid.uuid4())
        content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
        with open(content_path, "w") as f:
            json.dump(
                {
                    "text": pdf_text,
                    "tables": pdf_tables,
                    "drive_file_id": drive_file_id,
                },
                f,
            )

        return jsonify(
            {
                "message": "PDF uploaded successfully. Click next to ask a question!",
                "session_id": session_id,
            }
        )

    except Exception as e:
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)  # Ensure cleanup on error
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
@limiter.limit("10 per minute")  # Limit this route to 10 requests per minute
def chat():
    data = request.get_json()
    question = data.get("question", "").strip()
    session_id = data.get("session_id")
    enable_summarization = data.get("enable_summarization", False)

    if not question or not session_id:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Load the document content
        content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
        if not os.path.exists(content_path):
            return jsonify({"error": "No PDF content available"}), 400

        with open(content_path, "r") as f:
            content = json.load(f)

        pdf_text = content.get("text", "")
        pdf_tables = content.get("tables", [])

        # Optionally summarize text
        summary_text = summarize_text(pdf_text, enable_summarization)

        # Prepare tables for inclusion in the prompt
        table_summaries = [
            f"Table {i + 1}:\n{table}" for i, table in enumerate(pdf_tables)
        ]

        # Determine intent dynamically using the LLM
        prompt_parts = [
            "You are an intelligent assistant that helps users interact with document content.",
            "Classify the input as one of the following:",
            "- Greeting (e.g., 'hello', 'hi')",
            "- Gratitude (e.g., 'thank you')",
            "- Relevant question related to the document",
            "- Irrelevant question unrelated to the document",
            "- Other input",
            "Respond appropriately based on the classification:",
            "- For greeting: Acknowledge and invite the user to ask a question.",
            "- For gratitude: Thank them and offer further assistance.",
            "- For relevant questions: Provide a detailed, direct answer using the document context. Ensure the response is clear, complete, and contains key information needed to fully answer the question.",
            "- For irrelevant questions: Politely state that you're limited to document-related queries.",
        ]

        if summary_text:
            prompt_parts.append(f"Document Summary:\n{summary_text}")
        if table_summaries:
            prompt_parts.append(f"Tables:\n{' '.join(table_summaries)}")
        prompt_parts.append(f"User Input: {question}")
        prompt = "\n\n".join(prompt_parts)

        # Query DeepSeek with the constructed prompt
        response = query_deepseek(prompt)

        if not response:
            return jsonify(
                {
                    "answer": "I'm sorry, I couldn't process your request. Please try asking again."
                }
            )

        return jsonify({"answer": response.strip()})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    if ENV == "production":
        # Production settings
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.run(host="0.0.0.0", port=PORT, threaded=True)
    else:
        app.run(debug=True)
