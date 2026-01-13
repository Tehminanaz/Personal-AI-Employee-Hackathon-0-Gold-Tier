#!/usr/bin/env python3
"""
CEO Audit Generator - Digital FTE System
Generates a data-driven, critical, strategic weekly audit in 'Bezos Tone'.

Logic:
1. Analyzes Logs/Action_Logs.json for success rates and error patterns.
2. Scans 04_Archive/ for completed task volume and types.
3. Reads 05_Accounting/Monthly_Budget_2026.md for financial health.
4. Generates Management/WEEKLY_STRATEGY_AUDIT.md.

Usage:
    python generate_ceo_audit.py
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_FILE = BASE_DIR / "Logs" / "Action_Logs.json"
ARCHIVE_DIR = BASE_DIR / "04_Archive"
ACCOUNTING_DIR = BASE_DIR / "05_Accounting"
BUDGET_FILE = ACCOUNTING_DIR / "Monthly_Budget_2026.md"
OUTPUT_FILE = BASE_DIR / "Management" / "WEEKLY_STRATEGY_AUDIT.md"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CEO_Audit")

def load_logs():
    """Load action logs."""
    if not LOGS_FILE.exists():
        logger.warning("No Action_Logs.json found. Returning empty list.")
        return []
    try:
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Action_Logs.json is corrupted.")
        return []

def analyze_performance(logs):
    """Analyze success rates and task types."""
    if not logs:
        return {"total": 0, "success_rate": 0, "types": {}}
    
    total = len(logs)
    successes = sum(1 for log in logs if log.get("status") == "SUCCESS")
    success_rate = (successes / total) * 100 if total > 0 else 0
    
    task_types = Counter(log.get("type", "UNKNOWN") for log in logs)
    
    return {
        "total": total,
        "success_rate": success_rate,
        "types": dict(task_types)
    }

def analyze_financials():
    """Parse budget file for financial status."""
    if not BUDGET_FILE.exists():
        return {"status": "MISSING_DATA", "alerts": ["Budget file not found"]}
    
    try:
        with open(BUDGET_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing logic (looking for Total row)
        # Assuming format: | **Total** | **$1,150.00** | **$0.00** | ...
        match = re.search(r'\|\s*\*\*Total\*\*\s*\|\s*\*\*(\$[\d,.]+)\*\*\s*\|\s*\*\*(\$[\d,.]+)\*\*', content)
        
        if match:
            budget_str = match.group(1).replace('$', '').replace(',', '')
            actual_str = match.group(2).replace('$', '').replace(',', '')
            return {
                "budget": float(budget_str),
                "actual": float(actual_str),
                "variance": float(budget_str) - float(actual_str)
            }
        return {"status": "PARSE_ERROR", "alerts": ["Could not parse totals from budget file"]}
            
    except Exception as e:
        return {"status": "ERROR", "alerts": [str(e)]}

def generate_report(perf_data, fin_data):
    """Generate the Markdown report in Bezos Tone."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # Bezos Tone: Direct, No Fluff, Narrative Structure
    
    report = f"""# Weekly Strategy Audit / {timestamp}
**To:** CEO / Stakeholders
**From:** Digital FTE Audit System (generate_ceo_audit.py)

---

## 1. Executive Summary (The "So What?")
"""
    
    if perf_data['success_rate'] < 95:
        report += f"**CRITICAL:** System reliability is at {perf_data['success_rate']:.1f}%. This is unacceptable. We are failing to meet the Six Sigma standard. Immediate investigation into error patterns is required.\n\n"
    else:
        report += f"System operating within nominal parameters ({perf_data['success_rate']:.1f}% success rate). Focus needs to shift from stability to velocity.\n\n"

    report += f"""
## 2. Operational Metrics (Truth in Data)
*   **Total Actions:** {perf_data['total']}
*   **Success Rate:** {perf_data['success_rate']:.1f}%
*   **Task Distribution:**
"""
    for type_, count in perf_data['types'].items():
        report += f"    *   {type_}: {count}\n"

    report += "\n## 3. Financial Health (Cash is Reality)\n"
    
    if "alerts" in fin_data:
         for alert in fin_data["alerts"]:
             report += f"**WARNING:** {alert}\n"
    else:
        burn_rate = (fin_data['actual'] / fin_data['budget']) * 100 if fin_data['budget'] > 0 else 0
        report += f"*   **Budget:** ${fin_data['budget']:,.2f}\n"
        report += f"*   **Actual Spend:** ${fin_data['actual']:,.2f}\n"
        report += f"*   **Variance:** ${fin_data['variance']:,.2f}\n"
        
        if burn_rate > 90:
             report += "**ALERT:** Spend is nearing budget cap. Freeze all non-essential P2/P3 expenses immediately.\n"
        elif burn_rate < 50:
             report += "**NOTE:** Underspend detailed. Resources are being underutilized. Acceleration required.\n"

    report += """
## 4. Strategic Memos & Narratives
**Subject: Raising the Bar on Automation**

We must refuse to accept "good enough" in our automation logic. 
If a task requires manual intervention more than once, the process is broken. 
Fix the root cause, do not patch the symptom.

**Next Week's Mandate:**
1.  Eliminate one manual touchpoint from the 'Financial Controller' workflow.
2.  Increase 'Social Media' output velocity by 20% without sacrificing the Triple-Draft rule.

*End of Report.*
"""

    # Ensure directory exists
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Audit generated at {OUTPUT_FILE}")
    print(f"DONE: Generated {OUTPUT_FILE}")

def main():
    logger.info("Starting Weekly Strategy Audit...")
    logs = load_logs()
    perf_data = analyze_performance(logs)
    fin_data = analyze_financials()
    generate_report(perf_data, fin_data)

if __name__ == "__main__":
    main()
