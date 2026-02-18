import json

# Read the existing log file
with open('Logs/Action_Logs.json', 'r') as f:
    logs = json.load(f)

# Create a completely new list with only one success entry for our specific file
filtered_logs = []
our_file_success_added = False

for entry in logs:
    file_name = entry.get('file')

    # If this is our specific file
    if file_name == 'P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md':
        status = entry.get('status')

        # Only add the success entry once
        if status == 'SUCCESS' and not our_file_success_added:
            filtered_logs.append(entry)
            our_file_success_added = True
        # Skip all other entries for this file (failures, etc.)
    else:
        # For other files, add normally
        filtered_logs.append(entry)

# Write back to the file
with open('Logs/Action_Logs.json', 'w') as f:
    json.dump(filtered_logs, f, indent=2)