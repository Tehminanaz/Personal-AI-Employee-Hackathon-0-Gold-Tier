#!/usr/bin/env python3
"""
CEO Audit Generator - Digital FTE System (Gold Tier Enhanced)
Generates a data-driven, critical, strategic weekly audit in 'Bezos Tone'.

Logic:
1. Analyzes Logs/Action_Logs.json for success rates and error patterns.
2. Scans 04_Archive/ for completed task volume and types.
3. Reads 05_Accounting/Monthly_Budget_2026.md for financial health.
4. Fetches Odoo financial data (invoices, payments, receivables).
5. Reads Management/Social_Media_Summary.md for engagement metrics.
6. Generates Management/CEO_WEEKLY_BRIEFING.md.

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
MANAGEMENT_DIR = BASE_DIR / "Management"
SOCIAL_SUMMARY_FILE = MANAGEMENT_DIR / "Social_Media_Summary.md"
OUTPUT_FILE = MANAGEMENT_DIR / "CEO_WEEKLY_BRIEFING.md"

# Import Odoo MCP (optional - graceful degradation if not available)
try:
    from odoo_mcp_server import OdooMCPServer
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False
    logger.warning("Odoo MCP not available - financial data will be limited")

# Import social media summary
try:
    from social_media_summary import get_weekly_summary, generate_summary_report
    SOCIAL_AVAILABLE = True
except ImportError:
    SOCIAL_AVAILABLE = False
    logger.warning("Social media summary not available")

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

def analyze_odoo_financials():
    """Fetch financial data from Odoo if available."""
    if not ODOO_AVAILABLE:
        return {"status": "UNAVAILABLE", "message": "Odoo integration not configured"}
    
    try:
        server = OdooMCPServer()
        
        # Fetch recent transactions
        transactions = server.fetch_recent_transactions(days=7)
        
        # Calculate metrics
        total_invoices = len([t for t in transactions if t['type'] == 'invoice'])
        total_revenue = sum(t['amount'] for t in transactions if t['type'] == 'invoice' and t['state'] == 'posted')
        pending_revenue = sum(t['amount'] for t in transactions if t['type'] == 'invoice' and t['state'] == 'draft')
        
        # Get accounts receivable (if available)
        try:
            ar_balance = server.get_account_balance("100000")  # Adjust account code as needed
        except:
            ar_balance = None
        
        return {
            "total_invoices": total_invoices,
            "total_revenue": total_revenue,
            "pending_revenue": pending_revenue,
            "ar_balance": ar_balance,
            "transactions": transactions[:5]  # Last 5 for detail
        }
        
    except Exception as e:
        logger.error(f"Error fetching Odoo data: {e}")
        return {"status": "ERROR", "message": str(e)}

def analyze_social_media():
    """Analyze social media performance from summary file."""
    if not SOCIAL_AVAILABLE:
        return {"status": "UNAVAILABLE", "message": "Social media tracking not configured"}
    
    try:
        # Get weekly summary
        summary = get_weekly_summary()
        
        if not summary or summary.get('total_posts', 0) == 0:
            return {"status": "NO_DATA", "message": "No social media posts in last 7 days"}
        
        return {
            "total_posts": summary['total_posts'],
            "by_platform": summary['by_platform'],
            "recent_posts": summary['posts'][-3:] if summary['posts'] else []
        }
        
    except Exception as e:
        logger.error(f"Error analyzing social media: {e}")
        return {"status": "ERROR", "message": str(e)}

def generate_report(perf_data, fin_data, odoo_data, social_data):
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

    # Odoo Financial Data
    report += "\n## 4. Odoo Financial Performance (Real-Time Revenue)\n"
    
    if odoo_data.get("status") in ["UNAVAILABLE", "ERROR"]:
        report += f"**NOTE:** {odoo_data.get('message', 'Odoo data unavailable')}\n"
    else:
        report += f"*   **Invoices This Week:** {odoo_data.get('total_invoices', 0)}\n"
        report += f"*   **Revenue (Posted):** ${odoo_data.get('total_revenue', 0):,.2f}\n"
        report += f"*   **Revenue (Pending):** ${odoo_data.get('pending_revenue', 0):,.2f}\n"
        
        if odoo_data.get('ar_balance'):
            report += f"*   **Accounts Receivable:** ${odoo_data['ar_balance']:,.2f}\n"
        
        if odoo_data.get('pending_revenue', 0) > odoo_data.get('total_revenue', 0):
            report += "\n**ACTION REQUIRED:** Pending invoices exceed posted revenue. Accelerate approval workflow.\n"
    
    # Social Media Performance
    report += "\n## 5. Social Media Engagement (Brand Velocity)\n"
    
    if social_data.get("status") in ["UNAVAILABLE", "ERROR", "NO_DATA"]:
        report += f"**NOTE:** {social_data.get('message', 'No social media data')}\n"
    else:
        report += f"*   **Total Posts This Week:** {social_data.get('total_posts', 0)}\n"
        report += "*   **By Platform:**\n"
        
        for platform, count in social_data.get('by_platform', {}).items():
            report += f"    *   {platform}: {count}\n"
        
        # Show recent posts
        if social_data.get('recent_posts'):
            report += "\n*   **Recent Posts:**\n"
            for post in social_data['recent_posts']:
                report += f"    *   {post['platform']} ({post['timestamp']}): {post['content'][:50]}...\n"
        
        # Performance insights
        total_posts = social_data.get('total_posts', 0)
        if total_posts < 5:
            report += "\n**ALERT:** Social media output is below target (5+ posts/week). Increase content velocity.\n"
        elif total_posts > 15:
            report += "\n**NOTE:** High social media output. Ensure quality is maintained over quantity.\n"
    
    report += """
## 6. Strategic Memos & Narratives
**Subject: Raising the Bar on Automation**

We must refuse to accept "good enough" in our automation logic. 
If a task requires manual intervention more than once, the process is broken. 
Fix the root cause, do not patch the symptom.

**Next Week's Mandate:**
1.  Eliminate one manual touchpoint from the 'Financial Controller' workflow.
2.  Increase 'Social Media' output velocity by 20% without sacrificing quality.
3.  Ensure all Odoo invoices are approved within 24 hours of creation.

*End of Report.*
"""

    # Ensure directory exists
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Audit generated at {OUTPUT_FILE}")
    print(f"DONE: Generated {OUTPUT_FILE}")

def main():
    logger.info("Starting Weekly CEO Briefing Generation...")
    
    # Gather all data sources
    logs = load_logs()
    perf_data = analyze_performance(logs)
    fin_data = analyze_financials()
    odoo_data = analyze_odoo_financials()
    social_data = analyze_social_media()
    
    # Generate comprehensive report
    generate_report(perf_data, fin_data, odoo_data, social_data)
    
    logger.info("CEO Briefing generation complete")

if __name__ == "__main__":
    main()
