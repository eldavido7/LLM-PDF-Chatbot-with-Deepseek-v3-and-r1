import os
import fitz  # PyMuPDF for PDF text extraction
import requests  # For HTTP requests to DeepSeek API
from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)  # Generate a random secret key for the session

# Set your DeepSeek API key
deepseek_api_key = "sk-4398b4301343408db5511fc994b070f6"
deepseek_api_base = "https://api.deepseek.com/beta"  # Correct DeepSeek API base URL

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
        os.makedirs('uploads', exist_ok=True)
        pdf_path = os.path.join('uploads', file.filename)
        file.save(pdf_path)
    except Exception as e:
        return jsonify({"error": f"Error saving file: {e}"}), 500

    # Extract text from the PDF
    pdf_text = extract_pdf_text(pdf_path)
    if not pdf_text:
        return jsonify({"error": "Failed to extract text from PDF"}), 500

    # Save the extracted text in the session to be used later
    session['pdf_text'] = pdf_text
    
    return jsonify({"message": "PDF uploaded successfully. Ask a question!"})

# Route to interact with the chatbot (query)
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    # Retrieve the extracted text from the session
    pdf_text = session.get('pdf_text')
    if not pdf_text:
        return jsonify({"error": "No PDF text available"}), 400

    # Send the extracted text and the question to DeepSeek
    try:
        response = requests.post(
            f"{deepseek_api_base}/completions",  # Correct DeepSeek API endpoint
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",  # Adjust the model if needed
                "prompt": f"Based on the following text, {question} \n\n{pdf_text}",
                "max_tokens": 150  # Adjust token length as needed
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
    # Ensure the uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
