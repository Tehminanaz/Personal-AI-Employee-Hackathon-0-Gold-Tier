#!/usr/bin/env python3
"""
Gmail Re-authentication Script
Use this to refresh your Gmail token if it has expired or been revoked.
"""

import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
BASE_DIR = Path(__file__).parent.resolve()
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.pickle"

def reauthenticate():
    print("=" * 60)
    print("Gmail Re-authentication Script")
    print("=" * 60)
    
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        print("Please ensure credentials.json is in the project root.")
        return

    # Remove old token if it exists
    if TOKEN_FILE.exists():
        print("🗑️ Removing old token.pickle...")
        TOKEN_FILE.unlink()

    try:
        print("🌐 Opening browser for authentication...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Authentication successful!")
        print(f"📁 New token saved to: {TOKEN_FILE}")
        
        # Test connection
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"📧 Connected to: {profile.get('emailAddress')}")
        
    except Exception as e:
        print(f"❌ Error during authentication: {e}")

if __name__ == "__main__":
    reauthenticate()
