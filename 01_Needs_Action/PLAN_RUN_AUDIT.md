# PLAN: RUN_AUDIT Execution

## Executive Summary

**Situation:** The system has detected a RUN_AUDIT.md trigger file in the 00_Inbox directory, which requires immediate execution of the CEO audit generation process.

**Complication:** The audit process is critical for business operations and must follow proper protocols per the Company Handbook, including data accuracy, proper formatting, and executive communication standards.

**Question:** How should the RUN_AUDIT.md trigger be processed to generate the CEO weekly briefing according to established procedures?

**Answer:** Execute the python generate_ceo_audit.py script to produce the Management/CEO_WEEKLY_BRIEFING.md report, following the Chief of Staff narrative standards.

## Context

Based on CLAUDE.md operational rules, when a RUN_AUDIT.md file appears in the Inbox, the system must execute `python generate_ceo_audit.py` immediately and create the report in the Management/ directory. This follows the automated auditing protocol described in the Chief of Staff skill, which requires reading Logs/Action_Logs.json to calculate success rates and generate narrative reports in the "Six-Page Narrative" style with a "Jeff Bezos" tone (data-driven, high standards).

## Analysis

The RUN_AUDIT.md file in 00_Inbox serves as a system trigger for the automated audit process. According to the Company Handbook, all tasks must go through a planning phase before execution. The Chief of Staff skill defines the audit process as:

1. Reading Logs/Action_Logs.json
2. Calculating Success Rate = (Count "SUCCESS") / (Total Entries)
3. Generating a Narrative Report in the "Six-Page Narrative" style
4. Using a "Jeff Bezos" tone - data-driven, high standards, no fluff
5. Following a specific structure: Executive Summary, Operational Health, Action Items

### Current State
- RUN_AUDIT.md exists in 00_Inbox/
- The generate_ceo_audit.py script should exist in the root directory
- Logs/Action_Logs.json should contain historical data for analysis
- The Management/ directory should exist for the output

### Resources Required
- Python runtime environment
- Access to Logs/Action_Logs.json file
- Write access to Management/ directory
- The generate_ceo_audit.py script

## Recommendation

Execute the following action plan to process the RUN_AUDIT trigger:

1. Verify the existence of required files and directories
2. Execute the python generate_ceo_audit.py script
3. Confirm the successful creation of the CEO weekly briefing report
4. Log the action to Logs/Action_Logs.json
5. Move the RUN_AUDIT.md trigger file to the 04_Archive/ directory

## Execution Plan

### Step 1: Pre-Execution Verification
- [ ] Verify generate_ceo_audit.py exists in root directory
- [ ] Verify Logs/Action_Logs.json exists and contains data
- [ ] Verify Management/ directory exists for output
- [ ] Verify 04_Archive/ directory exists for archiving

### Step 2: Execute Audit Generation
- [ ] Run: python generate_ceo_audit.py
- [ ] Monitor for successful completion
- [ ] Verify output file created in Management/ directory

### Step 3: Post-Execution Validation
- [ ] Confirm report follows Six-Page Narrative format
- [ ] Verify data accuracy from Action_Logs.json
- [ ] Ensure "Jeff Bezos" tone (data-driven, high standards)

### Step 4: System Cleanup
- [ ] Move RUN_AUDIT.md from 00_Inbox/ to 04_Archive/
- [ ] Update Action_Logs.json with this audit execution event
- [ ] Verify all file operations completed successfully

## Risks and Mitigations

### Key Risks
- **Script execution failure**: The generate_ceo_audit.py script may have errors or missing dependencies
- **Missing data**: Action_Logs.json may be missing or corrupted
- **Insufficient permissions**: Unable to write to Management/ directory
- **Malformed output**: Generated report doesn't follow required format

### Mitigation Strategies
- **Pre-execution checks**: Verify all required files exist before execution
- **Error handling**: Capture and log any execution errors for troubleshooting
- **Backup verification**: Ensure original RUN_AUDIT.md is preserved until successful completion
- **Validation**: Check output format before finalizing the process

### Contingency Plans
- If script fails: Create an escalation report in 02_Pending_Approval/ detailing the issue
- If data missing: Document the gap and request manual intervention
- If permissions issue: Escalate as a system administration concern

## Success Criteria

- [ ] CEO weekly briefing report generated in Management/ directory
- [ ] Report follows Six-Page Narrative format with appropriate data
- [ ] RUN_AUDIT.md trigger file processed and archived
- [ ] Action log updated with audit execution record
- [ ] All steps completed without errors

## Appendix

### FAQ
Q: What if the generate_ceo_audit.py script doesn't exist?
A: Create an escalation report in 02_Pending_Approval/ requesting the missing script.

Q: What if the Action_Logs.json is empty?
A: Generate the report noting the lack of historical data for trend analysis.

Q: How often should audits be run?
A: Per the Chief of Staff skill, this is triggered by RUN_AUDIT.md appearing in the inbox, suggesting it's demand-driven rather than scheduled.

### Definitions
- **Six-Page Narrative**: Executive report format with Executive Summary, Context, Analysis, Recommendation, Risks and Mitigations, and Appendix
- **Jeff Bezos tone**: Data-driven, high standards, no fluff approach to executive communication
- **Success Rate**: Calculation of (Count "SUCCESS") / (Total Entries) from Action_Logs.json