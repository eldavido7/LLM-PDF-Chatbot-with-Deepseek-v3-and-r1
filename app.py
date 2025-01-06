import os
import json
import uuid
import pandas as pd
from io import StringIO
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from transformers import pipeline
import camelot
import fitz
from utils.drive_utils import (
    authenticate_google_drive,
    upload_file_to_drive,
    download_file_from_drive,
)
from utils.api_utils import query_deepseek

# Initialize Flask application
app = Flask(__name__)

# Production security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Load environment variables
load_dotenv()

# Environment-specific configuration
ENV = os.getenv("ENV", "production")
DEBUG = ENV == "development"
PORT = int(os.getenv("PORT", 10000))  # Render uses PORT env variable

# Lazy loading of ML models
summarizer = None

def get_summarizer():
    """Lazy load the summarization model only when needed"""
    global summarizer
    if summarizer is None:
        summarizer = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=-1  # Force CPU usage to reduce memory
        )
    return summarizer

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

def summarize_text(text):
    """Summarize text with memory-efficient chunking"""
    try:
        # Break text into smaller chunks if too long
        max_chunk_size = 1000  # Adjust based on memory constraints
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_chunk_size):
            chunk = " ".join(words[i:i + max_chunk_size])
            summarizer = get_summarizer()
            max_length = min(150, int(len(chunk.split()) * 0.3))
            min_length = min(30, int(len(chunk.split()) * 0.1))
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            chunks.append(summary[0]['summary_text'])
        
        return " ".join(chunks)
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:500]

def extract_pdf_text(pdf_path):
    """Memory-efficient PDF text extraction"""
    try:
        doc = fitz.open(pdf_path)
        text_chunks = []
        for page in doc:
            text_chunks.append(page.get_text())
            page.clean_contents()  # Clean up page resources
        doc.close()  # Explicitly close the document
        return "\n".join(text_chunks)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_pdf_tables(pdf_path):
    """Memory-efficient table extraction"""
    tables = []
    try:
        # Process only first 10 pages for tables to save memory
        max_pages = 10
        extracted_tables = camelot.read_pdf(
            pdf_path,
            pages=f"1-{max_pages}",
            flavor="stream"
        )
        
        if extracted_tables.n > 0:
            for table in extracted_tables:
                # Convert to JSON and clear DataFrame
                tables.append(table.df.to_json())
                del table.df
        
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)
        local_pdf_path = os.path.join("temp", file.filename)
        file.save(local_pdf_path)

        # Process file
        pdf_text = extract_pdf_text(local_pdf_path)
        pdf_tables = extract_pdf_tables(local_pdf_path)

        if not pdf_text and not pdf_tables:
            return jsonify({"error": "Failed to extract content from PDF"}), 500

        # Upload to Drive only in production
        drive_file_id = None
        if ENV == "production":
            drive_file_id = upload_file_to_drive(drive_service, local_pdf_path, file.filename)

        # Clean up
        os.remove(local_pdf_path)

        # Save extracted content
        session_id = str(uuid.uuid4())
        content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
        with open(content_path, "w") as f:
            json.dump({
                "text": pdf_text,
                "tables": pdf_tables,
                "drive_file_id": drive_file_id
            }, f)

        return jsonify({
            "message": "PDF uploaded successfully. Ask a question!",
            "session_id": session_id
        })

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('question')
    session_id = data.get('session_id')

    if not question or not session_id:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
        if not os.path.exists(content_path):
            return jsonify({"error": "No PDF content available"}), 400

        with open(content_path, "r") as f:
            content = json.load(f)

        pdf_text = content.get("text", "")
        pdf_tables = content.get("tables", [])
        drive_file_id = content.get("drive_file_id")

        # Download PDF if we have a drive file ID
        if drive_file_id:
            try:
                local_pdf_path = os.path.join("temp", f"{session_id}.pdf")
                os.makedirs("temp", exist_ok=True)
                
                # Download the file
                download_file_from_drive(drive_service, drive_file_id, local_pdf_path)
                
                # Re-extract text and tables from the downloaded PDF
                new_text = extract_pdf_text(local_pdf_path)
                new_tables = extract_pdf_tables(local_pdf_path)
                
                # Update with fresh content if extraction succeeded
                if new_text:
                    pdf_text = new_text
                if new_tables:
                    pdf_tables = new_tables
                
                # Clean up
                os.remove(local_pdf_path)
                
            except Exception as e:
                print(f"Error processing downloaded PDF: {e}")
                # Continue with existing content if download/processing fails
                pass

        # Generate summary
        summary_text = summarize_text(pdf_text)

        # Process tables
        table_summary = "\n\n".join([f"Table {i + 1}:\n{table}" 
                                   for i, table in enumerate(pdf_tables[:3])])  # Limit to 3 tables
        
        # Construct prompt with length limits
        prompt = f"Document Summary:\n{summary_text[:1000]}\n\nTables:\n{table_summary[:1000]}\n\nQuestion: {question}"

        # Query DeepSeek
        answer = query_deepseek(prompt)
        if not answer:
            return jsonify({"error": "Failed to get response"}), 500

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if ENV == "production":
        # Production settings
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.run(host='0.0.0.0', port=PORT)
    else:
        app.run(debug=True)
