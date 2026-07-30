from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.saas_support.loaders import (
    InputFileNotFoundError,
    InputParseError,
    InvalidInputPathError,
    UnsupportedFileTypeError,
    load_csv,
    load_input,
    load_json,
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

INVALID_JSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "malformed"
    / "malformed_json_01_invalid_syntax.json"
)

VALID_CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "csv"
    / "valid"
    / "support_tickets_01.csv"
)


class InputLoaderTests(unittest.TestCase):
    def test_load_json_returns_dictionary(self) -> None:
        data = load_json(VALID_JSON_FILE)

        self.assertIsInstance(data, dict)
        self.assertEqual(
            data["subscription_id"],
            "SUB-0001",
        )

    def test_load_csv_returns_rows(self) -> None:
        rows = load_csv(VALID_CSV_FILE)

        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[0]["ticket_id"],
            "TKT-0001",
        )

    def test_load_input_detects_json_extension(self) -> None:
        data = load_input(VALID_JSON_FILE)

        self.assertIsInstance(data, dict)

    def test_load_input_detects_csv_extension(self) -> None:
        rows = load_input(VALID_CSV_FILE)

        self.assertIsInstance(rows, list)

    def test_missing_file_raises_actionable_error(self) -> None:
        missing_file = PROJECT_ROOT / "data" / "missing.json"

        with self.assertRaises(InputFileNotFoundError):
            load_input(missing_file)

    def test_directory_path_is_rejected(self) -> None:
        directory_path = PROJECT_ROOT / "data" / "fixtures"

        with self.assertRaises(InvalidInputPathError):
            load_input(directory_path)

    def test_unsupported_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            unsupported_file = (
                Path(temporary_directory) / "input.txt"
            )

            unsupported_file.write_text(
                "unsupported content",
                encoding="utf-8",
            )

            with self.assertRaises(UnsupportedFileTypeError):
                load_input(unsupported_file)

    def test_invalid_json_syntax_is_rejected(self) -> None:
        with self.assertRaises(InputParseError):
            load_json(INVALID_JSON_FILE)

    def test_uppercase_json_extension_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            json_file = Path(temporary_directory) / "SAMPLE.JSON"

            json_file.write_text(
                '{"subscription_id": "SUB-UPPERCASE"}',
                encoding="utf-8",
            )

            data = load_input(json_file)

            self.assertEqual(
                data["subscription_id"],
                "SUB-UPPERCASE",
            )

    def test_path_with_spaces_is_supported(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="saas loader test "
        ) as temporary_directory:
            json_file = (
                Path(temporary_directory)
                / "input with spaces.json"
            )

            json_file.write_text(
                '{"subscription_id": "SUB-SPACES"}',
                encoding="utf-8",
            )

            data = load_json(json_file)

            self.assertEqual(
                data["subscription_id"],
                "SUB-SPACES",
            )


if __name__ == "__main__":
    unittest.main()
