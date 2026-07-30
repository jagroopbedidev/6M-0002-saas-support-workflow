from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.saas_support.logging_config import (
    configure_logging,
    shutdown_logging,
)
from src.saas_support.pipeline import process_input_file
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

INVALID_JSON_RECORD_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "malformed"
    / "malformed_json_02_missing_subscription_id.json"
)


def read_json_lines(path: Path) -> list[dict]:
    """Read a JSONL file and return its records."""

    return [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


class StructuredLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.addCleanup(
            self.temporary_directory.cleanup
        )
        self.addCleanup(shutdown_logging)

        self.directory = Path(
            self.temporary_directory.name
        )

        self.log_path = (
            self.directory / "logs" / "application.jsonl"
        )

    def test_successful_processing_writes_structured_logs(
        self,
    ) -> None:
        configure_logging(
            self.log_path,
            console=False,
        )

        output_path = self.directory / "result.json"

        process_input_file(
            VALID_JSON_FILE,
            output_path,
        )

        shutdown_logging()

        records = read_json_lines(self.log_path)
        events = [
            record.get("event")
            for record in records
        ]

        self.assertIn(
            "logging_configured",
            events,
        )
        self.assertIn(
            "processing_started",
            events,
        )
        self.assertIn(
            "processing_completed",
            events,
        )

        completed_record = next(
            record
            for record in records
            if record.get("event")
            == "processing_completed"
        )

        self.assertEqual(
            completed_record["status"],
            "success",
        )
        self.assertEqual(
            completed_record["file_type"],
            "json",
        )
        self.assertEqual(
            completed_record["record_count"],
            1,
        )

    def test_validation_failure_writes_error_log(
        self,
    ) -> None:
        configure_logging(
            self.log_path,
            console=False,
        )

        output_path = self.directory / "result.json"
        original_content = b'{"status": "stable"}\n'
        output_path.write_bytes(original_content)

        with self.assertRaises(DataValidationError):
            process_input_file(
                INVALID_JSON_RECORD_FILE,
                output_path,
            )

        shutdown_logging()

        records = read_json_lines(self.log_path)

        failure_record = next(
            record
            for record in records
            if record.get("event")
            == "processing_failed"
        )

        self.assertEqual(
            failure_record["status"],
            "failed",
        )
        self.assertEqual(
            failure_record["error_type"],
            "DataValidationError",
        )
        self.assertEqual(
            output_path.read_bytes(),
            original_content,
        )

    def test_log_does_not_contain_full_customer_record(
        self,
    ) -> None:
        configure_logging(
            self.log_path,
            console=False,
        )

        process_input_file(
            VALID_JSON_FILE,
            self.directory / "result.json",
        )

        shutdown_logging()

        log_content = self.log_path.read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "Sample Company 1",
            log_content,
        )
        self.assertNotIn(
            '"monthly_revenue"',
            log_content,
        )

    def test_reconfiguration_does_not_duplicate_handlers(
        self,
    ) -> None:
        configure_logging(
            self.log_path,
            console=False,
        )

        configure_logging(
            self.log_path,
            console=False,
        )

        process_input_file(
            VALID_JSON_FILE,
            self.directory / "result.json",
        )

        shutdown_logging()

        records = read_json_lines(self.log_path)

        completed_records = [
            record
            for record in records
            if record.get("event")
            == "processing_completed"
        ]

        self.assertEqual(
            len(completed_records),
            1,
        )


if __name__ == "__main__":
    unittest.main()
