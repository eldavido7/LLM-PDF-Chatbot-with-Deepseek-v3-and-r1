import os
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import io

# Load environment variables from .env file
load_dotenv()

# Access the credentials from the environment variable
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# Folder ID where you want to upload the file
FOLDER_ID = "1Gx3auUkba55e2suc2lXOHot-_C21gSoI"

def authenticate_google_drive():
    """Authenticate with Google Drive API and return the service object."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, ['https://www.googleapis.com/auth/drive.file'])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, ['https://www.googleapis.com/auth/drive.file'])
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(service, file_path, file_name):
    """Upload a file to Google Drive in the specified folder."""
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File ID: {file.get('id')}")
    return file.get('id')

def download_file_from_drive(service, file_id, destination_path):
    """Download a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download progress: {int(status.progress() * 100)}%")
    
    print(f"File downloaded to {destination_path}")
