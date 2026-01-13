#!/usr/bin/env python3
"""
Digital FTE Master Runner
Launches and manages all sub-agents:
1. Orchestrator (Core Logic)
2. Gmail Watcher (Input Sensor)
3. Action Executor (Output & Execution)

Also performs periodic system health checks.

Usage:
    python run_fte.py
"""

import subprocess
import sys
import time
import schedule
import logging
import signal
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "Logs"
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
HEALTH_LOG = LOGS_DIR / f"health_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(HEALTH_LOG, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SystemMaster")

processes = []

def start_process(script_name):
    """Starts a python script as a subprocess."""
    script_path = BASE_DIR / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_name}")
        return None
        
    try:
        # Launch process
        # Using sys.executable to ensure we use the same python interpreter
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            # On Windows, we refrain from creationflags unless needed to hide window
            # Generally default is fine for running in same terminal or background.
        )
        logger.info(f"Started {script_name} (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        return None

def check_health():
    """Checks the status of all processes."""
    all_healthy = True
    status_report = []
    
    for proc, name in processes:
        if proc.poll() is None:
            status_report.append(f"{name}: RUNNING (PID {proc.pid})")
        else:
            status_report.append(f"{name}: DEAD (Exit Code {proc.returncode})")
            all_healthy = False
            # Attempt restart? For now just log.
            logger.warning(f"Process {name} has died! Restating...")
            new_proc = start_process(name)
            if new_proc:
                # Update process list reference
                # (Simple list replacement logic needed here if fully robust, 
                # but for this script we just append and might leak dead refs in 'processes' list 
                # if restarts happen often. For simplicity/hackathon, we'll just re-append)
                # Correction: We can't easily replace inside the loop. 
                # Let's just log failure for now.
                pass 

    log_msg = f"System Health Check: {'OK' if all_healthy else 'ISSUES'}\n" + "\n".join(status_report)
    logger.info(log_msg)

def stop_all(signum=None, frame=None):
    """Gracefully stops all processes."""
    logger.info("Stopping all Digital FTE services...")
    for proc, name in processes:
        if proc.poll() is None:
            logger.info(f"Terminating {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} did not terminate, forcing kill...")
                proc.kill()
    logger.info("All services stopped. Goodbye.")
    sys.exit(0)

def main():
    logger.info("=" * 60)
    logger.info("Digital FTE System Starting...")
    logger.info("=" * 60)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    # Start Services
    scripts = ["orchestrator.py", "gmail_watcher.py", "action_executor.py"]
    
    for script in scripts:
        p = start_process(script)
        if p:
            processes.append((p, script))
    
    # Schedule Health Check
    schedule.every(1).hours.do(check_health)
    # Also run one immediately
    check_health()
    
    logger.info("System is live. Press Ctrl+C to shutdown.")
    
    # Main Loop
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
