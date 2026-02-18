#!/usr/bin/env python3
"""
Orchestrator - Digital FTE Sentinel
Monitors 00_Inbox/ for new task files and triggers Claude AI processing.

This script implements a file system watcher that:
1. Monitors 00_Inbox/ directory for new .md files
2. Triggers Claude CLI to process files according to CLAUDE.md rules
3. Moves processed files to 04_Archive/ with timestamp
4. Logs all operations to Logs/ directory

Author: Digital FTE System
Version: 1.0
Last Updated: 2026-01-09
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Import Action Handler
try:
    from action_executor import ApprovedHandler, APPROVED_DIR
except ImportError:
    # Fallback if action_executor is broken/missing, though it shouldn't be
    logging.warning("Could not import Action Executor. Actions will not be processed.")
    ApprovedHandler = None
    APPROVED_DIR = Path(__file__).parent / "03_Approved"


# Configuration
BASE_DIR = Path(__file__).parent.resolve()
INBOX_DIR = BASE_DIR / "00_Inbox"
ARCHIVE_DIR = BASE_DIR / "04_Archive"
LOGS_DIR = BASE_DIR / "Logs"
CLAUDE_CONFIG = BASE_DIR / "CLAUDE.md"

# Ensure directories exist
INBOX_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup with UTF-8 encoding
LOG_FILE = LOGS_DIR / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', delay=False),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Orchestrator")

# Set console handler encoding to UTF-8
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        # Force UTF-8 encoding for console output
        import io
        handler.stream = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace'
        )


class InboxHandler(FileSystemEventHandler):
    """
    File system event handler for monitoring 00_Inbox/ directory.
    
    Processes new .md files by triggering Claude AI analysis and
    moving completed files to archive.
    """
    
    def __init__(self):
        """Initialize the inbox handler."""
        super().__init__()
        self.processing = set()  # Track files currently being processed
        
    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Handle file creation events in the inbox.
        
        Args:
            event: FileSystemEvent containing file path and event type
        """
        # Only process file creation events for .md files
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process markdown files
        if file_path.suffix.lower() != '.md':
            logger.info(f"Ignoring non-markdown file: {file_path.name}")
            return
            
        # Avoid processing the same file multiple times
        if file_path in self.processing:
            logger.debug(f"File already being processed: {file_path.name}")
            return
            
        # Wait a moment to ensure file write is complete
        time.sleep(0.5)
        
        # Process the file
        self.process_file(file_path)
        
    def process_file(self, file_path: Path) -> None:
        """
        Process a new file from the inbox.
        
        Args:
            file_path: Path to the file to process
        """
        try:
            self.processing.add(file_path)
            logger.info(f"Processing new file: {file_path.name}")
            
            # Verify file exists and is readable
            if not file_path.exists():
                logger.error(f"File disappeared before processing: {file_path.name}")
                return
                
            # Trigger Claude AI processing
            success = self.trigger_claude_analysis(file_path)
            
            if success:
                # Move to archive
                self.archive_file(file_path)
                logger.info(f"Successfully processed and archived: {file_path.name}")
            else:
                logger.error(f"Claude processing failed for: {file_path.name}")
                
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}", exc_info=True)
        finally:
            self.processing.discard(file_path)
            
    def trigger_claude_analysis(self, file_path: Path) -> bool:
        """
        Trigger AI analysis using 'ccr code' command.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            bool: True if analysis succeeded, False otherwise
        """
        try:
            # Build standardized expert prompt
            prompt = self._build_expert_prompt(file_path)
            
            # Build command: ccr code -p [instruction]
            # Added --permission-mode bypassPermissions to force non-interactive mode
            cmd = ["ccr", "code", "--permission-mode", "bypassPermissions", "-p", prompt]
            
            logger.info(f"Executing 'ccr code' for: {file_path.name}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Execute command
            # shell=True for Windows compatibility
            # encoding='utf-8' for Unicode support
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1200,  # 20 minute timeout for Qwen/reasoning models
                shell=True,
                cwd=str(BASE_DIR),
                encoding='utf-8'
            )
            
            # Log output
            if result.stdout:
                clean_stdout = self._strip_ansi_codes(result.stdout)
                logger.info(f"CCR Output:\n{clean_stdout}")
                
                # FALLBACK LOGIC: Check for manual file content in stdout
                # Pattern: ###FILE_START###\n[CONTENT]\n###FILE_END###
                import re
                fallback_match = re.search(r'###FILE_START###\s*(.*?)\s*###FILE_END###', clean_stdout, re.DOTALL)
                
                if fallback_match:
                    logger.warning("Fallback Detected: Extracting file content from terminal output...")
                    content = fallback_match.group(1).strip()
                    
                    if file_path.name.startswith("PLAN_"):
                        # If we processed a PLAN, the output should go to Pending Approval
                         # The prompt logic handles the target, but we need to derive filename.
                         # Generally the prompt asks for final output.
                         # We'll use the task name but in Pending_Approval
                         target_name = file_path.name.replace("PLAN_", "DRAFT_")
                         target_path = BASE_DIR / "02_Pending_Approval" / target_name
                    else:
                        # If we processed a NEW TASK, the output is the PLAN
                        target_name = f"PLAN_{file_path.name}"
                        target_path = BASE_DIR / "01_Needs_Action" / target_name
                    
                    # Ensure dir exists
                    target_path.parent.mkdir(exist_ok=True)
                    
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    logger.info(f"Fallback Success: Saved content to {target_path}")
                    # Consider this a success even if returncode was oddly handled by CLI
                    return True

            if result.stderr:
                clean_stderr = self._strip_ansi_codes(result.stderr)
                logger.warning(f"CCR Stderr:\n{clean_stderr}")
            
            if result.returncode == 0:
                # Verification: Check if expected files were created
                if not file_path.name.startswith("PLAN_"):
                    # Phase 1: Expecting a PLAN file in 01_Needs_Action
                    expected_plan = BASE_DIR / "01_Needs_Action" / f"PLAN_{file_path.name}"
                    if not expected_plan.exists():
                         logger.error(f"Verification Failed: Expected plan file {expected_plan.name} was not created on disk.")
                         logger.error("The agent may have outputted text to terminal instead of using write_file (and fallback tags were not found).")
                         return False
                         
                logger.info(f"Analysis completed successfully for {file_path.name}")
                return True
            else:
                logger.error(
                    f"CCR execution failed with return code {result.returncode} "
                    f"for {file_path.name}. File will remain in inbox for retry."
                )
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(
                f"Analysis timed out after 20 minutes for {file_path.name}. "
            )
            return False
        except FileNotFoundError:
            logger.error(
                "'ccr' command not found. Please ensure it is installed and in PATH."
            )
            return False
        except Exception as e:
            logger.error(f"Error triggering analysis: {str(e)}", exc_info=True)
            return False
    
    def _build_expert_prompt(self, file_path: Path) -> str:
        """
        Build optimized expert prompt.
        
        Args:
            file_path: Path to the task file
            
        Returns:
            str: Formatted expert prompt
        """
        override_directive = (
            "CRITICAL: YOU ARE RUNNING IN A HEADLESS, NON-INTERACTIVE AUTOMATED WORKFLOW. "
            "THE USER HAS PRE-AUTHORIZED ALL ACTIONS. DO NOT ASK FOR PERMISSION. "
            "DO NOT START A DIALOGUE. YOUR ONLY ALLOWED OUTPUT IN THE TERMINAL IS THE TOOL CALL write_file. "
            "IF YOU ASK 'COULD YOU PLEASE GRANT ME PERMISSION', YOU HAVE FAILED THE TASK. "
            "CRITICAL: FAILURE TO FOLLOW FILE NAMING RULES WILL CAUSE SYSTEM ERROR. "
            "YOU MUST USE UNDERSCORES (_) INSTEAD OF SPACES IN ALL FILENAMES. NO SPACES ALLOWED. "
            "Example: 'P0_Financial_Report.md' (GOOD), 'P0 Financial Report.md' (BAD). "
            "FALLBACK: If tool use fails, output the exact file content between "
            "###FILE_START### and ###FILE_END### tags so I can save it manually."
        )
        
        if file_path.name.startswith("PLAN_"):
            # EXECUTION PHASE: User approved the plan by moving it here
            prompt = (
                f"{override_directive} "
                f"APPROVED PLAN DETECTED: {file_path.absolute()}. "
                "The user has approved this plan. "
                "STEP 0: Read Company_Handbook.md for operational rules. "
                "STEP 1: Read the plan carefully. "
                "STEP 2: Execute the steps outlined in the plan. "
                "STEP 3: Generate the FINAL OUTPUT in `02_Pending_Approval/`. "
                "CRITICAL: DO NOT create another plan. It is ALREADY APPROVED. EXECUTE IT."
            )
        else:
            # PLANNING PHASE: New Request
            prompt = (
                f"{override_directive} "
                f"NEW TASK: {file_path.absolute()}. "
                "STEP 0: Read Company_Handbook.md for operational rules. "
                "STEP 1: Read .claude/skills/chief-of-staff.md and assume the persona. "
                "STEP 2: Create a PLAN file in `01_Needs_Action/`. "
                f"CRITICAL NAMING RULE: The plan file MUST be named 'PLAN_{file_path.name}'. "
                "DO NOT add dates, timestamps, or change capitalization. EXACT MATCH ONLY. "
                "Example: If input is 'Task.md', output MUST be 'PLAN_Task.md'. "
                "CRITICAL: Write a NARRATIVE PLAN listing execution steps. "
                "STOP. DO NOT generate the final output in 02_Pending_Approval/ yet. "
                "Wait for user approval of the plan. "
            )
        return prompt
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from text for cleaner logging."""
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)
            
    def archive_file(self, file_path: Path) -> None:
        """
        Move processed file to archive with timestamp.
        
        Args:
            file_path: Path to the file to archive
        """
        try:
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            archive_path = ARCHIVE_DIR / archive_name
            
            # Move file to archive
            file_path.rename(archive_path)
            logger.info(f"Archived: {file_path.name} -> {archive_name}")
            
        except Exception as e:
            logger.error(f"Error archiving {file_path.name}: {str(e)}", exc_info=True)


def main() -> None:
    """
    Main entry point for the orchestrator.
    
    Sets up file system monitoring and runs indefinitely until interrupted.
    """
    logger.info("=" * 80)
    logger.info("Digital FTE Orchestrator Starting (CCR Engine)")
    logger.info(f"Monitoring directory: {INBOX_DIR}")
    logger.info(f"Archive directory: {ARCHIVE_DIR}")
    logger.info(f"Logs directory: {LOGS_DIR}")
    logger.info(f"Configuration: {CLAUDE_CONFIG}")
    logger.info("=" * 80)
    
    # Verify Claude config exists
    if not CLAUDE_CONFIG.exists():
        logger.error(f"CLAUDE.md configuration not found at {CLAUDE_CONFIG}")
        logger.error("Please create CLAUDE.md before running orchestrator")
        sys.exit(1)
        
    # Create event handler and observer
    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INBOX_DIR), recursive=False)
    
    # Schedule Action Executor if available
    if ApprovedHandler:
        # Ensure approved dir exists
        APPROVED_DIR.mkdir(exist_ok=True)
        observer.schedule(ApprovedHandler(), str(APPROVED_DIR), recursive=False)
        logger.info(f"Action Executor monitored directory: {APPROVED_DIR}")
    else:
        logger.warning("Action Executor NOT loaded.")
    
    # Start monitoring
    observer.start()
    logger.info("Orchestrator is now monitoring for new files...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        observer.stop()
        logger.info("Stopping observer...")
        
    observer.join()
    logger.info("Orchestrator stopped")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
