import os
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv
import io
import json

# Load environment variables from .env file
load_dotenv()

# Folder ID where you want to upload the file
FOLDER_ID = "1Gx3auUkba55e2suc2lXOHot-_C21gSoI"

def authenticate_google_drive():
    """Authenticate with Google Drive API using either OAuth or service account."""
    env = os.getenv("ENV", "development")
    auth_type = os.getenv("AUTH_TYPE", "service_account")  # or "oauth"

    # Define scopes based on authentication type
    oauth_scopes = ['https://www.googleapis.com/auth/drive.file']
    service_account_scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata'
    ]

    try:
        if auth_type == "oauth":
            return authenticate_with_oauth(env, oauth_scopes)
        else:
            return authenticate_with_service_account(env, service_account_scopes)
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")

def authenticate_with_oauth(env, scopes):
    """Handle OAuth authentication for both development and production."""
    creds = None
    token_file = "token.json"

    if env == "production":
        # In production, use OAuth credentials from environment variable
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable not set")
        
        try:
            creds_dict = json.loads(credentials_json)
            creds = Credentials.from_authorized_user_info(creds_dict, scopes)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in GOOGLE_CREDENTIALS_JSON")
    else:
        # In development, use local credentials file
        credentials_path = "credentials.json"
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"OAuth credentials file not found at: {credentials_path}")

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

    # Handle token refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("OAuth credentials are invalid or expired")
        
        # Save the refreshed token
        if env == "development":
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def authenticate_with_service_account(env, scopes):
    """Handle service account authentication for both development and production."""
    if env == "production":
        # In production, use service account from environment variable
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_json:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        try:
            creds_dict = json.loads(credentials_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, 
                scopes=scopes
            )
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS")
    else:
        # In development, use local service account credentials file
        credentials_path = os.path.abspath("GOOGLE_APPLICATION_CREDENTIALS.json")
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Service account credentials file not found at: {credentials_path}"
            )
        
        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, 
                scopes=scopes
            )
        except Exception as e:
            raise ValueError(f"Invalid service account file: {str(e)}")

    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(service, file_path, file_name):
    """Upload a file to Google Drive in the specified folder."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        print(f"File ID: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")

def download_file_from_drive(service, file_id, destination_path):
    """Download a file from Google Drive."""
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
        
        print(f"File downloaded to {destination_path}")
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")