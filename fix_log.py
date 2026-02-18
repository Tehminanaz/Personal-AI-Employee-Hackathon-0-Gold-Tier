import json
from datetime import datetime

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Remove the incorrect entry first
logs = [entry for entry in logs if entry.get('file') != 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md']

# Create the correct log entry
new_entry = {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "file": "P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md",
    "type": "EMAIL",
    "status": "SUCCESS",
    "details": "Created response to urgent AI project proposal request with requirements gathering questionnaire",
    "financial_impact": "$0.00",
    "approval_status": "PENDING"
}

# Append the new entry
logs.append(new_entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(logs, f, indent=2)