#!/usr/bin/env python3
"""
Gmail Watcher - Digital FTE System
Monitors Gmail inbox for unread messages, converts them to Markdown, 
and saves them to 00_Inbox/ for the Orchestrator to process.

Requirements:
    - credentials.json in the project root (from Google Cloud Console)
    - pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 markdownify

Usage:
    python gmail_watcher.py
"""

import os
import sys
import time
import base64
import logging
import pickle
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from markdownify import markdownify as md

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Robust Absolute Path Resolution
# This ensures paths work correctly regardless of where the script is run from
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = SCRIPT_DIR
INBOX_DIR = BASE_DIR / "00_Inbox"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.pickle"
SIMULATION_FILE = BASE_DIR / "gmail_simulation.txt"
PROCESSED_FILE = BASE_DIR / "processed_emails.json"
POLL_INTERVAL = 10  # Reduced for responsiveness, original was 60

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "gmail_watcher.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("GmailWatcher")

def authenticate_gmail():
    """Authenticates with Gmail API and returns the service object."""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
            
    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing access token...")
            creds.refresh(Request())
        else:
            logger.info("Initiating new authentication flow...")
            if not CREDENTIALS_FILE.exists():
                logger.error(f"Credentials file not found at: {CREDENTIALS_FILE}")
                logger.error("Please download 'credentials.json' from Google Cloud Console and place it in the root directory.")
                logger.error(f"Credentials file not found at: {CREDENTIALS_FILE}")
                logger.warning("Simulation Mode Only: Gmail API will be unavailable.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
            
    return build('gmail', 'v1', credentials=creds)

def get_message_body(payload: Dict[str, Any]) -> str:
    """Recursively extracts the body from the message payload."""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                # Prefer HTML if available, but keep looking for plain text as fallback/addition
                data = part['body'].get('data')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                    body = html_content # Overwrite with HTML if found, as we'll convert it
            elif 'parts' in part:
                 # Recursive call for nested parts
                 body += get_message_body(part)
    elif 'body' in payload:
        data = payload['body'].get('data')
        if data:
             body += base64.urlsafe_b64decode(data).decode('utf-8')
             
    return body

def clean_filename(subject: str) -> str:
    """Sanitizes the subject to be safe for filenames."""
    # Replace invalid characters with underscore
    clean = re.sub(r'[<>:"/\\|?*]', '_', subject)
    # Truncate if too long
    return clean[:100]

def is_spam_or_newsletter(content: str, subject: str) -> bool:
    """
    Analyzes content to determine if it's spam or newsletter.
    Returns True if it should be ignored.
    """
    spam_keywords = [
        'unsubscribe', 'view in browser', 'marketing', 'newsletter', 
        'promo', 'offer', 'sale', 'opt-out', 'subscription'
    ]
    
    text_to_scan = (subject + " " + content).lower()
    
    # Check for keywords
    for keyword in spam_keywords:
        if keyword in text_to_scan:
            return True
            
    return False

def get_priority_prefix(content: str, subject: str) -> str:
    """
    Determines if a task is urgent.
    Returns '[URGENT]_' or empty string.
    """
    urgent_keywords = ['urgent', 'asap', 'immediate', 'critical', 'important', 'emergency']
    
    text_to_scan = (subject + " " + content).lower()
    
    for keyword in urgent_keywords:
        # Simple word boundary check would be better, but simple inclusion is fine for v1
        if keyword in text_to_scan:
            return "[URGENT]_"
            
    return ""


def load_processed_ids() -> set:
    """Load set of processed message IDs from file."""
    # PROCESSED_FILE is now defined globally

    if PROCESSED_FILE.exists():
        try:
            import json
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_id(msg_id: str):
    """Save a new processed ID to file."""
    # PROCESSED_FILE is now defined globally
    processed = load_processed_ids()
    processed.add(msg_id)
    try:
        import json
        with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(processed), f)
    except Exception as e:
        logger.error(f"Failed to save processed ID: {e}")


def process_messages(service):
    """Checks for unread messages and processes them."""
    if not service:
        # No service, skip API check
        return

    try:
        # List unread messages in Inbox (All unread emails)
        results = service.users().messages().list(userId='me', q='label:UNREAD label:INBOX').execute()
        messages = results.get('messages', [])

        if not messages:
            logger.debug("No unread messages found.")
            return

        logger.info(f"Found {len(messages)} unread messages.")
        
        # Load processed IDs
        processed_ids = load_processed_ids()

        for msg in messages:
            try:
                msg_id = msg['id']
                
                # Deduplication Check
                if msg_id in processed_ids:
                    logger.info(f"Skipping already processed message: {msg_id}")
                    # Attempt to mark as read again just in case it failed previously
                    try:
                        service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
                    except:
                        pass
                    continue
                
                message = service.users().messages().get(userId='me', id=msg_id).execute()
                payload = message['payload']
                headers = payload.get('headers', [])

                # Extract Subject and From
                subject = "No Subject"
                sender = "Unknown Sender"
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    if header['name'] == 'From':
                        sender = header['value']

                logger.info(f"Processing email: {subject} from {sender}")

                # Get body
                body_content = get_message_body(payload)
                
                # SPAM FILTERING
                if is_spam_or_newsletter(body_content, subject):
                    logger.info(f"Skipping SPAM/NEWSLETTER: {subject}")
                    # Mark as read so we don't fetch it again
                    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
                    save_processed_id(msg_id)
                    continue

                # PRIORITY TAGGING
                priority_prefix = get_priority_prefix(body_content, subject)
                if priority_prefix:
                    logger.info(f"Marking as URGENT: {subject}")

                # Convert to Markdown
                # If content looks like HTML, markdownify it. 
                # If it's plain text, markdownify might just leave it alone or escape properly.
                md_content = md(body_content)


                # Create file content
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file_content = f"""# TASK: {subject}

**Source**: Email from {sender}
**Date**: {timestamp}
**Original Subject**: {subject}

## Content
{md_content}
"""

                # Save to 00_Inbox
                safe_subject = clean_filename(subject)
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Include Priority Prefix in filename
                filename = f"{priority_prefix}Email_{date_str}_{safe_subject}.md"
                file_path = INBOX_DIR / filename


                # Ensure inbox exists
                INBOX_DIR.mkdir(exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                
                logger.info(f"Saved task to: {file_path}")

                # Mark as read (remove UNREAD label)
                service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
                logger.info(f"Marked message {msg_id} as read.")
                
                # Save ID as processed
                save_processed_id(msg_id)


            except Exception as e:
                logger.error(f"Error processing message {msg.get('id')}: {e}", exc_info=True)

    except HttpError as error:
        logger.error(f"An error occurred with Gmail API: {error}")

def check_simulation():
    """Checks for a local simulation file to create a task."""
    if SIMULATION_FILE.exists():
        logger.info(f"Simulation file found: {SIMULATION_FILE}")
        try:
            with open(SIMULATION_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing: First line is Subject, rest is body
            lines = content.split('\n', 1)
            subject = lines[0].replace("Subject:", "").strip()
            body_content = lines[1].strip() if len(lines) > 1 else ""
            
            # Use "Simulation" as sender
            sender = "Simulation Mode"
            
            # Convert body to markdown (in case it has HTML, though unlikely for txt)
            md_content = md(body_content)

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_content = f"""# TASK: {subject}

**Source**: Email from {sender}
**Date**: {timestamp}
**Original Subject**: {subject}

## Content
{md_content}
"""
            # Save to 00_Inbox
            safe_subject = clean_filename(subject)
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Email_{date_str}_{safe_subject}.md"
            file_path = INBOX_DIR / filename

            # Ensure inbox exists
            INBOX_DIR.mkdir(exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            logger.info(f"Saved simulation task to: {file_path}")
            
            # Delete simulation file
            SIMULATION_FILE.unlink()
            logger.info("Simulation file deleted.")
            
        except Exception as e:
            logger.error(f"Error processing simulation file: {e}", exc_info=True)


def main():
    logger.info("Starting Gmail Watcher...")
    
    # Ensure credentials exist before starting loop
    service = None
    if not CREDENTIALS_FILE.exists():
         logger.warning(f"WARNING: 'credentials.json' not found at {CREDENTIALS_FILE}")
         logger.warning("Running in SIMULATION MODE ONLY.")
    else:
        try:
             service = authenticate_gmail()
             logger.info(f"Authenticated successfully. Polling every {POLL_INTERVAL} seconds.")
        except Exception as e:
             logger.error(f"Authentication failed: {e}")
             logger.warning("Running in SIMULATION MODE ONLY.")

    try:
        while True:
            # Check for simulation file first (works even without internet)
            check_simulation()
            
            # Check Gmail if available
            if service:
                process_messages(service)
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
