import os
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
import io
import json

# Load environment variables from .env file
load_dotenv()

# Folder ID where you want to upload the file
FOLDER_ID = "1Gx3auUkba55e2suc2lXOHot-_C21gSoI"

def authenticate_google_drive():
    """Authenticate with Google Drive API and return the service object."""
    creds = None
    token_file = "token.json"
    scopes = ['https://www.googleapis.com/auth/drive.file']
    
    # Check environment
    env = os.getenv("ENV", "development")

    if env == "production":
        # In production, use service account from environment variable
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_json:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        # Load the service account credentials from the environment variable (JSON string)
        creds_dict = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Use token.json for credentials if available
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Unable to authenticate with the service account.")
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
    else:
        # In development, use local service account credentials file
        credentials_path = "GOOGLE_APPLICATION_CREDENTIALS.json"
        
        if not os.path.exists(credentials_path):
            raise Exception(f"{credentials_path} file not found in the local environment.")
        
        creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
        
        # Use token.json for credentials if available
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Unable to authenticate with the local service account.")
            with open(token_file, 'w') as token:
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
