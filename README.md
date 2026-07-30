# 6M-0002 SaaS Support Workflow

A production-oriented Python repository demonstrating repository initialization, commit hygiene, JSON and CSV input processing, structured logging, automated testing and safe output handling for a subscription SaaS platform.

The workflow is designed to help a SaaS engineering team process subscription records and customer-support tickets without corrupting existing valid output when malformed or invalid input is received.

## Business Scenario

A subscription SaaS platform wants to reduce customer churn and improve issue-resolution speed.

The repository processes two categories of input:

- Subscription records stored as JSON
- Customer-support ticket records stored as CSV

The implementation validates records, detects malformed or unsafe content, writes structured logs and protects previously generated output from failed processing.

## Key Features

- JSON and CSV input loading
- Cross-platform path handling with `pathlib`
- Missing-file and invalid-path handling
- Subscription record validation
- Customer-support ticket validation
- Duplicate identifier detection
- Spreadsheet formula-injection detection
- Safe temporary-file output
- Atomic output replacement
- Existing-output preservation on failure
- Structured JSONL application logging
- Command-line interface
- Automated unit tests
- Exactly 30 starter fixtures
- One-command project verification
- Clean and reviewable Git history

## Requirements

- Git
- Python 3.10 or newer
- PowerShell, Command Prompt, Bash or another terminal

The project currently uses only the Python standard library. No third-party runtime packages are required.

## Repository URL

```text
https://github.com/jagroopbedidev/6M-0002-saas-support-workflow
