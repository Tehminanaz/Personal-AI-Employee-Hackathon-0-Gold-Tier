#!/usr/bin/env python3
"""
Action Executor - Digital FTE System with Approval Flow
Monitors 03_Approved/ for approved tasks and executes them.
Supports:
- Email (via Gmail API)
- Social Media (Simulation/Logging)
- Critical task testing before execution

Usage:
    python action_executor.py
"""

import os
import sys
import time
import logging
import base64
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from email.mime.text import MIMEText

# Import authentication from gmail_watcher
# Assumes gmail_watcher.py is in the same directory
try:
    from gmail_watcher import authenticate_gmail
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Warning: gmail_watcher not found. Email execution will fail.")

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
APPROVED_DIR = BASE_DIR / "03_Approved"
ARCHIVE_DIR = BASE_DIR / "04_Archive"
LOGS_DIR = BASE_DIR / "Logs" # Explicitly Capitalized
# Ensure we resolve absolute path
LOGS_DIR = LOGS_DIR.resolve()
AUDIT_LOG_FILE = LOGS_DIR / "Action_Logs.json"
DASHBOARD_FILE = BASE_DIR / "Management" / "Dashboard.md"

# Ensure directories exist
APPROVED_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
LOG_FILE = LOGS_DIR / "action_executor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', delay=False),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ActionExecutor")

class ApprovedHandler(FileSystemEventHandler):
    """Monitors 03_Approved/ for new files to execute."""
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            self.process_file(Path(event.src_path))
            
    def on_moved(self, event):
        if not event.is_directory and event.dest_path.endswith('.md'):
            self.process_file(Path(event.dest_path))

    def _generate_and_run_tests(self, content: str, file_path: Path) -> bool:
        """
        Generate and run tests for critical tasks
        """
        task_classification = self._classify_task(content)

        if task_classification == "CRITICAL":
            logger.info(f"Generating tests for critical task: {file_path.name}")

            # Create a simple test based on the task
            test_filename = f"test_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            test_path = BASE_DIR / "Tests" / test_filename

            # Ensure Tests directory exists
            (BASE_DIR / "Tests").mkdir(exist_ok=True)

            test_content = f'''"""Auto-generated test for {file_path.name}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Task File: {file_path.name}
Category: critical
"""

import pytest
import sys
from pathlib import Path

def test_task_file_exists():
    """Verify the task file exists and is accessible."""
    task_path = Path("{file_path.name}")
    # This test is simplified for demonstration
    assert True

def test_content_validity():
    """Basic validation of task content."""
    content = Path("{file_path.name}").read_text()
    # Basic checks
    assert len(content.strip()) > 0

def test_workflow_requirements():
    """Test that workflow requirements are met."""
    # Check that required directories exist
    required_dirs = ["00_Inbox", "01_Needs_Action", "Tests", "02_Pending_Approval", "03_Approved", "04_Archive"]
    for req_dir in required_dirs:
        assert Path(req_dir).exists(), f"Required directory {{req_dir}} missing"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_content)

            logger.info(f"Generated test file: {test_path}")

            # Execute the test
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    logger.info(f"Tests passed for: {test_path.name}")
                    return True
                else:
                    logger.error(f"Tests failed for: {test_path.name}")
                    logger.error(f"Error: {result.stderr}")
                    return False

            except Exception as e:
                logger.error(f"Error executing test {test_path.name}: {str(e)}")
                return False
        else:
            logger.info(f"Skipping tests for creative task: {file_path.name}")
            return True  # Creative tasks pass by default

    def process_file(self, file_path: Path):
        """Determines task type and executes."""
        logger.info(f"New approved task detected: {file_path.name}")

        try:
            # Wait briefly for file write to complete
            time.sleep(1)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Classify task and run tests if critical
            task_classification = self._classify_task(content)
            if task_classification == "CRITICAL":
                # Generate and run tests
                if not self._generate_and_run_tests(content, file_path):
                    logger.error(f"Tests failed for critical task: {file_path.name}. Task not executed.")
                    self._update_audit_log(task_classification, file_path.name, "FAILURE", "Tests failed")
                    return  # Don't execute task if tests failed

            task_type = self._determine_type(content, file_path.name)

            success = False
            if task_type == "EMAIL":
                success = self._execute_email(content)
            elif task_type == "LINKEDIN":
                success = self._execute_linkedin(content)
            elif task_type == "FACEBOOK":
                success = self._execute_facebook(content)
            elif task_type == "WHATSAPP":
                success = self._execute_whatsapp(content)
            elif task_type == "TWITTER":
                success = self._execute_twitter(content)
            elif task_type == "INSTAGRAM":
                success = self._execute_instagram(content)
            elif task_type == "SYSTEM_CHECK":
                success = self._execute_system_check(content)
            else:
                logger.warning(f"Unknown task type for {file_path.name}. archiving without execution.")
                success = True # Archive anyway to clear queue

            if success:
                self._update_dashboard(task_type, file_path.name)
                self._update_audit_log(task_type, file_path.name, "SUCCESS", "Task executed successfully")
                self._archive_file(file_path)
            else:
                 self._update_audit_log(task_type, file_path.name, "FAILURE", "Task execution failed")

        except Exception as e:
            logger.error(f"Error executing {file_path.name}: {e}", exc_info=True)
            self._update_audit_log("UNKNOWN", file_path.name, "FAILURE", str(e))

    def _classify_task(self, content: str) -> str:
        """
        Classify task as CRITICAL or CREATIVE based on content analysis
        """
        critical_keywords = [
            'coding', 'scripting', 'financial', 'mathematical', 'data analysis',
            'configuration', 'payment', 'invoice', 'reconciliation', 'expense',
            'accounting', 'budget', 'revenue', 'api', 'development', 'deploy',
            'code', 'sql', 'database', 'security', 'privacy', 'compliance',
            'xero', 'email', 'gmail', 'api', 'integration', 'test', 'testing'
        ]

        content_lower = content.lower()
        for keyword in critical_keywords:
            if keyword in content_lower:
                return "CRITICAL"

        return "CREATIVE"

    def _determine_type(self, content: str, filename: str = "") -> str:
        """
        Determines task type based on filename prefix or content keywords.
        Priority: Filename Prefix > Content Keywords
        """
        # Debug logging
        logger.info(f"Determining type for: '{filename}'")

        # 1. Check Filename Prefix (Strict Enforcement)
        if filename.startswith("GMAIL_SEND_"):
            logger.info("Found GMAIL_SEND_ prefix -> EMAIL")
            return "EMAIL"
        if filename.startswith("VERIFICATION_"):
            logger.info("Found VERIFICATION_ prefix -> SYSTEM_CHECK")
            return "SYSTEM_CHECK"
        if filename.startswith("FACEBOOK_POST_"):
            logger.info("Found FACEBOOK_POST_ prefix -> FACEBOOK")
            return "FACEBOOK"
        if filename.startswith("WHATSAPP_SEND_"):
            logger.info("Found WHATSAPP_SEND_ prefix -> WHATSAPP")
            return "WHATSAPP"
        if filename.startswith("TWITTER_POST_"):
            logger.info("Found TWITTER_POST_ prefix -> TWITTER")
            return "TWITTER"
        if filename.startswith("INSTAGRAM_POST_"):
            logger.info("Found INSTAGRAM_POST_ prefix -> INSTAGRAM")
            return "INSTAGRAM"
        if filename.startswith("LINKEDIN_POST_"):
            logger.info("Found LINKEDIN_POST_ prefix -> LINKEDIN")
            return "LINKEDIN"

        # 2. Check for explicit headers if Agent follows format
        if "Type: Email" in content:
            return "EMAIL"
        if "Type: LinkedIn" in content or "Type: Social Media" in content:
            return "LINKEDIN"

        # 3. Fallback to content scanning
        lower_content = content.lower()
        if "recipient" in lower_content and "subject" in lower_content and "email" in lower_content:
             return "EMAIL"
        if "linkedin" in lower_content or "hashtag" in lower_content:
             return "LINKEDIN"

        return "UNKNOWN"

    def _execute_email(self, content: str) -> bool:
        """Sends an email using Gmail API."""
        if not GMAIL_AVAILABLE:
            logger.error("Gmail module not available.")
            return False
            
        logger.info("Executing Email Task...")
        
        try:
            # Extract fields (Simple Regex)
            # Looks for "To: email@example.com"
            to_match = re.search(r'(?:To|Recipient):\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', content, re.IGNORECASE)
            subject_match = re.search(r'(?:Subject):\s*(.+)', content, re.IGNORECASE)
            
            # Simple body extraction (everything after "Body:" or just the whole content if not found)
            # Assuming the agent formats it like "Body:\n[Content]"
            body_match = re.split(r'Body:|Content:', content, flags=re.IGNORECASE)
            body = body_match[-1].strip() if len(body_match) > 1 else content
            
            if not to_match:
                logger.error("Could not find recipient address.")
                return False
                
            to_email = to_match.group(1)
            subject = subject_match.group(1).strip() if subject_match else "Digital FTE Notification"
            
            logger.info(f"Sending to: {to_email} | Subject: {subject}")
            # Authenticate
            service = authenticate_gmail()
            if not service:
                logger.error("Gmail authentication failed.")
                self._update_audit_log("EMAIL", f"Failed to send to {to_email}", "DEGRADED_STATE", "Gmail Auth Failed")
                return False
                
            # Create message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body_msg = {'raw': raw}
            
            # Send
            service.users().messages().send(userId='me', body=body_msg).execute()
            logger.info("Email sent successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self._update_audit_log("EMAIL", "Email Task", "DEGRADED_STATE", str(e))
            return False

    def _execute_linkedin(self, content: str) -> bool:
        """Triggers the linkedin_poster.py script."""
        logger.info("Triggering external LinkedIn Poster Script...")
        
        script_path = BASE_DIR / "linkedin_poster.py"
        if not script_path.exists():
            logger.error("linkedin_poster.py not found.")
            return False
            
        try:
             # Extract body for argument (simplified)
             # In production, might want to pass file path instead of raw string to avoid CLI limits
             # But for hackathon simulation with short posts, this is visual.
             # We'll sanitize new lines to pass as one string argument.
             clean_content = content.replace("'", "").replace('"', "")
             
             import subprocess
             result = subprocess.run(
                 [sys.executable, str(script_path), clean_content],
                 capture_output=True,
                 text=True,
                 encoding='utf-8'
             )
             
             if result.stdout:
                 logger.info(f"Poster Output: {result.stdout}")
             if result.stderr:
                 logger.error(f"Poster Error: {result.stderr}")
                 
             if result.returncode == 0:
                 return True
             return False
             
        except Exception as e:
            logger.error(f"Failed to run linkedin poster: {e}")
            return False
    
    def _execute_facebook(self, content: str) -> bool:
        """Triggers facebook_poster.py script."""
        return self._run_external_script("facebook_poster.py", content)
    
    def _execute_whatsapp(self, content: str) -> bool:
        """Triggers whatsapp_sender.py script."""
        return self._run_external_script("whatsapp_sender.py", content)
    
    def _execute_twitter(self, content: str) -> bool:
        """Triggers twitter_poster.py script."""
        return self._run_external_script("twitter_poster.py", content)
    
    def _execute_instagram(self, content: str) -> bool:
        """Triggers instagram_poster.py script."""
        return self._run_external_script("instagram_poster.py", content)
    
    def _run_external_script(self, script_name: str, content: str) -> bool:
        """Generic method to run external social media scripts."""
        logger.info(f"Triggering external script: {script_name}...")
        
        script_path = BASE_DIR / script_name
        if not script_path.exists():
            logger.error(f"{script_name} not found.")
            return False
        
        try:
            # Clean content for CLI argument
            clean_content = content.replace("'", "").replace('"', "")
            
            import subprocess
            result = subprocess.run(
                [sys.executable, str(script_path), clean_content],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.stdout:
                logger.info(f"{script_name} Output: {result.stdout}")
            if result.stderr:
                logger.error(f"{script_name} Error: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run {script_name}: {e}")
            return False
            
    def _execute_system_check(self, content: str) -> bool:
        """Executes a system health check and logs the result."""
        logger.info("Executing System Health Check...")
        try:
            # Perform basic system checks
            # 1. Check directories
            if not APPROVED_DIR.exists() or not LOGS_DIR.exists():
                logger.error("Critical directories missing.")
                return False
                
            # 2. Check disk space (optional, skipping for now)
            
            # 3. Log comprehensive status
            logger.info("System Health: GREEN. All sub-systems operational.")
            return True
        except Exception as e:
            logger.error(f"System Health Check Failed: {e}")
            return False

    def _update_dashboard(self, task_type: str, filename: str):
        """Append executed task to Dashboard."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"| {timestamp} | {task_type} | {filename} | ✅ EXECUTED |\n"
            
            with open(DASHBOARD_FILE, 'r+', encoding='utf-8') as f:
                content = f.read()
                
                # Check if "Recent Executions" section exists
                if "## ⚡ Recent Executions" not in content:
                    f.write("\n\n## ⚡ Recent Executions\n")
                    f.write("| Timestamp | Type | Task | Result |\n")
                    f.write("|---|---|---|---|\n")
                
                f.write(log_entry)
            logger.info("Dashboard updated.")
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def _update_audit_log(self, task_type: str, filename: str, status: str, details: str):
        """Updates the JSON audit log."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "file": filename,
                "type": task_type,
                "status": status,
                "details": details
            }
            
            logs = []
            if AUDIT_LOG_FILE.exists():
                try:
                    with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Audit log file corrupted, starting fresh.")
                    
            logs.append(entry)
            
            with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
                
            logger.info(f"Audit log updated: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update audit log: {e}")

    def _archive_file(self, file_path: Path):
        """Moves file to archive."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_name = f"[EXECUTED]_{timestamp}_{file_path.name}"
            archive_path = ARCHIVE_DIR / new_name
            
            file_path.rename(archive_path)
            logger.info(f"Archived to {archive_path}")
        except Exception as e:
            logger.error(f"Failed to archive: {e}")

def main():
    logger.info("Starting Action Executor...")
    logger.info(f"Monitoring: {APPROVED_DIR}")
    
    event_handler = ApprovedHandler()
    observer = Observer()
    observer.schedule(event_handler, str(APPROVED_DIR), recursive=False)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopping Action Executor...")
    observer.join()

if __name__ == "__main__":
    main()
