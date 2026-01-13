#!/usr/bin/env python3
"""
Ralph Wiggum Loop - Continuous Iteration Pattern
"I'm helping!" - Keeps processing until TASK_COMPLETE or inbox empty.

Gold Tier Feature: Autonomous continuous iteration loop.

Usage:
    python ralph_loop.py
    python ralph_loop.py --max-iterations 100
    python ralph_loop.py --delay 5
    python ralph_loop.py --dry-run

Stop Conditions:
    1. TASK_COMPLETE.md file detected in inbox
    2. Inbox is empty (no .md files)
    3. Max iterations reached (safety)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
INBOX_DIR = BASE_DIR / "00_Inbox"
LOGS_DIR = BASE_DIR / "Logs"
MANAGEMENT_DIR = BASE_DIR / "Management"

# Ensure directories exist
INBOX_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
MANAGEMENT_DIR.mkdir(exist_ok=True)

# Loop Settings
DEFAULT_MAX_ITERATIONS = 50
DEFAULT_ITERATION_DELAY = 3  # seconds
TASK_COMPLETE_SIGNAL = "TASK_COMPLETE.md"
STATUS_FILE = MANAGEMENT_DIR / "Loop_Status.md"

# Logging setup
LOG_FILE = LOGS_DIR / f"ralph_loop_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RalphLoop")


class RalphWiggumLoop:
    """
    Continuous iteration loop that processes files until completion.
    
    Named after Ralph Wiggum's "I'm helping!" - keeps iterating until
    explicitly told to stop or work is complete.
    """
    
    def __init__(
        self,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        delay: int = DEFAULT_ITERATION_DELAY,
        dry_run: bool = False
    ):
        """
        Initialize Ralph Wiggum Loop.
        
        Args:
            max_iterations: Maximum number of iterations (safety limit)
            delay: Seconds to wait between iterations
            dry_run: If True, simulate without actual processing
        """
        self.max_iterations = max_iterations
        self.delay = delay
        self.dry_run = dry_run
        self.iteration_count = 0
        self.files_processed = 0
        self.start_time = datetime.now()
        
        logger.info(f"Initialized Ralph Wiggum Loop")
        logger.info(f"Max Iterations: {self.max_iterations}")
        logger.info(f"Iteration Delay: {self.delay}s")
        logger.info(f"Dry Run: {self.dry_run}")
    
    def check_task_complete_signal(self) -> bool:
        """
        Check if TASK_COMPLETE signal file exists.
        
        Returns:
            True if signal detected, False otherwise
        """
        signal_file = INBOX_DIR / TASK_COMPLETE_SIGNAL
        
        if signal_file.exists():
            logger.info(f"✅ TASK_COMPLETE signal detected: {signal_file.name}")
            return True
        
        return False
    
    def is_inbox_empty(self) -> bool:
        """
        Check if inbox has any processable files.
        
        Returns:
            True if inbox is empty, False otherwise
        """
        files = self.get_inbox_files()
        return len(files) == 0
    
    def get_inbox_files(self) -> List[Path]:
        """
        Get list of files to process from inbox.
        
        Excludes:
            - TASK_COMPLETE.md (signal file)
            - Non-.md files
        
        Returns:
            List of Path objects for processable files
        """
        all_files = list(INBOX_DIR.glob("*.md"))
        
        # Filter out signal files
        processable_files = [
            f for f in all_files
            if not f.name.startswith("TASK_COMPLETE")
        ]
        
        return processable_files
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single file using orchestrator logic.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would process: {file_path.name}")
                time.sleep(0.5)  # Simulate processing time
                return True
            
            # Import orchestrator handler
            from orchestrator import InboxHandler
            
            # Create handler and process file
            handler = InboxHandler()
            handler.process_file(file_path)
            
            logger.info(f"✅ Processed: {file_path.name}")
            self.files_processed += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path.name}: {e}", exc_info=True)
            return False
    
    def update_status_file(self, status: str = "RUNNING") -> None:
        """
        Update real-time status file for monitoring.
        
        Args:
            status: Current status (RUNNING, COMPLETED, STOPPED)
        """
        try:
            files_remaining = len(self.get_inbox_files())
            elapsed_time = datetime.now() - self.start_time
            
            content = f"""# Ralph Wiggum Loop Status

**Status:** {status}
**Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Elapsed Time:** {str(elapsed_time).split('.')[0]}
**Current Iteration:** {self.iteration_count}/{self.max_iterations}
**Files Processed:** {self.files_processed}
**Files Remaining:** {files_remaining}

## Stop Conditions
- {'[x]' if self.check_task_complete_signal() else '[ ]'} TASK_COMPLETE signal detected
- {'[x]' if self.is_inbox_empty() else '[ ]'} Inbox empty
- {'[x]' if self.iteration_count >= self.max_iterations else '[ ]'} Max iterations reached

## Recent Activity
Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"Error updating status file: {e}")
    
    def run(self) -> None:
        """
        Main loop execution.
        
        Continuously processes files until one of the stop conditions is met:
        1. TASK_COMPLETE signal detected
        2. Inbox is empty
        3. Max iterations reached
        """
        logger.info("=" * 80)
        logger.info("🔄 Ralph Wiggum Loop Started - 'I'm helping!'")
        logger.info("=" * 80)
        
        try:
            while self.iteration_count < self.max_iterations:
                self.iteration_count += 1
                logger.info("")
                logger.info(f"{'=' * 80}")
                logger.info(f"📍 Iteration {self.iteration_count}/{self.max_iterations}")
                logger.info(f"{'=' * 80}")
                
                # Update status file
                self.update_status_file("RUNNING")
                
                # Stop Condition 1: TASK_COMPLETE signal
                if self.check_task_complete_signal():
                    logger.info("🛑 Stop Condition Met: TASK_COMPLETE signal detected")
                    self.update_status_file("COMPLETED")
                    break
                
                # Stop Condition 2: Empty inbox
                if self.is_inbox_empty():
                    logger.info("🛑 Stop Condition Met: Inbox is empty")
                    self.update_status_file("COMPLETED")
                    break
                
                # Get files to process
                files = self.get_inbox_files()
                logger.info(f"📂 Found {len(files)} file(s) to process")
                
                # Process each file
                for i, file in enumerate(files, 1):
                    logger.info(f"📄 Processing file {i}/{len(files)}: {file.name}")
                    self.process_file(file)
                
                # Check if we should continue
                if self.iteration_count < self.max_iterations:
                    logger.info(f"⏳ Waiting {self.delay}s before next iteration...")
                    time.sleep(self.delay)
            
            # Stop Condition 3: Max iterations reached
            if self.iteration_count >= self.max_iterations:
                logger.warning("⚠️ Stop Condition Met: Max iterations reached (safety limit)")
                self.update_status_file("STOPPED")
            
        except KeyboardInterrupt:
            logger.info("⚠️ User interrupted loop (Ctrl+C)")
            self.update_status_file("INTERRUPTED")
        
        except Exception as e:
            logger.error(f"❌ Fatal error in loop: {e}", exc_info=True)
            self.update_status_file("ERROR")
        
        finally:
            # Final summary
            elapsed_time = datetime.now() - self.start_time
            logger.info("")
            logger.info("=" * 80)
            logger.info("🏁 Ralph Wiggum Loop Completed")
            logger.info("=" * 80)
            logger.info(f"Total Iterations: {self.iteration_count}")
            logger.info(f"Files Processed: {self.files_processed}")
            logger.info(f"Elapsed Time: {str(elapsed_time).split('.')[0]}")
            logger.info(f"Status File: {STATUS_FILE}")
            logger.info("=" * 80)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Loop - Continuous iteration until task complete",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ralph_loop.py                    # Default settings
  python ralph_loop.py --max-iterations 100  # Custom max iterations
  python ralph_loop.py --delay 5          # 5 second delay between iterations
  python ralph_loop.py --dry-run          # Simulate without processing
  
Stop Conditions:
  1. TASK_COMPLETE.md file appears in 00_Inbox/
  2. 00_Inbox/ is empty (no .md files)
  3. Max iterations reached (safety limit)
        """
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum iterations (default: {DEFAULT_MAX_ITERATIONS})"
    )
    
    parser.add_argument(
        "--delay",
        type=int,
        default=DEFAULT_ITERATION_DELAY,
        help=f"Seconds between iterations (default: {DEFAULT_ITERATION_DELAY})"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without actual processing"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run loop
    loop = RalphWiggumLoop(
        max_iterations=args.max_iterations,
        delay=args.delay,
        dry_run=args.dry_run
    )
    
    loop.run()


if __name__ == "__main__":
    main()
