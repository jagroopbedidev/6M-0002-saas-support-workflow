# Project Metrics

This document records measurable evidence for the 6M-0002 SaaS Support Workflow implementation.

## Measurement Snapshot

| Metric | Value |
|---|---:|
| Captured at | 2026-07-31 01:41:36 +05:30 |
| Python runtime | Python 3.14.5 |
| Implementation HEAD before this documentation commit | 990c180 |
| Total commits at capture time | 10 |
| Feature-branch commits since main | 9 |
| Files changed from main | 22 |
| Python source modules | 7 |
| Automated test modules | 6 |
| Approximate source lines | 1121 |
| Approximate test lines | 1064 |
| External runtime dependencies | 0 |

The implementation HEAD and commit counts above were captured before the metrics documentation commit itself was created.

## Fixture Coverage

| Fixture category | Count |
|---|---:|
| Valid subscription JSON | 10 |
| Malformed subscription JSON | 5 |
| Valid support-ticket CSV | 10 |
| Malformed support-ticket CSV | 5 |
| Total fixtures | 30 |

The repository acceptance target is exactly 30 fixture files.

## Automated Test Results

| Test metric | Result |
|---|---:|
| Automated tests discovered | 57 |
| Test process exit code | 0 |
| Skipped tests |  |
| Failures | 0 |
| Errors | 0 |
| Pass rate | 100% |

Test command:

~~~powershell
python -m unittest discover -s tests -v
~~~

## One-Command Verification

| Verification metric | Result |
|---|---:|
| Verification command exit code | 0 |
| Measured duration | 1.17 seconds |
| Final status | PASS |

Verification command:

~~~powershell
python scripts/run_all.py
~~~

The one-command workflow verifies:

- Supported Python runtime
- Required repository files
- Exactly 30 fixtures
- Complete automated test suite
- Valid JSON processing
- Valid CSV processing
- Invalid subscription-record rejection
- CSV formula-injection rejection
- Existing-output preservation
- Structured JSONL logging
- Temporary-file cleanup

## Input and Failure Coverage

The implementation handles the following expected cases:

- Missing input file
- Directory supplied instead of a file
- Unsupported file extension
- Invalid JSON syntax
- Missing required JSON fields
- Invalid JSON field types
- Invalid subscription plan or status
- Duplicate subscription identifiers
- Negative revenue values
- Invalid churn-risk range
- Missing CSV headers or columns
- Duplicate support-ticket identifiers
- Invalid priority, category or status
- Invalid resolution-hour values
- Spreadsheet formula-injection content
- Input and output path collision
- Mismatched input and output extensions
- Simulated output-write failure

## Data-Integrity Evidence

Automated tests verify that existing valid output remains byte-for-byte unchanged when:

- JSON parsing fails
- JSON business validation fails
- CSV validation fails
- Formula-injection content is detected
- A simulated disk-write failure occurs

The pipeline writes to a temporary file and uses atomic replacement only after the complete output has been written and flushed.

## Repository-Hygiene Evidence

The repository demonstrates:

- A documented baseline commit
- Repository safety configuration
- Small logical feature and fix commits
- Focused staging before commits
- Runtime logs excluded from Git
- Generated output excluded from Git
- Environment secrets excluded from Git
- Cross-platform paths implemented with pathlib
- Safe shared-history rollback documented with git revert

## Acceptance Result

At the time of measurement:

- Automated tests passed
- One-command verification passed
- No tests were skipped
- Exactly 30 fixtures were present
- No third-party runtime dependency was required
- Existing-output protection was verified
- Structured success and failure logs were verified
