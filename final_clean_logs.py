import json

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Filter entries to keep only one success entry for our specific file
filtered_logs = []
files_seen = {}

for entry in logs:
    file_name = entry.get('file')

    # If this is our specific file
    if file_name == 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md':
        status = entry.get('status')

        # If we haven't recorded any entry for this file yet
        if file_name not in files_seen:
            # Only add if it's a success entry
            if status == 'SUCCESS':
                filtered_logs.append(entry)
                files_seen[file_name] = True
        # If we've already added a success entry, skip all others
    else:
        # For other files, add normally
        filtered_logs.append(entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(filtered_logs, f, indent=2)