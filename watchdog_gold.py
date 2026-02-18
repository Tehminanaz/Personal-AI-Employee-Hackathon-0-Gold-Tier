#!/usr/bin/env python3
"""
Gold Tier Watchdog - Digital FTE System
Monitors critical processes (Ralph Loop, Action Executor, Gmail Watcher) and ensures uptime.
Implements graceful degradation logging and captures child process output.

Usage:
    python watchdog_gold.py
"""

import os
import sys
import time
import json
import logging
import subprocess
import signal
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "Logs"
SYSTEM_OUTPUT_DIR = LOGS_DIR / "System_Output"
ACTION_LOGS = LOGS_DIR / "Action_Logs.json"
WATCHDOG_LOG = LOGS_DIR / "watchdog_gold.log"

# Ensure log directories exist
LOGS_DIR.mkdir(exist_ok=True)
SYSTEM_OUTPUT_DIR.mkdir(exist_ok=True)

# Processes to monitor
MONITORED_SCRIPTS = [
    "gmail_watcher.py",
    "ralph_loop.py",
    "action_executor.py",
    "weekly_audit_scheduler.py"
]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(WATCHDOG_LOG, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WatchdogGold")

class ProcessManager:
    def __init__(self):
        self.processes = {}  # {script_name: subprocess.Popen}
        self.output_files = {} # {script_name: (stdout_handle, stderr_handle, stderr_path)}
        self.restart_counts = {name: 0 for name in MONITORED_SCRIPTS}

    def log_degraded_state(self, service_name, error_msg):
        """Log degraded state to Action_Logs.json"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "file": "SYSTEM_WATCHDOG",
            "type": "SYSTEM_ALERT",
            "status": "DEGRADED_STATE",
            "details": f"Service {service_name} failed: {error_msg}. Restarting...",
            "financial_impact": "$0.00",
            "approval_status": "NOT_REQUIRED"
        }
        
        try:
            logs = []
            if ACTION_LOGS.exists():
                with open(ACTION_LOGS, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            
            logs.append(entry)
            
            with open(ACTION_LOGS, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to write to Action Logs: {e}")

    def start_process(self, script_name):
        """Start a python script as a subprocess with output captured."""
        script_path = BASE_DIR / script_name
        
        # Absolute path validation
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return

        try:
            logger.info(f"Starting {script_name}...")
            
            # Prepare Log Files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = script_name.replace('.py', '')
            out_log = SYSTEM_OUTPUT_DIR / f"{clean_name}_{timestamp}.out"
            err_log = SYSTEM_OUTPUT_DIR / f"{clean_name}_{timestamp}.err"
            
            stdout_f = open(out_log, 'w', encoding='utf-8')
            stderr_f = open(err_log, 'w', encoding='utf-8')
            
            # Store handles and path to close/read later
            self.output_files[script_name] = (stdout_f, stderr_f, err_log)

            # Prepare Environment
            env = os.environ.copy()
            
            # DETERMINE PYTHON EXECUTABLE
            # Try to find the local venv manually to FORCE consistent environment
            # This fixes the "ModuleNotFoundError" even if started from global python
            venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                python_exe = str(venv_python)
                # logger.info(f"Using VENV Python: {python_exe}")
            else:
                # Fallback to whatever started this script
                python_exe = sys.executable

            # Run with chosen python and absolute path, setting CWD explicitly
            proc = subprocess.Popen(
                [python_exe, str(script_path.resolve())],
                cwd=str(BASE_DIR),
                env=env,
                stdout=stdout_f,
                stderr=stderr_f,
                shell=False
            )
            
            self.processes[script_name] = proc
            logger.info(f"Started {script_name} (PID: {proc.pid}) -> Logs: {SYSTEM_OUTPUT_DIR.name}/")
            return proc
            
        except Exception as e:
            logger.error(f"Failed to start {script_name}: {e}")
            return None

    def print_crash_tail(self, script_name, lines=5):
        """Prints the last few lines of the error log for a crashed script."""
        if script_name not in self.output_files:
            return

        _, _, err_path = self.output_files[script_name]
        
        if not err_path.exists():
            return
            
        try:
            logger.error(f"===== LAST {lines} LINES OF ERROR LOG FOR {script_name} =====")
            # Read all lines then take last N
            with open(err_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.readlines()
                tail = content[-lines:] if len(content) > lines else content
                for line in tail:
                    print(f"[{script_name}] {line.strip()}")
            logger.error("==========================================================")
        except Exception as e:
            logger.error(f"Could not read error log: {e}")

    def monitor(self):
        """Main monitoring loop."""
        logger.info("Starting Gold Tier Watchdog...")
        logger.info(f"Monitoring: {MONITORED_SCRIPTS}")
        
        # Initial start
        for script in MONITORED_SCRIPTS:
            self.start_process(script)

        try:
            while True:
                for script in MONITORED_SCRIPTS:
                    proc = self.processes.get(script)
                    
                    if proc is None:
                        # Never started or failed to start
                        self.start_process(script)
                        continue

                    # Check if process is dead
                    return_code = proc.poll()
                    if return_code is not None:
                        # Handle Clean Exit vs Warning
                        if return_code == 0:
                            logger.info(f"{script} exited cleanly (Loop/Done). Restarting cycle...")
                        else:
                            logger.warning(f"{script} crashed with code {return_code}. Restarting...")
                            # Increment restart count only for actual crashes
                            self.restart_counts[script] += 1
                            
                            # DEBUG ALERT: If > 3 crashes, print tail
                            if self.restart_counts[script] >= 3:
                                self.print_crash_tail(script)

                        # Close old file handles
                        if script in self.output_files:
                            o, e, _ = self.output_files[script]
                            try:
                                o.close()
                                e.close()
                            except: pass
                            del self.output_files[script]

                        # Log degraded state (Only for non-zero)
                        if return_code != 0:
                            self.log_degraded_state(script, f"Crashed (Exit Code: {return_code})")
                        
                        # Restart
                        time.sleep(2)  # Brief pause before restart
                        self.start_process(script)

                time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Stopping all monitored processes...")
        for name, proc in self.processes.items():
            if proc.poll() is None:
                logger.info(f"Terminating {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            
            # Close file handles
            if name in self.output_files:
                o, e, _ = self.output_files[name]
                try:
                    o.close()
                    e.close()
                except: pass
        
        sys.exit(0)

if __name__ == "__main__":
    manager = ProcessManager()
    manager.monitor()
