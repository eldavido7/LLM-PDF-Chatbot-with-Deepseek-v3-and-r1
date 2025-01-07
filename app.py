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
    """Lazy load the summarization model with GPU if available"""
    global summarizer
    if summarizer is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        summarizer = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=device  # Use GPU if available
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

def summarize_text(text, enable_summarization=False):
    """Configurable text summarization with length-based bypass"""
    if not enable_summarization:
        # Return first 1000 characters if summarization disabled
        return text[:1000]
        
    try:
        # Only summarize if text is long enough to warrant it
        if len(text) < 1000:
            return text
            
        # Break text into smaller chunks if too long
        max_chunk_size = 1000
        words = text.split()
        chunks = []
        
        summarizer = get_summarizer()
        for i in range(0, len(words), max_chunk_size):
            chunk = " ".join(words[i:i + max_chunk_size])
            max_length = min(150, int(len(chunk.split()) * 0.3))
            min_length = min(30, int(len(chunk.split()) * 0.1))
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            chunks.append(summary[0]['summary_text'])
            
            # Stop after 3 chunks to limit processing time
            if len(chunks) >= 3:
                break
        
        return " ".join(chunks)
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:1000]

def extract_pdf_text(pdf_path):
    """Memory-efficient PDF text extraction with better error handling"""
    try:
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return None
            
        doc = fitz.open(pdf_path)
        text_chunks = []
        
        for page in doc:
            try:
                chunk = page.get_text()
                if chunk:  # Only append non-empty chunks
                    text_chunks.append(chunk)
                page.clean_contents()  # Clean up page resources
            except Exception as page_error:
                print(f"Error extracting text from page: {page_error}")
                continue
                
        doc.close()  # Explicitly close the document
        
        if not text_chunks:
            return None
            
        return "\n".join(text_chunks)
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_pdf_tables(pdf_path):
    """Memory-efficient table extraction with better error handling"""
    tables = []
    try:
        # Process only first 10 pages for tables to save memory
        max_pages = 10
        
        # First check if the PDF exists and is readable
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return tables
            
        # Get actual page count
        doc = fitz.open(pdf_path)
        actual_pages = min(doc.page_count, max_pages)
        doc.close()
        
        if actual_pages == 0:
            return tables
            
        # Use string format for pages only if we have pages to process
        pages_str = f"1-{actual_pages}"
        
        extracted_tables = camelot.read_pdf(
            pdf_path,
            pages=pages_str,
            flavor="stream"
        )
        
        if extracted_tables and extracted_tables.n > 0:
            for table in extracted_tables:
                try:
                    if not table.df.empty:
                        # Convert to JSON and clear DataFrame
                        table_json = table.df.to_json(orient='records')
                        tables.append(table_json)
                    del table.df
                except Exception as table_error:
                    print(f"Error processing individual table: {table_error}")
                    continue
        
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables

@app.route('/upload', methods=['POST'])
def upload_pdf():
    max_size = 1 * 1024 * 1024
    if request.content_length > max_size:
        return jsonify({"error": "File too large. Maximum size is 1MB"}), 413
    
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
    enable_summarization = data.get('enable_summarization', False)  # Make summarization optional

    if not question or not session_id:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
        if not os.path.exists(content_path):
            return jsonify({"error": "No PDF content available"}), 400

        try:
            with open(content_path, "r") as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in content file: {e}")
            return jsonify({"error": "Invalid content data"}), 500

        pdf_text = content.get("text", "")
        pdf_tables = content.get("tables", [])

        # Process text and tables concurrently
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            # Start text summarization
            summary_future = executor.submit(
                summarize_text, 
                pdf_text, 
                enable_summarization
            )
            
            # Process tables while summarization is running
            table_summaries = []
            for i, table in enumerate(pdf_tables[:2]):  # Reduced to 2 tables for speed
                try:
                    if isinstance(table, str):
                        table_summaries.append(f"Table {i + 1}:\n{table}")
                except Exception as table_error:
                    print(f"Error processing table {i}: {table_error}")
                    continue
            
            # Get summarization result
            summary_text = summary_future.result()
        
        # Construct prompt with stricter limits
        prompt_parts = []
        if summary_text:
            prompt_parts.append(f"Document Summary:\n{summary_text[:800]}")  # Reduced limit
        if table_summaries:
            table_summary = "\n\n".join(table_summaries)
            prompt_parts.append(f"Tables:\n{table_summary[:500]}")  # Reduced limit
        prompt_parts.append(f"Question: {question}")
        
        prompt = "\n\n".join(prompt_parts)

        # Query DeepSeek
        answer = query_deepseek(prompt)
        if not answer:
            return jsonify({"error": "Failed to get response from AI model"}), 500

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
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