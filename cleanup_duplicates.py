import os
import shutil
import re
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
NEEDS_ACTION_DIR = BASE_DIR / "01_Needs_Action"
INBOX_DIR = BASE_DIR / "00_Inbox"
ARCHIVE_DIR = BASE_DIR / "04_Archive"
DUPLICATES_DIR = ARCHIVE_DIR / "Duplicates_Cleanup"

def setup_dirs():
    DUPLICATES_DIR.mkdir(exist_ok=True, parents=True)

def cleanup_plans():
    print(f"Scanning {NEEDS_ACTION_DIR} for duplicates...")
    files = list(NEEDS_ACTION_DIR.glob("*.md"))
    
    # Group by "core" name (ignoring timestamps arguably)
    # A simple heuristic: if we have multiple files with "Final_System_Audit" in them, keep the latest.
    
    # Let's map normalized names to files
    # We'll normalize by removing "PLAN_", "Email_", timestamps, and "ACTION_REQUIRED" to find core topic
    
    topic_map = {}
    
    for f in files:
        name = f.name
        # Normalize
        # Remove common prefixes
        s = name.replace("PLAN_", "").replace("Email_", "")
        # Remove timestamps roughly (20260114_...)
        s = re.sub(r'\d{8}_\d{4,6}_?', '', s)
        s = re.sub(r'\d{8}', '', s)
        # Remove ACTION REQUIRED
        s = s.replace("ACTION_REQUIRED", "").replace("ACTION REQUIRED", "")
        # Remove underscores and spaces
        s = re.sub(r'[_\s]+', '', s).lower()
        
        if len(s) < 5: # Too short, maybe risky
            continue
            
        if s not in topic_map:
            topic_map[s] = []
        topic_map[s].append(f)
        
    # Process groups
    for topic, file_list in topic_map.items():
        if len(file_list) > 1:
            print(f"Found {len(file_list)} duplicates for topic '{topic}':")
            # Sort by modification time, descending (newest first)
            file_list.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            keep = file_list[0]
            move = file_list[1:]
            
            print(f"  Keeping: {keep.name}")
            for m in move:
                print(f"  Moving to Archive: {m.name}")
                shutil.move(str(m), str(DUPLICATES_DIR / m.name))

def cleanup_inbox_emails():
    print(f"Scanning {INBOX_DIR} for duplicate emails...")
    files = list(INBOX_DIR.glob("Email_*.md"))
    
    # Similar grouping logic could apply, but simpler:
    # If we have multiple emails with same subject (ignoring timestamp), keep newest.
    
    topic_map = {}
    for f in files:
        # Email_20260114_010101_Subject.md
        parts = f.name.split('_', 3) # Email, date, time, Subject...
        if len(parts) >= 4:
            subject = parts[3]
            if subject not in topic_map:
                topic_map[subject] = []
            topic_map[subject].append(f)
            
    for subject, file_list in topic_map.items():
        if len(file_list) > 1:
            print(f"Found {len(file_list)} duplicate emails for '{subject}':")
            file_list.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            keep = file_list[0]
            move = file_list[1:]
            print(f"  Keeping: {keep.name}")
            for m in move:
                print(f"  Moving to Archive: {m.name}")
                shutil.move(str(m), str(DUPLICATES_DIR / m.name))

if __name__ == "__main__":
    setup_dirs()
    cleanup_plans()
    cleanup_inbox_emails()
    print("Cleanup complete.")
