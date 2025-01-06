import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# Path to your token.json
TOKEN_PATH = "token.json"

# Define the folder ID for uploads
DRIVE_FOLDER_ID = "your_target_folder_ID" 

def authenticate_google_drive():
    """Authenticate and return the Google Drive service."""
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, ["https://www.googleapis.com/auth/drive"])
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Error authenticating Google Drive: {e}")
        return None

def upload_file_to_drive(service, file_path, file_name):
    """Upload a file to a specific folder in Google Drive."""
    try:
        file_metadata = {
            "name": file_name,
            "parents": [DRIVE_FOLDER_ID]  # Specify the folder ID
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"File uploaded successfully. File ID: {file.get('id')}")
        return file.get("id")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

# Example usage (for testing only; remove or comment out in production)
if __name__ == "__main__":
    service = authenticate_google_drive()
    if service:
        # File path and name for the test file in the root directory
        test_file_path = "test.pdf"
        test_file_name = "test.pdf"
        upload_file_to_drive(service, test_file_path, test_file_name)
