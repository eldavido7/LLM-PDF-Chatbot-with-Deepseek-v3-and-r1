# PDF-LLM Chatbot
A web-based application that allows users to upload PDF files, process their content, and interact with the document using a chatbot interface. The application supports text extraction, table processing, and optional summarization of long texts using deepseek r1.

## Features
- PDF Upload: Upload PDF files for processing.
- Text and Table Extraction: Extract text and tables from PDFs.
- Chat Interface: Ask questions based on the extracted content.
- Optional Summarization: Summarize lengthy documents for easier understanding using deepseek r1's deep reasoning.

## Prerequisites
Before running this project, ensure you have the following installed:
- Python (3.8 or higher)
- pip (Python package installer)
- node (npm)

## Installation
Follow these steps to set up and run the application locally:
1. Clone the Repository:
    
        git clone https://github.com/your-username/pdf-chatbot.git
        cd pdf-chatbot

2. Set Up a Virtual Environment:
    
        python -m venv venv
        source venv/bin/activate (For Linux/MacOS)
        venv\Scripts\activate (For Windows)
          
3. Install Dependencies:
    
        pip install -r requirements.txt

4. Environment Variables:
   
    Create a .env file in the project root and configure the following variables:
   
   i. Google Drive API Keys:
   
   * Sign up for Google Cloud Console and create a project
   * Enable the Google Drive API
   * Download the JSON credentials file and place it in the root directory of the application.
   
   ii. DeepSeek API Key
   * Sign up for DeepSeek and generate an API key
   * Add the key to your .env file:
     
            DEEPSEEK_API_KEY=your-deepseek-api-key

5. Frontend Initialization:
   
   i. Navigate to the frontend directory:
   
           cd frontend
   ii. Install the dependencies:

           npm install
   iii. update .env with the local url for the initialized backend:

           NEXT_PUBLIC_BASE_URL=backend_local_url i.e: http://127.0.0.1:5000
   
## Running the Application
i. Start the Flask server by running the following:

    python app.py

The app will be available at http://127.0.0.1:5000/

ii. Start the react app:

    npm run dev

## Usage
1. Upload PDF:
    Use the "Upload PDF" button to upload a file.

2. Ask Questions:
    Click next, then enter your query in the chat interface text area and send. Optionally, you can enable the Summarization toggle for a concise summary using deepseek r1's deep reasoning capability.

3. Responses:
    The chatbot will provide an answer based on the extracted text and tables from the uploaded PDF.

## Testing
To test uploads to your google drive folder before integration, enter the folder ID in test_google_drive.py, and the path to a pdf you want to test with as defined in the file. After that, run:

    python test_google_drive.py

To test querying deepseek r1, enter your deepseek api key in the .env file. After that, run:

    python test_r1.py

## Directory Structure
* app.py: Main application logic.
* templates/index.html: Frontend template.
* utils/: Helper modules for Google Drive and API integration.
* frontend: Friendly UI made with nextjs and typescript.

## Key Libraries
* Flask: Web framework.
* PyMuPDF: PDF text extraction.
* Camelot: PDF table extraction.
* Hugging Face Transformers: Summarization pipeline.
* NextJS: For user friendly UI and chat interface.

## Known Limitations
Summarization might be slower for large texts when enabled.

## License
This project is licensed under the MIT License.
