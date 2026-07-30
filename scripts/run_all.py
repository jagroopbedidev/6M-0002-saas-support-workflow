from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures"

VALID_JSON_FILE = (
    FIXTURE_ROOT
    / "json"
    / "valid"
    / "subscription_01.json"
)

INVALID_JSON_FILE = (
    FIXTURE_ROOT
    / "json"
    / "malformed"
    / "malformed_json_02_missing_subscription_id.json"
)

VALID_CSV_FILE = (
    FIXTURE_ROOT
    / "csv"
    / "valid"
    / "support_tickets_01.csv"
)

FORMULA_INJECTION_CSV_FILE = (
    FIXTURE_ROOT
    / "csv"
    / "malformed"
    / "malformed_csv_04_formula_injection.csv"
)

MINIMUM_PYTHON_VERSION = (3, 10)


class VerificationError(Exception):
    """Raised when one-command verification does not pass."""


def print_heading(title: str) -> None:
    """Print a readable verification section heading."""

    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_pass(message: str) -> None:
    """Print one successful verification result."""

    print(f"[PASS] {message}")


def require(condition: bool, message: str) -> None:
    """Raise a verification error when a condition is false."""

    if not condition:
        raise VerificationError(message)


def run_command(
    command: list[str],
    *,
    expected_exit_code: int = 0,
) -> subprocess.CompletedProcess[str]:
    """
    Run one command from the project root.

    Standard output and standard error are captured and displayed.
    """

    print()
    print("$ " + " ".join(command))

    completed_process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed_process.stdout.strip():
        print(completed_process.stdout.rstrip())

    if completed_process.stderr.strip():
        print(completed_process.stderr.rstrip())

    require(
        completed_process.returncode == expected_exit_code,
        (
            "Command returned an unexpected exit code. "
            f"Expected {expected_exit_code}, "
            f"received {completed_process.returncode}."
        ),
    )

    return completed_process


def verify_python_version() -> None:
    """Verify that the active Python version is supported."""

    print_heading("1. Python Environment")

    current_version = sys.version_info[:3]

    print(
        "Python version: "
        + ".".join(str(part) for part in current_version)
    )

    require(
        current_version >= MINIMUM_PYTHON_VERSION,
        (
            "Python 3.10 or newer is required. "
            f"Current version: {current_version}"
        ),
    )

    print_pass("Supported Python version is active.")


def verify_repository_files() -> None:
    """Verify the expected repository assets."""

    print_heading("2. Repository Assets")

    required_files = [
        PROJECT_ROOT / ".gitignore",
        PROJECT_ROOT / ".gitattributes",
        PROJECT_ROOT / ".editorconfig",
        PROJECT_ROOT / ".env.example",
        PROJECT_ROOT / "requirements.txt",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        PROJECT_ROOT / "src" / "saas_support" / "loaders.py",
        PROJECT_ROOT / "src" / "saas_support" / "validators.py",
        PROJECT_ROOT / "src" / "saas_support" / "pipeline.py",
        PROJECT_ROOT
        / "src"
        / "saas_support"
        / "logging_config.py",
        PROJECT_ROOT / "src" / "saas_support" / "cli.py",
        PROJECT_ROOT / "src" / "saas_support" / "__main__.py",
    ]

    missing_files = [
        str(path.relative_to(PROJECT_ROOT))
        for path in required_files
        if not path.is_file()
    ]

    require(
        not missing_files,
        "Required repository files are missing: "
        + ", ".join(missing_files),
    )

    fixture_files = [
        path
        for path in FIXTURE_ROOT.rglob("*")
        if path.is_file()
    ]

    print(f"Fixture count: {len(fixture_files)}")

    require(
        len(fixture_files) == 30,
        (
            "Expected exactly 30 fixture files, "
            f"but found {len(fixture_files)}."
        ),
    )

    print_pass("Repository configuration and source files exist.")
    print_pass("Exactly 30 starter fixtures are present.")


def run_automated_tests() -> None:
    """Run the complete unittest suite."""

    print_heading("3. Automated Test Suite")

    run_command(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ]
    )

    print_pass("Complete automated test suite passed.")


def read_json_lines(path: Path) -> list[dict[str, Any]]:
    """Read and parse a JSONL file."""

    require(
        path.is_file(),
        f"Expected structured log was not created: {path}",
    )

    records: list[dict[str, Any]] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            parsed_record = json.loads(line)
        except json.JSONDecodeError as error:
            raise VerificationError(
                "Structured log contains invalid JSON "
                f"at line {line_number}: {error}"
            ) from error

        require(
            isinstance(parsed_record, dict),
            (
                "Structured log line "
                f"{line_number} is not a JSON object."
            ),
        )

        records.append(parsed_record)

    return records


def verify_valid_json(
    temporary_directory: Path,
    log_path: Path,
) -> None:
    """Process and verify one valid JSON fixture."""

    print_heading("4. Valid JSON Processing")

    output_path = temporary_directory / "valid-result.json"

    completed_process = run_command(
        [
            sys.executable,
            "-m",
            "src.saas_support",
            "--input",
            str(VALID_JSON_FILE),
            "--output",
            str(output_path),
            "--log-file",
            str(log_path),
        ]
    )

    require(
        output_path.is_file(),
        "Valid JSON processing did not create an output file.",
    )

    try:
        output_data = json.loads(
            output_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise VerificationError(
            f"Generated JSON output is invalid: {error}"
        ) from error

    require(
        output_data.get("subscription_id") == "SUB-0001",
        "Generated JSON contains an unexpected subscription_id.",
    )

    require(
        "Records processed: 1" in completed_process.stdout,
        "CLI did not report the expected JSON record count.",
    )

    print_pass("Valid JSON input was processed successfully.")
    print_pass("Generated JSON output contains SUB-0001.")


def verify_valid_csv(
    temporary_directory: Path,
    log_path: Path,
) -> None:
    """Process and verify one valid CSV fixture."""

    print_heading("5. Valid CSV Processing")

    output_path = temporary_directory / "valid-result.csv"

    completed_process = run_command(
        [
            sys.executable,
            "-m",
            "src.saas_support",
            "--input",
            str(VALID_CSV_FILE),
            "--output",
            str(output_path),
            "--log-file",
            str(log_path),
        ]
    )

    require(
        output_path.is_file(),
        "Valid CSV processing did not create an output file.",
    )

    with output_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    require(
        len(rows) == 3,
        f"Expected 3 generated CSV rows, but found {len(rows)}.",
    )

    require(
        rows[0].get("ticket_id") == "TKT-0001",
        "Generated CSV contains an unexpected first ticket ID.",
    )

    require(
        "Records processed: 3" in completed_process.stdout,
        "CLI did not report the expected CSV record count.",
    )

    print_pass("Valid CSV input was processed successfully.")
    print_pass("Generated CSV contains 3 customer-support rows.")


def verify_invalid_json_preserves_output(
    temporary_directory: Path,
    log_path: Path,
) -> None:
    """Verify malformed business data cannot damage valid output."""

    print_heading("6. Invalid JSON Data-Integrity Protection")

    output_path = temporary_directory / "protected-result.json"
    original_content = b'{"status": "stable-existing-output"}\n'

    output_path.write_bytes(original_content)

    completed_process = run_command(
        [
            sys.executable,
            "-m",
            "src.saas_support",
            "--input",
            str(INVALID_JSON_FILE),
            "--output",
            str(output_path),
            "--log-file",
            str(log_path),
        ],
        expected_exit_code=1,
    )

    require(
        output_path.read_bytes() == original_content,
        (
            "Existing JSON output changed after invalid "
            "input processing."
        ),
    )

    require(
        "DataValidationError" in completed_process.stderr,
        "CLI did not report DataValidationError.",
    )

    require(
        "Existing output was not modified."
        in completed_process.stderr,
        "CLI did not confirm output protection.",
    )

    print_pass("Invalid JSON record was rejected.")
    print_pass("Existing JSON output remained byte-for-byte unchanged.")


def verify_formula_injection_preserves_output(
    temporary_directory: Path,
    log_path: Path,
) -> None:
    """Verify formula-injection CSV data is rejected safely."""

    print_heading("7. CSV Formula-Injection Protection")

    output_path = temporary_directory / "protected-result.csv"

    original_content = (
        b"status,message\n"
        b"stable,existing output\n"
    )

    output_path.write_bytes(original_content)

    completed_process = run_command(
        [
            sys.executable,
            "-m",
            "src.saas_support",
            "--input",
            str(FORMULA_INJECTION_CSV_FILE),
            "--output",
            str(output_path),
            "--log-file",
            str(log_path),
        ],
        expected_exit_code=1,
    )

    require(
        output_path.read_bytes() == original_content,
        (
            "Existing CSV output changed after formula-injection "
            "input processing."
        ),
    )

    require(
        "potential spreadsheet formula"
        in completed_process.stderr,
        "Formula-injection validation message was not reported.",
    )

    print_pass("CSV formula-injection content was rejected.")
    print_pass("Existing CSV output remained unchanged.")


def verify_structured_logs(log_path: Path) -> None:
    """Verify structured success and failure log events."""

    print_heading("8. Structured Logging Verification")

    records = read_json_lines(log_path)

    events = {
        record.get("event")
        for record in records
    }

    required_events = {
        "logging_configured",
        "processing_started",
        "processing_completed",
        "processing_failed",
    }

    missing_events = sorted(required_events - events)

    require(
        not missing_events,
        "Structured log is missing events: "
        + ", ".join(missing_events),
    )

    for index, record in enumerate(records, start=1):
        require(
            "timestamp" in record,
            f"Log record {index} has no timestamp.",
        )

        require(
            "level" in record,
            f"Log record {index} has no logging level.",
        )

        require(
            "message" in record,
            f"Log record {index} has no message.",
        )

    print(f"Structured log records: {len(records)}")
    print_pass("Every log line is valid JSON.")
    print_pass("Success and failure events are both present.")


def verify_no_temporary_files(
    temporary_directory: Path,
) -> None:
    """Verify failed processing did not leave temporary files."""

    print_heading("9. Temporary-File Cleanup")

    temporary_files = list(
        temporary_directory.rglob("*.tmp")
    )

    require(
        not temporary_files,
        "Temporary files were not cleaned: "
        + ", ".join(str(path) for path in temporary_files),
    )

    print_pass("No temporary processing files remain.")


def main() -> int:
    """Run the complete one-command project verification."""

    start_time = time.perf_counter()

    print("6M-0002 SaaS Support Workflow")
    print("One-command verification started.")
    print(f"Project root: {PROJECT_ROOT}")

    try:
        verify_python_version()
        verify_repository_files()
        run_automated_tests()

        with tempfile.TemporaryDirectory(
            prefix="saas-support-verification-"
        ) as temporary_directory_name:
            temporary_directory = Path(
                temporary_directory_name
            )

            log_path = (
                temporary_directory
                / "logs"
                / "verification.jsonl"
            )

            verify_valid_json(
                temporary_directory,
                log_path,
            )

            verify_valid_csv(
                temporary_directory,
                log_path,
            )

            verify_invalid_json_preserves_output(
                temporary_directory,
                log_path,
            )

            verify_formula_injection_preserves_output(
                temporary_directory,
                log_path,
            )

            verify_structured_logs(log_path)

            verify_no_temporary_files(
                temporary_directory
            )

    except VerificationError as error:
        print_heading("VERIFICATION FAILED")
        print(f"[FAIL] {error}")
        return 1

    except Exception as error:
        print_heading("UNEXPECTED VERIFICATION FAILURE")
        print(f"[FAIL] {type(error).__name__}: {error}")
        return 2

    elapsed_seconds = time.perf_counter() - start_time

    print_heading("VERIFICATION COMPLETED")
    print("[PASS] All automated tests passed.")
    print("[PASS] Valid JSON processing passed.")
    print("[PASS] Valid CSV processing passed.")
    print("[PASS] Malformed input was rejected safely.")
    print("[PASS] Existing valid output was preserved.")
    print("[PASS] Structured logs were verified.")
    print("[PASS] Temporary files were cleaned.")
    print(f"Completed in {elapsed_seconds:.2f} seconds.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
