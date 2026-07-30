from __future__ import annotations

import unittest
from pathlib import Path

from src.saas_support.loaders import (
    InputParseError,
    load_csv,
    load_json,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures"


class StarterRepositoryTests(unittest.TestCase):
    def test_repository_contains_thirty_fixtures(self) -> None:
        fixture_files = [
            path
            for path in FIXTURE_ROOT.rglob("*")
            if path.is_file()
        ]

        self.assertEqual(
            len(fixture_files),
            30,
            "The starter repository must contain exactly 30 fixture files.",
        )

    def test_valid_json_fixture_directory_exists(self) -> None:
        directory = FIXTURE_ROOT / "json" / "valid"
        self.assertTrue(directory.is_dir())

    def test_malformed_json_fixture_directory_exists(self) -> None:
        directory = FIXTURE_ROOT / "json" / "malformed"
        self.assertTrue(directory.is_dir())

    def test_valid_csv_fixture_directory_exists(self) -> None:
        directory = FIXTURE_ROOT / "csv" / "valid"
        self.assertTrue(directory.is_dir())

    def test_malformed_csv_fixture_directory_exists(self) -> None:
        directory = FIXTURE_ROOT / "csv" / "malformed"
        self.assertTrue(directory.is_dir())

    def test_valid_json_can_be_loaded(self) -> None:
        input_file = (
            FIXTURE_ROOT
            / "json"
            / "valid"
            / "subscription_01.json"
        )

        data = load_json(input_file)

        self.assertEqual(
            data["subscription_id"],
            "SUB-0001",
        )

    def test_invalid_json_syntax_is_rejected(self) -> None:
        input_file = (
            FIXTURE_ROOT
            / "json"
            / "malformed"
            / "malformed_json_01_invalid_syntax.json"
        )

        with self.assertRaises(InputParseError):
            load_json(input_file)

    def test_valid_csv_can_be_loaded(self) -> None:
        input_file = (
            FIXTURE_ROOT
            / "csv"
            / "valid"
            / "support_tickets_01.csv"
        )

        rows = load_csv(input_file)

        self.assertEqual(len(rows), 3)

    @unittest.skip(
        "TODO: Complete after implementing CSV record validation."
    )
    def test_malformed_csv_is_rejected(self) -> None:
        pass

    @unittest.skip(
        "TODO: Complete after implementing safe output writes."
    )
    def test_failed_processing_preserves_existing_output(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
