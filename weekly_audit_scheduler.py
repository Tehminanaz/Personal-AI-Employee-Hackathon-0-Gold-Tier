#!/usr/bin/env python3
"""
Weekly Audit Scheduler - Digital FTE System
Automatically triggers CEO audit generation every Sunday at 8 PM.

This scheduler creates a trigger file that the orchestrator picks up
and processes using the generate_ceo_audit.py script.

Usage:
    python weekly_audit_scheduler.py
    
The scheduler runs as a daemon and is monitored by watchdog_gold.py.
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
INBOX_DIR = BASE_DIR / "00_Inbox"
MANAGEMENT_DIR = BASE_DIR / "Management"
LOGS_DIR = BASE_DIR / "Logs"

# Ensure directories exist
INBOX_DIR.mkdir(exist_ok=True)
MANAGEMENT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
LOG_FILE = LOGS_DIR / "scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WeeklyAuditScheduler")


def trigger_weekly_audit():
    """
    Create trigger file for weekly CEO audit.
    
    This file is picked up by the orchestrator which then
    executes generate_ceo_audit.py to create the briefing.
    """
    try:
        logger.info("=" * 80)
        logger.info("Triggering Weekly CEO Audit")
        logger.info("=" * 80)
        
        # Create trigger file
        trigger_file = INBOX_DIR / "RUN_AUDIT.md"
        
        content = f"""---
type: system_trigger
priority: P0
created: {datetime.now().isoformat()}
---

# Weekly CEO Audit Trigger

This file triggers the automated weekly business audit.

## Audit Scope
- Financial performance (revenue, expenses)
- Task completion metrics
- Social media engagement
- System health
- Proactive recommendations

## Expected Output
`Management/CEO_WEEKLY_BRIEFING.md` will be generated with:
- Executive summary
- Key metrics
- Bottlenecks identified
- Strategic recommendations

---

**Triggered by:** Weekly Audit Scheduler
**Schedule:** Every Sunday at 8:00 PM
**Next Run:** {(datetime.now()).strftime('%Y-%m-%d 20:00:00')}
"""
        
        with open(trigger_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Audit trigger created: {trigger_file.name}")
        logger.info("Waiting for orchestrator to process...")
        
        # Monitor for completion (optional)
        briefing_file = MANAGEMENT_DIR / "CEO_WEEKLY_BRIEFING.md"
        timeout = 600  # 10 minutes timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if briefing_file.exists():
                # Check if file was updated recently (within last 5 minutes)
                mtime = briefing_file.stat().st_mtime
                if time.time() - mtime < 300:
                    logger.info(f"✅ CEO briefing generated: {briefing_file.name}")
                    break
            time.sleep(10)
        else:
            logger.warning("⚠️ Audit generation timeout. Check orchestrator logs.")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to trigger weekly audit: {e}", exc_info=True)


def run_scheduler():
    """
    Main scheduler loop.
    
    Schedules weekly audit for every Sunday at 8:00 PM.
    Runs indefinitely until interrupted.
    """
    logger.info("=" * 80)
    logger.info("Weekly Audit Scheduler Starting")
    logger.info("=" * 80)
    logger.info("Schedule: Every Sunday at 8:00 PM")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Schedule weekly audit
    schedule.every().sunday.at("20:00").do(trigger_weekly_audit)
    
    # For testing: Also allow manual trigger via file
    # If TRIGGER_AUDIT_NOW.md appears in inbox, run immediately
    
    logger.info("Scheduler initialized. Waiting for scheduled time...")
    
    try:
        while True:
            # Run pending scheduled tasks
            schedule.run_pending()
            
            # Check for manual trigger
            manual_trigger = INBOX_DIR / "TRIGGER_AUDIT_NOW.md"
            if manual_trigger.exists():
                logger.info("Manual audit trigger detected!")
                trigger_weekly_audit()
                # Remove manual trigger file
                manual_trigger.unlink()
            
            # Sleep for 1 minute between checks
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}", exc_info=True)
    finally:
        logger.info("=" * 80)
        logger.info("Weekly Audit Scheduler Stopped")
        logger.info("=" * 80)


def main():
    """Entry point for the scheduler."""
    # Check if running as test
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running in TEST mode - triggering audit immediately")
        trigger_weekly_audit()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
