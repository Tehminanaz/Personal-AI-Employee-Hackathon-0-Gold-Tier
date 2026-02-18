import json
from datetime import datetime

# Define the new log entry
log_entry = {
    "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
    "file": "P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md",
    "type": "EMAIL",
    "status": "DRAFTED",
    "details": "Created professional response to urgent AI project proposal request from Tehmina Naz, expressing interest and proposing meeting times for next week",
    "financial_impact": "$0.00",
    "approval_status": "PENDING"
}

# Load the existing logs
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Append the new entry
logs.append(log_entry)

# Write back to the file with proper formatting
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(logs, f, indent=2)