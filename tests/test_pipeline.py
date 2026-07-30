from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.saas_support.loaders import InputParseError
from src.saas_support.pipeline import (
    OutputPathError,
    OutputWriteError,
    process_input_file,
)
from src.saas_support.validators import DataValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID_JSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "valid"
    / "subscription_01.json"
)

INVALID_JSON_SYNTAX_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "malformed"
    / "malformed_json_01_invalid_syntax.json"
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

INVALID_CSV_RECORD_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "csv"
    / "malformed"
    / "malformed_csv_04_formula_injection.csv"
)


class SafeOutputPipelineTests(unittest.TestCase):
    def test_valid_json_creates_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.json"
            )

            result = process_input_file(
                VALID_JSON_FILE,
                output_path,
            )

            written_data = json.loads(
                output_path.read_text(encoding="utf-8")
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual(result.record_count, 1)
            self.assertEqual(result.file_type, "json")
            self.assertEqual(
                written_data["subscription_id"],
                "SUB-0001",
            )

    def test_valid_csv_creates_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.csv"
            )

            result = process_input_file(
                VALID_CSV_FILE,
                output_path,
            )

            with output_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as csv_file:
                rows = list(csv.DictReader(csv_file))

            self.assertEqual(result.record_count, 3)
            self.assertEqual(result.file_type, "csv")
            self.assertEqual(len(rows), 3)
            self.assertEqual(
                rows[0]["ticket_id"],
                "TKT-0001",
            )

    def test_successful_processing_replaces_existing_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.json"
            )

            output_path.write_text(
                '{"status": "old"}\n',
                encoding="utf-8",
            )

            process_input_file(
                VALID_JSON_FILE,
                output_path,
            )

            written_data = json.loads(
                output_path.read_text(encoding="utf-8")
            )

            self.assertEqual(
                written_data["subscription_id"],
                "SUB-0001",
            )

    def test_invalid_json_syntax_preserves_existing_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.json"
            )

            original_content = b'{"status": "stable"}\n'
            output_path.write_bytes(original_content)

            with self.assertRaises(InputParseError):
                process_input_file(
                    INVALID_JSON_SYNTAX_FILE,
                    output_path,
                )

            self.assertEqual(
                output_path.read_bytes(),
                original_content,
            )

    def test_invalid_json_record_preserves_existing_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.json"
            )

            original_content = b'{"status": "stable"}\n'
            output_path.write_bytes(original_content)

            with self.assertRaises(DataValidationError):
                process_input_file(
                    INVALID_JSON_RECORD_FILE,
                    output_path,
                )

            self.assertEqual(
                output_path.read_bytes(),
                original_content,
            )

    def test_invalid_csv_record_preserves_existing_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.csv"
            )

            original_content = (
                b"status,message\n"
                b"stable,existing output\n"
            )

            output_path.write_bytes(original_content)

            with self.assertRaises(DataValidationError):
                process_input_file(
                    INVALID_CSV_RECORD_FILE,
                    output_path,
                )

            self.assertEqual(
                output_path.read_bytes(),
                original_content,
            )

    def test_missing_output_directory_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory)
                / "nested"
                / "output"
                / "result.json"
            )

            process_input_file(
                VALID_JSON_FILE,
                output_path,
            )

            self.assertTrue(output_path.is_file())

    def test_input_and_output_paths_cannot_match(self) -> None:
        original_content = VALID_JSON_FILE.read_bytes()

        with self.assertRaises(OutputPathError):
            process_input_file(
                VALID_JSON_FILE,
                VALID_JSON_FILE,
            )

        self.assertEqual(
            VALID_JSON_FILE.read_bytes(),
            original_content,
        )

    def test_output_extension_must_match_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = (
                Path(temporary_directory) / "result.csv"
            )

            with self.assertRaises(OutputPathError):
                process_input_file(
                    VALID_JSON_FILE,
                    output_path,
                )

            self.assertFalse(output_path.exists())

    def test_failed_write_preserves_output_and_removes_temp_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_path = directory / "result.json"

            original_content = b'{"status": "stable"}\n'
            output_path.write_bytes(original_content)

            with patch(
                "src.saas_support.pipeline._write_json",
                side_effect=OSError(
                    "Simulated disk-write failure"
                ),
            ):
                with self.assertRaises(OutputWriteError):
                    process_input_file(
                        VALID_JSON_FILE,
                        output_path,
                    )

            temporary_files = list(
                directory.glob(".result.json.*.tmp")
            )

            self.assertEqual(
                output_path.read_bytes(),
                original_content,
            )

            self.assertEqual(
                temporary_files,
                [],
            )


if __name__ == "__main__":
    unittest.main()
