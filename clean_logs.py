import json
from datetime import datetime

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Create a set to track unique file entries
seen_files = set()
unique_logs = []

for entry in logs:
    file_name = entry.get('file')
    # Skip entries that are for our specific file unless we haven't seen them yet
    if file_name == 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md':
        if 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118' not in seen_files:
            # Keep the SUCCESS entry if it exists, or the most recent one
            success_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "file": "P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md",
                "type": "EMAIL",
                "status": "SUCCESS",
                "details": "Created response to urgent AI project proposal request with requirements gathering questionnaire",
                "financial_impact": "$0.00",
                "approval_status": "PENDING"
            }
            unique_logs.append(success_entry)
            seen_files.add('P1_EMAIL_Response_AI_Project_Proposal_Request_20260118')
    else:
        unique_logs.append(entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(unique_logs, f, indent=2)