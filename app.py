import os
import fitz  # PyMuPDF for PDF text extraction
import camelot  # For table extraction from PDF
import requests  # For HTTP requests to DeepSeek API
from flask import Flask, request, jsonify, render_template
import json  # For handling JSON data
import uuid  # For generating unique session IDs
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Access the DeepSeek API key from the environment variable
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = "https://api.deepseek.com/beta"

# Directory to store uploaded files and processed content
UPLOAD_DIR = "uploads"
CONTENT_DIR = "content"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CONTENT_DIR, exist_ok=True)

# A function to extract text from PDF using PyMuPDF
def extract_pdf_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# A function to extract tables from PDF using Camelot
def extract_pdf_tables(pdf_path):
    tables = []
    try:
        # First attempt with 'stream' flavor
        extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
        if not extracted_tables:
            # If no tables detected, try the 'lattice' flavor
            extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        
        if extracted_tables:
            # Log how many tables were detected
            print(f"Detected {len(extracted_tables)} tables")
            for table in extracted_tables:
                tables.append(table.df.to_json())  # Convert table to JSON
        else:
            print("No tables detected with both 'stream' and 'lattice' methods.")
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables

# A function to summarize the text (to prevent exceeding token limit)
def summarize_text(text, max_length=5000):
    if len(text) > max_length:
        return text[:max_length]
    return text

# A function to split tables into smaller parts (if they are too large)
def split_large_tables(tables, max_tokens_per_chunk=2048):
    table_chunks = []
    for table in tables:
        # Assuming the table is a JSON string, we'll split by rows if needed
        table_data = json.loads(table)  # Convert back to a list
        rows = table_data.get("data", [])
        
        chunk = []
        chunk_size = 0
        
        for row in rows:
            chunk_size += len(json.dumps(row))  # Estimate the size of the chunk
            
            if chunk_size > max_tokens_per_chunk:
                table_chunks.append(json.dumps({"data": chunk}))  # Save current chunk
                chunk = [row]  # Start a new chunk
                chunk_size = len(json.dumps(row))
            else:
                chunk.append(row)
        
        if chunk:
            table_chunks.append(json.dumps({"data": chunk}))  # Add the last chunk
    return table_chunks

# Route to upload and process PDF
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the PDF temporarily
    try:
        pdf_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(pdf_path)
    except Exception as e:
        return jsonify({"error": f"Error saving file: {e}"}), 500

    # Extract text and tables from the PDF
    pdf_text = extract_pdf_text(pdf_path)
    pdf_tables = extract_pdf_tables(pdf_path)

    if not pdf_text and not pdf_tables:
        return jsonify({"error": "Failed to extract meaningful content from PDF"}), 500

    # Generate a unique ID for the session
    session_id = str(uuid.uuid4())

    # Save the extracted text and tables to server-side storage
    content_path = os.path.join(CONTENT_DIR, f"{session_id}.json")
    with open(content_path, "w") as f:
        f.write(json.dumps({"text": pdf_text, "tables": pdf_tables}))

    # Return the session ID to the client
    return jsonify({"message": "PDF uploaded successfully. Ask a question!", "session_id": session_id})

# Route to interact with the chatbot (query)
@app.route('/chat', methods=['POST'])
def chat():
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

    # Summarize text to avoid excessive length
    summary_text = summarize_text(pdf_text)

    # Split tables into smaller parts if needed
    table_chunks = split_large_tables(pdf_tables)

    # Construct the prompt
    table_summary = "\n\n".join([f"Table {i + 1}:\n{chunk}" for i, chunk in enumerate(table_chunks)])
    prompt = f"Document Text (summarized):\n{summary_text}\n\nTable Summary:\n{table_summary}\n\nQuestion: {question}"

    # Send the extracted text and tables with the question to DeepSeek
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
            return jsonify({"error": f"Error querying DeepSeek: {response_data}"}), 500

        answer = response_data['choices'][0]['text']
    except Exception as e:
        return jsonify({"error": f"Error querying DeepSeek: {e}"}), 500

    # Return the response from DeepSeek
    return jsonify({"answer": answer})

# Route to serve the frontend interface
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
