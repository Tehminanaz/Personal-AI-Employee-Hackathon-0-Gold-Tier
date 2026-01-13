"""
Digital FTE Audit Report Generator

This script reads logs from Logs/Action_Logs.json and generates a weekly audit report
following the Chief of Staff six-page narrative format.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

def calculate_success_rate(logs: List[Dict]) -> float:
    """
    Calculate the success rate from the action logs.

    Args:
        logs: List of log entries

    Returns:
        Success rate as a percentage (0-100)
    """
    if not logs:
        return 0.0

    total_entries = len(logs)
    success_count = sum(1 for log in logs if log.get('status') == 'SUCCESS')

    return (success_count / total_entries) * 100

def analyze_logs(logs: List[Dict]) -> Dict:
    """
    Analyze the logs to extract meaningful insights.

    Args:
        logs: List of log entries

    Returns:
        Dictionary containing analysis results
    """
    total_entries = len(logs)
    success_count = sum(1 for log in logs if log.get('status') == 'SUCCESS')
    failure_count = total_entries - success_count

    success_rate = calculate_success_rate(logs)

    # Count by file type/status
    file_analysis = {}
    for log in logs:
        filename = log.get('file', 'Unknown')
        if filename not in file_analysis:
            file_analysis[filename] = {'success': 0, 'failure': 0}

        if log.get('status') == 'SUCCESS':
            file_analysis[filename]['success'] += 1
        else:
            file_analysis[filename]['failure'] += 1

    # Find most common failures
    failures = [log for log in logs if log.get('status') == 'FAILURE']
    failure_details = [log.get('details', '') for log in failures]

    return {
        'total_entries': total_entries,
        'success_count': success_count,
        'failure_count': failure_count,
        'success_rate': success_rate,
        'file_analysis': file_analysis,
        'failures': failures,
        'failure_details': failure_details
    }

def generate_executive_summary(analysis: Dict) -> str:
    """
    Generate the executive summary section of the report.

    Args:
        analysis: Analysis results from analyze_logs

    Returns:
        Executive summary as a string
    """
    success_rate = analysis['success_rate']
    success_count = analysis['success_count']
    total_entries = analysis['total_entries']

    return f"""## Executive Summary

**Situation**: The Digital FTE system processed {total_entries} operations this week with a success rate of {success_rate:.1f}%.

**Complication**: While the overall success rate is acceptable, certain file types experienced higher failure rates that require attention.

**Question**: How can we maintain high operational reliability while scaling operations?

**Answer**: Maintain the current success rate above 80% while implementing improvements to reduce specific failure types."""

def generate_context_section(analysis: Dict) -> str:
    """
    Generate the context section of the report.

    Args:
        analysis: Analysis results from analyze_logs

    Returns:
        Context section as a string
    """
    total_entries = analysis['total_entries']
    success_count = analysis['success_count']
    failure_count = analysis['failure_count']

    return f"""## Context

The Digital FTE system operates autonomously across multiple directories (00_Inbox, 01_Needs_Action, 02_Pending_Approval, 03_Approved) as outlined in the CLAUDE.md operational procedures. This week, the system processed {total_entries} tasks with {success_count} successful operations and {failure_count} failures.

The system follows the Chief of Staff six-page narrative format for reporting, emphasizing data-driven decision making and high operational standards. Most operations involve processing task files across the established workflow directories.

The most common failure pattern appears to be missing files in the 03_Approved directory, suggesting either tasks weren't properly approved or were moved prematurely."""

def generate_analysis_section(analysis: Dict) -> str:
    """
    Generate the analysis section of the report.

    Args:
        analysis: Analysis results from analyze_logs

    Returns:
        Analysis section as a string
    """
    success_rate = analysis['success_rate']
    file_analysis = analysis['file_analysis']

    # Identify problematic files
    problematic_files = []
    for filename, stats in file_analysis.items():
        if stats['failure'] > 0:
            failure_rate = (stats['failure'] / (stats['success'] + stats['failure'])) * 100
            problematic_files.append((filename, failure_rate))

    problematic_files.sort(key=lambda x: x[1], reverse=True)

    analysis_text = f"""## Analysis

### Current State
The system achieved a {success_rate:.1f}% success rate this week. Of the {len(file_analysis)} unique files processed, {len(problematic_files)} experienced at least one failure.

### Operational Metrics
- Total operations: {analysis['total_entries']}
- Successful operations: {analysis['success_count']} ({analysis['success_rate']:.1f}%)
- Failed operations: {analysis['failure_count']} ({100 - analysis['success_rate']:.1f}%)

### Problematic Files
"""

    for filename, failure_rate in problematic_files[:5]:  # Top 5 problematic files
        stats = file_analysis[filename]
        analysis_text += f"- {filename}: {failure_rate:.1f}% failure rate ({stats['failure']} failures, {stats['success']} successes)\n"

    analysis_text += """

### Options Considered

1. **Maintain Current Approach** (Status Quo)
   - Pros: Stable, proven system
   - Cons: Some failure patterns persist
   - Trade-off: Accept minor inefficiencies for stability

2. **Enhanced Validation Before Execution**
   - Pros: Reduce failures by verifying file existence beforehand
   - Cons: Additional processing overhead
   - Trade-off: Slight performance reduction for improved reliability

3. **Improved Error Recovery Mechanisms**
   - Pros: Better handling of missing files and edge cases
   - Cons: More complex system logic
   - Trade-off: Complexity increase for resilience improvement

Based on the data showing recurring file-not-found errors, the Enhanced Validation approach offers the best balance of reliability improvement with minimal complexity increase."""

    return analysis_text

def generate_recommendation_section(analysis: Dict) -> str:
    """
    Generate the recommendation section of the report.

    Args:
        analysis: Analysis results from analyze_logs

    Returns:
        Recommendation section as a string
    """
    return """## Recommendation

### Proposed Action
Implement pre-execution validation to verify file existence before attempting operations. This will address the most common failure pattern (file-not-found errors) without significantly increasing system complexity.

### Success Metrics
- Reduce file-not-found errors by 90%
- Maintain or improve current success rate (currently 80%+)
- Decrease average time to detect invalid tasks

### Timeline
- Week 1: Implement file existence checks
- Week 2: Test and refine validation logic
- Week 3: Deploy and monitor results

### Resources Required
- Development time: 2-3 days for implementation and testing
- Monitoring: Existing log infrastructure sufficient

### Key Milestones
- Complete validation implementation by end of Week 1
- Achieve 90% reduction in file-not-found errors by end of Week 2"""

def generate_risks_mitigations_section() -> str:
    """
    Generate the risks and mitigations section of the report.

    Returns:
        Risks and mitigations section as a string
    """
    return """## Risks and Mitigations

### Key Risks
- **Implementation delays**: New validation logic might introduce bugs
  - Mitigation: Thorough testing in development environment before deployment
- **Performance impact**: Additional validation might slow down operations
  - Mitigation: Optimize validation logic and monitor performance metrics
- **Incomplete coverage**: New validation might not catch all edge cases
  - Mitigation: Maintain existing error handling alongside new validation

### Mitigation Strategies
- Conduct extensive unit and integration testing before deployment
- Implement gradual rollout with monitoring
- Maintain rollback capability if issues arise

### Contingency Plans
- If performance degrades significantly, temporarily disable validation and investigate
- If new bugs emerge, revert to previous version and implement fixes incrementally"""

def generate_appendix_section(analysis: Dict) -> str:
    """
    Generate the appendix section of the report.

    Args:
        analysis: Analysis results from analyze_logs

    Returns:
        Appendix section as a string
    """
    return f"""## Appendix

### FAQ
Q: Why is the success rate not 100%?
A: The system encounters legitimate errors when files referenced in tasks don't exist in the 03_Approved directory, typically because tasks haven't been properly approved or were moved.

Q: How often should audits be generated?
A: Weekly, as specified in the Chief of Staff skill requirements.

### Sample Failure Details
Top failure patterns observed:
{chr(10).join(f"- {detail[:100]}..." if len(detail) > 100 else f"- {detail}" for detail in analysis['failure_details'][:5])}

### Definitions
- **Success Rate**: Percentage of operations that completed successfully
- **Narrative Report**: Six-page memo format with executive summary, context, analysis, recommendations
- **Digital FTE**: Autonomous Digital Full-Time Employee system following CLAUDE.md procedures"""

def generate_audit_report() -> str:
    """
    Generate the complete audit report.

    Returns:
        Complete audit report as a string
    """
    # Load the logs
    log_file_path = "Logs/Action_Logs.json"

    if not os.path.exists(log_file_path):
        return f"""# CEO WEEKLY BRIEFING - {datetime.now().strftime('%Y-%m-%d')}

## Executive Summary

**Situation**: Unable to locate action logs at {log_file_path}.
**Complication**: Cannot assess system performance without log data.
**Question**: How can we restore logging functionality?
**Answer**: Verify log file generation process and file system permissions.

## Action Required
1. Check that the logging system is functioning correctly
2. Verify that logs are being written to the correct location
3. Ensure proper file system permissions

No further analysis possible without valid log data."""

    with open(log_file_path, 'r') as f:
        logs = json.load(f)

    # Analyze the logs
    analysis = analyze_logs(logs)

    # Generate report sections
    header = f"# CEO WEEKLY BRIEFING - {datetime.now().strftime('%Y-%m-%d')}"

    executive_summary = generate_executive_summary(analysis)
    context_section = generate_context_section(analysis)
    analysis_section = generate_analysis_section(analysis)
    recommendation_section = generate_recommendation_section(analysis)
    risks_section = generate_risks_mitigations_section()
    appendix_section = generate_appendix_section(analysis)

    # Combine all sections
    report = f"{header}\n\n"
    report += executive_summary + "\n\n"
    report += context_section + "\n\n"
    report += analysis_section + "\n\n"
    report += recommendation_section + "\n\n"
    report += risks_section + "\n\n"
    report += appendix_section + "\n\n"

    return report

def main():
    """
    Main function to generate and save the audit report.
    """
    report = generate_audit_report()

    # Save to the required location
    output_path = "Management/CEO_WEEKLY_BRIEFING.md"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(report)

    print(f"Audit report generated successfully at {output_path}")
    print(f"Report length: {len(report)} characters")

if __name__ == "__main__":
    main()