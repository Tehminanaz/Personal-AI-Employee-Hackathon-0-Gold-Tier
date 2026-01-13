# Tests Directory

This directory contains test scripts for validating tasks processed by the Digital FTE system.

## Purpose

Every task processed from `00_Inbox/` must have a corresponding test script generated in this directory. Tests must **PASS** before the task can move to `02_Pending_Approval/`.

## Mandatory Testing Rule

From CLAUDE.md:
> **CRITICAL RULE:** For every task processed from `00_Inbox/`, you must generate a corresponding Python test script in `Tests/` directory. The task is only considered 'Drafted' if test cases PASS.

## Test Naming Convention

```
test_[task_category]_[brief_description]_[YYYYMMDD_HHMMSS].py
```

Examples:
- `test_financial_invoice_processing_20260109_032100.py`
- `test_social_linkedin_post_20260109_032200.py`
- `test_executive_weekly_report_20260109_032300.py`

## Test Structure

Each test file should include:

1. **Docstring**: Explaining what is being tested
2. **Test Classes**: Organized by test category
3. **Test Functions**: Individual test cases with clear assertions
4. **Utility Functions**: Helper functions for testing

See `test_template_example.py` for a complete example.

## Running Tests

### Run All Tests
```bash
pytest Tests/
```

### Run Specific Test File
```bash
pytest Tests/test_financial_invoice_processing_20260109_032100.py
```

### Run with Verbose Output
```bash
pytest Tests/ -v
```

### Run with Coverage
```bash
pytest Tests/ --cov=. --cov-report=html
```

## Test Coverage Requirements

Each test should cover:
- ✅ Input validation
- ✅ Expected output verification
- ✅ Edge case handling
- ✅ Error condition testing

## Test Results

Test results are logged to:
- Console output (real-time)
- `Logs/test_results.log` (persistent)

## Pass Criteria

All tests must:
- Execute without errors
- Return exit code 0
- Have all assertions pass

Only then can the task move to `02_Pending_Approval/`.

## Example Test Categories

### Financial Tasks
- Invoice validation
- Reconciliation accuracy
- Payment processing
- Account categorization

### Communication Tasks
- Content format validation
- Platform-specific requirements
- Character limits
- Link validation

### Executive Tasks
- Report completeness
- Data accuracy
- Format compliance
- Metric validation

### Technical Tasks
- Code syntax validation
- Deployment readiness
- Configuration correctness
- Security checks

### Safety Tasks
- Content moderation
- Privacy compliance
- Ethical guidelines
- Risk assessment

---

**Note:** This directory is critical to the Digital FTE quality assurance process. Never skip test generation!
