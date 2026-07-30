# 6M-0002 SaaS Support Workflow

Starter repository for Problem 6M-0002: Repository Initialization and Commit Hygiene.

## Business Scenario

This project represents a subscription SaaS platform that wants to reduce
customer churn and improve customer-support issue resolution.

## Starter Repository Contents

The starter repository currently contains:

- 30 JSON and CSV fixture files
- Valid subscription JSON examples
- Malformed subscription JSON examples
- Valid customer-support CSV examples
- Malformed customer-support CSV examples
- Intentionally incomplete automated tests
- Cross-platform project paths using `pathlib`

## Current Status

Starter baseline only. The production input-processing workflow, validation,
structured logging, safe output operations and complete automated tests have
not yet been implemented.

## Run Starter Tests

From the repository root:

```bash
python -m unittest discover -s tests -v