# Engineering Trade-offs

This document explains the main technical decisions used in the 6M-0002 SaaS Support Workflow, including their benefits, limitations and reasons.

## 1. Python Standard Library Instead of Third-Party Packages

### Decision

The project uses only Python standard-library modules such as:

- pathlib
- json
- csv
- logging
- tempfile
- os
- argparse
- unittest

### Benefit

- A clean clone does not require package installation.
- Setup is faster and more reliable.
- Dependency conflicts and supply-chain risk are reduced.
- The project can run in restricted environments.

### Cost

- Validation and structured logging require more custom code.
- Third-party tools could provide richer schemas and shorter implementations.

### Reason

The repository is small and the required workflow can be implemented safely without external runtime dependencies. Reproducibility was prioritized over convenience.

## 2. Separate Loader, Validator, Pipeline and CLI Modules

### Decision

Input loading, business validation, output writing, logging and terminal interaction are separated into focused modules.

### Benefit

- Each component has one clear responsibility.
- Unit tests can target individual layers.
- Input parsing can change without rewriting the CLI.
- Business rules can change without modifying file-loading code.
- Failures are easier to locate.

### Cost

- The repository contains more files.
- A beginner must understand how multiple modules connect.

### Reason

Production code is easier to test and maintain when parsing, validation, persistence and presentation are not mixed in one large script.

## 3. Strict Validation Instead of Permissive Processing

### Decision

Records with missing fields, invalid values, duplicate identifiers or unsafe formula-like content are rejected.

### Benefit

- Corrupt or misleading records do not enter downstream output.
- Validation errors clearly identify the affected record and field.
- Data quality is consistent.

### Cost

- A partly usable file is rejected instead of being partially processed.
- New plans, statuses or categories require validation-rule updates.

### Reason

For subscription and customer-support data, silently accepting invalid records creates more risk than rejecting them with an actionable explanation.

## 4. Validate the Complete Input Before Writing Output

### Decision

The application loads and validates all records before creating the final output.

### Benefit

- A later invalid record cannot leave partially written final output.
- Duplicate identifiers can be detected across the complete input.
- The output represents one fully validated processing result.

### Cost

- The complete input is held in memory.
- This approach is not ideal for extremely large files.

### Reason

The supplied fixture dataset and expected SaaS workflow are small enough for in-memory processing. Data integrity was prioritized over streaming scalability.

## 5. Temporary File and Atomic Replacement

### Decision

Validated data is written to a temporary file in the destination directory. The final file is replaced only after writing, flushing and synchronization succeed.

### Benefit

- Existing valid output survives malformed input.
- Partial output is not exposed as the final result.
- A failed write does not destroy the previous output.
- Temporary files can be removed after failure.

### Cost

- Temporary disk space is required.
- Atomic replacement depends on input and temporary output being on compatible filesystems.
- The implementation is more complex than direct writing.

### Reason

The production constraint explicitly requires malformed input to be handled without data corruption.

## 6. Preserve Original Input Instead of Normalizing In Place

### Decision

The application reads input files without overwriting or editing them.

### Benefit

- Original evidence remains available for investigation.
- A user can correct and retry an invalid file.
- Processing is repeatable.
- Input hashes remain unchanged.

### Cost

- Corrected or normalized data must be written to another output path.
- Additional files may be created.

### Reason

In-place mutation creates unnecessary data-loss risk and makes failures harder to audit.

## 7. JSONL Structured Logs Instead of Plain Text Logs

### Decision

Each log line is stored as an independent JSON object.

### Benefit

- Logs can be parsed by scripts and monitoring systems.
- Events can be filtered by status, file type or error type.
- Success and failure records use a consistent schema.
- Logs remain readable in a text editor.

### Cost

- JSONL is less visually friendly than carefully formatted prose logs.
- Developers must avoid logging non-serializable values.

### Reason

The workflow requires structured logs, and JSONL provides a simple standard-library solution.

## 8. Operational Metadata Instead of Complete Record Logging

### Decision

Logs contain event names, status, paths, file type, record count and error type, but not complete customer records.

### Benefit

- Sensitive customer and subscription information is not duplicated in logs.
- Log files remain smaller.
- Security and privacy exposure are reduced.

### Cost

- Logs alone cannot reconstruct the complete failed record.
- Developers may need the original fixture to investigate details.

### Reason

Operational observability should not require copying business data or potential secrets into runtime logs.

## 9. Formula-Injection Rejection

### Decision

CSV string values beginning with =, +, - or @ are rejected.

### Benefit

- Spreadsheet applications are less likely to execute attacker-controlled formulas.
- Exported CSV data is safer to inspect.

### Cost

- Some legitimate text values beginning with these characters may be rejected.
- A future system may require escaping or allowlisting instead of rejection.

### Reason

For the current workflow, rejecting suspicious spreadsheet content is safer than silently accepting it.

## 10. Committed Fixtures and a Fixture Generator

### Decision

The repository contains all 30 fixture files and also contains a script that recreates them.

### Benefit

- Tests work immediately after cloning.
- Reviewers can inspect fixture content directly.
- The generator documents how the dataset was produced.
- Fixtures can be regenerated consistently.

### Cost

- Fixture data occupies repository space.
- The generator and committed fixtures must remain synchronized.

### Reason

Immediate clean-clone execution and transparent review were more important than minimizing repository size.

## 11. Unittest Instead of a Third-Party Test Framework

### Decision

The project uses Python's built-in unittest framework.

### Benefit

- No package installation is required.
- Tests run on a clean clone.
- Test discovery is available through one standard command.

### Cost

- Some test syntax is more verbose than third-party alternatives.
- Parameterized and fixture-heavy testing requires more manual code.

### Reason

The standard library is sufficient for this repository's unit, integration and data-integrity tests.

## 12. CLI Exit Codes

### Decision

The command-line interface returns:

- 0 for success
- 1 for expected processing failure
- 2 for invalid arguments, configuration issues or unexpected failure

### Benefit

- Shell scripts and CI systems can determine success automatically.
- Expected bad input is separated from application configuration problems.
- Human-readable errors do not require parsing a traceback.

### Cost

- Callers must understand the exit-code contract.
- Multiple error classes are grouped under the same expected-failure code.

### Reason

A command-line program should communicate outcomes to both humans and automation.

## 13. One Verification Script Instead of Manual Acceptance Steps

### Decision

The repository provides scripts/run_all.py as the documented acceptance command.

### Benefit

- Reviewers run one consistent workflow.
- Manual steps are less likely to be missed.
- Tests, safe processing and structured logging are checked together.
- A clean clone can be assessed quickly.

### Cost

- The script duplicates a small amount of test orchestration.
- The verification workflow must be maintained when repository requirements change.

### Reason

One-command reproducibility is a mandatory production constraint and a strong repository-quality signal.

## 14. Small Logical Commits Instead of One Final Commit

### Decision

Baseline, safety configuration, loading, validation, fixture repair, data integrity, logging, CLI, automation and documentation are committed separately.

### Benefit

- Reviewers can understand changes incrementally.
- Regressions can be traced to a focused commit.
- A single feature or fix can be reverted safely.
- Commit messages explain repository evolution.

### Cost

- Development requires more staging and review effort.
- Incorrect commit boundaries may require cleanup before pushing.

### Reason

The problem specifically evaluates repository initialization and commit hygiene. A single massive final commit would hide the engineering process.

## 15. Git Revert Instead of Rewriting Shared History

### Decision

A pushed commit should be undone with git revert rather than reset plus force push.

### Benefit

- Shared history remains intact.
- Collaborators do not lose commits.
- The reversal is visible and auditable.

### Cost

- Revert creates an additional commit.
- A later reapplication may require reverting the revert or creating a new fix.

### Reason

Visible corrective history is safer for collaborative repositories.

## Future Scaling Considerations

For a larger production deployment, the following changes may be appropriate:

- Streaming processing for very large CSV files
- Schema validation with a dedicated validation library
- Centralized log aggregation
- Rotating log handlers
- Database-backed processing state
- Retry and dead-letter workflows
- CI workflows for multiple Python versions
- More granular security allowlists for formula-like values
- Transactional storage beyond filesystem atomic replacement

These are intentionally outside the current scope because the repository focuses on clean initialization, safe local processing and commit hygiene.
