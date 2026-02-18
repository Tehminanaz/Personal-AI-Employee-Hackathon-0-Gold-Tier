import json

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Filter out the failure entries for our specific file, keeping only the success one
filtered_logs = []
success_found = False

for entry in logs:
    file_name = entry.get('file')
    status = entry.get('status')

    if file_name == 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md':
        if status == 'SUCCESS' and not success_found:
            # Keep the first success entry
            filtered_logs.append(entry)
            success_found = True
        elif status == 'FAILURE':
            # Skip failure entries for this file
            continue
        else:
            # For any other status, skip
            continue
    else:
        # Keep all other entries
        filtered_logs.append(entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(filtered_logs, f, indent=2)