# Get the current date in ISO format
$date = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"

# Define the new log entry
$logEntry = @"
{
  "timestamp": "$date",
  "file": "P1_EMAIL_Response_AI_Project_Proposal_Request_20260118.md",
  "type": "EMAIL",
  "status": "DRAFTED",
  "details": "Created professional response to urgent AI project proposal request from Tehmina Naz, expressing interest and proposing meeting times for next week",
  "financial_impact": "$0.00",
  "approval_status": "PENDING"
}
"@

# Read the current content of the log file
$content = Get-Content "C:\Users\Kashan\Documents\Digital labor\digital_labor2 - Copy\Logs\Action_Logs.json" -Raw

# Remove the closing bracket and add the new entry
$updatedContent = $content.TrimEnd(']')
$updatedContent += ','
$updatedContent += "`n  $logEntry"
$updatedContent += "`n]"

# Write the updated content back to the file
Set-Content -Path "C:\Users\Kashan\Documents\Digital labor\digital_labor2 - Copy\Logs\Action_Logs.json" -Value $updatedContent