import os
import json
import uuid  # For generating unique session IDs
import pandas as pd  # For handling table data
from io import StringIO  # For handling JSON strings
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from transformers import pipeline  # For text summarization
import camelot  # For extracting tables from PDFs
import fitz  # PyMuPDF for text extraction
from utils.drive_utils import (
    authenticate_google_drive,
    upload_file_to_drive,
    download_file_from_drive,
)  # Utility functions for Google Drive operations
from utils.api_utils import query_deepseek  # Utility function for querying DeepSeek API

# Initialize Flask application
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Google Drive configuration
FOLDER_ID = "1Gx3auUkba55e2suc2lXOHot-_C21gSoI"  # Folder ID for storing files in Google Drive
drive_service = authenticate_google_drive()  # Authenticate with Google Drive

# Create directories to store content and uploads if they do not exist
CONTENT_DIR = "content"
UPLOAD_DIR = "uploads"
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Summarization function to reduce the length of text using Hugging Face Transformers
def summarize_text(text):
    """
    Summarize a given text using the distilbart model.
    Dynamically adjusts max_length based on input length.
    """
    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        input_length = len(text.split())
        max_length = min(150, int(input_length * 0.5))
        min_length = min(30, int(input_length * 0.2))
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:500]

# PDF text extraction function using PyMuPDF
def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF file.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# PDF table extraction function using Camelot
def extract_pdf_tables(pdf_path):
    """
    Extract tables from a PDF file using Camelot.
    """
    tables = []
    try:
        # First attempt with 'stream' flavor
        extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
        if extracted_tables.n == 0:
            extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        if extracted_tables.n > 0:
            for table in extracted_tables:
                tables.append(table.df.to_json())
        else:
            print("No tables detected.")
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables

# Function to split large tables into smaller chunks
def split_large_tables(tables, max_rows=50):
    """
    Split tables into smaller chunks if they exceed a specified row limit.
    """
    table_chunks = []
    for table_json in tables:
        try:
            table = pd.read_json(StringIO(table_json))
            if len(table) > max_rows:
                num_chunks = (len(table) // max_rows) + 1
                for i in range(num_chunks):
                    chunk = table.iloc[i * max_rows:(i + 1) * max_rows]
                    table_chunks.append(chunk.to_json())
            else:
                table_chunks.append(table_json)
        except Exception as e:
            print(f"Error splitting table: {e}")
    return table_chunks

# Route to upload and process PDF files
@app.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Handle PDF upload, extract content, and save metadata.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the PDF temporarily
    try:
        local_pdf_path = os.path.join("temp", file.filename)
        os.makedirs("temp", exist_ok=True)
        file.save(local_pdf_path)
    except Exception as e:
        return jsonify({"error": f"Error saving file: {e}"}), 500

    try:
        drive_file_id = upload_file_to_drive(drive_service, local_pdf_path, file.filename)
    except Exception as e:
        return jsonify({"error": f"Error uploading to Google Drive: {e}"}), 500

    pdf_text = extract_pdf_text(local_pdf_path)
    pdf_tables = extract_pdf_tables(local_pdf_path)

    if not pdf_text and not pdf_tables:
        return jsonify({"error": "Failed to extract meaningful content from PDF"}), 500

    # Generate a unique ID for the session
    session_id = str(uuid.uuid4())

    # Save the extracted text and tables to server-side storage
    content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
    with open(content_path, "w") as f:
        json.dump({"text": pdf_text, "tables": pdf_tables, "drive_file_id": drive_file_id}, f)

    os.remove(local_pdf_path)

    # Return the session ID to the client
    return jsonify({"message": "PDF uploaded successfully. Ask a question!", "session_id": session_id})

# Route to handle user queries
@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle user questions and provide answers based on PDF content.
    """
    data = request.get_json()
    question = data.get('question')
    session_id = data.get('session_id')

    if not question:
        return jsonify({"error": "No question provided"}), 400
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    # Load the extracted content from server-side storage
    content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
    if not os.path.exists(content_path):
        return jsonify({"error": "No PDF content available"}), 400

    with open(content_path, "r") as f:
        content = json.load(f)

    pdf_text = content.get("text", "")
    pdf_tables = content.get("tables", [])
    drive_file_id = content.get("drive_file_id")

    try:
        local_pdf_path = os.path.join(UPLOAD_DIR, f"{session_id}.pdf")
        download_file_from_drive(drive_service, drive_file_id, local_pdf_path)
    except Exception as e:
        return jsonify({"error": f"Error downloading PDF: {e}"}), 500

    summary_text = summarize_text(pdf_text)
    try:
        table_chunks = split_large_tables(pdf_tables)
    except Exception as e:
        return jsonify({"error": f"Error processing tables: {e}"}), 500

    # Construct the prompt
    table_summary = "\n\n".join([f"Table {i + 1}:\n{chunk}" for i, chunk in enumerate(table_chunks)])
    prompt = f"Document Text (summarized):\n{summary_text}\n\nTable Summary:\n{table_summary}\n\nQuestion: {question}"

    # Send the extracted text and tables with the question to DeepSeek
    try:
        answer = query_deepseek(prompt)
        if not answer:
            return jsonify({"error": "Error querying DeepSeek"}), 500
    except Exception as e:
        return jsonify({"error": f"Error querying DeepSeek: {e}"}), 500

    # Return the response from DeepSeek
    return jsonify({"answer": answer})

# Route to serve the frontend interface
@app.route('/')
def index():
    """
    Serve the main HTML page for user interaction.
    """
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
