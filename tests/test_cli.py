from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from src.saas_support.cli import (
    EXIT_PROCESSING_ERROR,
    EXIT_SUCCESS,
    main,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID_JSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "valid"
    / "subscription_01.json"
)

INVALID_JSON_RECORD_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "malformed"
    / "malformed_json_02_missing_subscription_id.json"
)

VALID_CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "csv"
    / "valid"
    / "support_tickets_01.csv"
)


class CommandLineInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.addCleanup(
            self.temporary_directory.cleanup
        )

        self.directory = Path(
            self.temporary_directory.name
        )

        self.log_path = (
            self.directory / "logs" / "application.jsonl"
        )

    def run_cli(
        self,
        arguments: list[str],
    ) -> tuple[int, str, str]:
        standard_output = StringIO()
        standard_error = StringIO()

        with redirect_stdout(standard_output):
            with redirect_stderr(standard_error):
                exit_code = main(arguments)

        return (
            exit_code,
            standard_output.getvalue(),
            standard_error.getvalue(),
        )

    def test_valid_json_returns_success_exit_code(
        self,
    ) -> None:
        output_path = self.directory / "result.json"

        exit_code, output, error = self.run_cli(
            [
                "--input",
                str(VALID_JSON_FILE),
                "--output",
                str(output_path),
                "--log-file",
                str(self.log_path),
            ]
        )

        self.assertEqual(
            exit_code,
            EXIT_SUCCESS,
        )
        self.assertTrue(output_path.is_file())
        self.assertIn(
            "Processing completed successfully.",
            output,
        )
        self.assertIn(
            "Records processed: 1",
            output,
        )
        self.assertEqual(error, "")

    def test_valid_csv_returns_success_exit_code(
        self,
    ) -> None:
        output_path = self.directory / "result.csv"

        exit_code, output, error = self.run_cli(
            [
                "--input",
                str(VALID_CSV_FILE),
                "--output",
                str(output_path),
                "--log-file",
                str(self.log_path),
            ]
        )

        self.assertEqual(
            exit_code,
            EXIT_SUCCESS,
        )
        self.assertTrue(output_path.is_file())
        self.assertIn(
            "Records processed: 3",
            output,
        )
        self.assertEqual(error, "")

    def test_invalid_record_returns_failure_and_preserves_output(
        self,
    ) -> None:
        output_path = self.directory / "result.json"
        original_content = b'{"status": "stable"}\n'
        output_path.write_bytes(original_content)

        exit_code, output, error = self.run_cli(
            [
                "--input",
                str(INVALID_JSON_RECORD_FILE),
                "--output",
                str(output_path),
                "--log-file",
                str(self.log_path),
            ]
        )

        self.assertEqual(
            exit_code,
            EXIT_PROCESSING_ERROR,
        )
        self.assertEqual(output, "")
        self.assertIn(
            "Processing failed.",
            error,
        )
        self.assertIn(
            "DataValidationError",
            error,
        )
        self.assertIn(
            "Existing output was not modified.",
            error,
        )
        self.assertEqual(
            output_path.read_bytes(),
            original_content,
        )

    def test_missing_input_returns_failure_exit_code(
        self,
    ) -> None:
        missing_input = self.directory / "missing.json"
        output_path = self.directory / "result.json"

        exit_code, output, error = self.run_cli(
            [
                "--input",
                str(missing_input),
                "--output",
                str(output_path),
                "--log-file",
                str(self.log_path),
            ]
        )

        self.assertEqual(
            exit_code,
            EXIT_PROCESSING_ERROR,
        )
        self.assertEqual(output, "")
        self.assertIn(
            "InputFileNotFoundError",
            error,
        )
        self.assertFalse(output_path.exists())

    def test_wrong_output_extension_is_rejected(
        self,
    ) -> None:
        output_path = self.directory / "result.csv"

        exit_code, output, error = self.run_cli(
            [
                "--input",
                str(VALID_JSON_FILE),
                "--output",
                str(output_path),
                "--log-file",
                str(self.log_path),
            ]
        )

        self.assertEqual(
            exit_code,
            EXIT_PROCESSING_ERROR,
        )
        self.assertEqual(output, "")
        self.assertIn(
            "OutputPathError",
            error,
        )
        self.assertFalse(output_path.exists())

    def test_module_help_command_returns_zero(
        self,
    ) -> None:
        completed_process = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.saas_support",
                "--help",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            completed_process.returncode,
            0,
        )
        self.assertIn(
            "--input",
            completed_process.stdout,
        )
        self.assertIn(
            "--output",
            completed_process.stdout,
        )


if __name__ == "__main__":
    unittest.main()
