import json
from datetime import datetime

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Filter out ALL entries for our specific file
filtered_logs = []
for entry in logs:
    file_name = entry.get('file')
    if file_name != 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md':
        filtered_logs.append(entry)

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
filtered_logs.append(new_entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(filtered_logs, f, indent=2)