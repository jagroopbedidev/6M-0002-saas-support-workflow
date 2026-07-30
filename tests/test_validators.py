from __future__ import annotations

import unittest
from pathlib import Path

from src.saas_support.loaders import load_csv, load_json
from src.saas_support.validators import (
    DataValidationError,
    validate_input_data,
    validate_subscription_records,
    validate_support_records,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

JSON_VALID_DIR = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "valid"
)

JSON_MALFORMED_DIR = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "json"
    / "malformed"
)

CSV_VALID_DIR = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "csv"
    / "valid"
)

CSV_MALFORMED_DIR = (
    PROJECT_ROOT
    / "data"
    / "fixtures"
    / "csv"
    / "malformed"
)


class SubscriptionValidatorTests(unittest.TestCase):
    def test_valid_subscription_record_is_accepted(self) -> None:
        data = load_json(
            JSON_VALID_DIR / "subscription_01.json"
        )

        records = validate_subscription_records(data)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["subscription_id"],
            "SUB-0001",
        )

    def test_missing_subscription_id_is_rejected(self) -> None:
        data = load_json(
            JSON_MALFORMED_DIR
            / "malformed_json_02_missing_subscription_id.json"
        )

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)

    def test_wrong_revenue_type_is_rejected(self) -> None:
        data = load_json(
            JSON_MALFORMED_DIR
            / "malformed_json_03_wrong_data_type.json"
        )

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)

    def test_invalid_subscription_status_is_rejected(self) -> None:
        data = load_json(
            JSON_MALFORMED_DIR
            / "malformed_json_04_invalid_status.json"
        )

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)

    def test_duplicate_subscription_id_is_rejected(self) -> None:
        data = load_json(
            JSON_MALFORMED_DIR
            / "malformed_json_05_duplicate_ids.json"
        )

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)

    def test_negative_monthly_revenue_is_rejected(self) -> None:
        data = {
            "subscription_id": "SUB-NEGATIVE",
            "customer_id": "CUST-NEGATIVE",
            "plan": "starter",
            "status": "active",
            "monthly_revenue": -1,
        }

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)

    def test_churn_score_outside_range_is_rejected(self) -> None:
        data = {
            "subscription_id": "SUB-RISK",
            "customer_id": "CUST-RISK",
            "plan": "growth",
            "status": "active",
            "monthly_revenue": 999,
            "churn_risk_score": 1.5,
        }

        with self.assertRaises(DataValidationError):
            validate_subscription_records(data)


class SupportValidatorTests(unittest.TestCase):
    def test_valid_support_records_are_accepted(self) -> None:
        rows = load_csv(
            CSV_VALID_DIR / "support_tickets_01.csv"
        )

        validated_rows = validate_support_records(rows)

        self.assertEqual(len(validated_rows), 3)
        self.assertEqual(
            validated_rows[0]["ticket_id"],
            "TKT-0001",
        )

    def test_missing_csv_header_is_rejected(self) -> None:
        rows = load_csv(
            CSV_MALFORMED_DIR
            / "malformed_csv_01_missing_header.csv"
        )

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)

    def test_missing_required_csv_columns_are_rejected(self) -> None:
        rows = load_csv(
            CSV_MALFORMED_DIR
            / "malformed_csv_02_missing_required_column.csv"
        )

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)

    def test_duplicate_ticket_id_is_rejected(self) -> None:
        rows = load_csv(
            CSV_MALFORMED_DIR
            / "malformed_csv_03_duplicate_ticket.csv"
        )

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)

    def test_formula_injection_is_rejected(self) -> None:
        rows = load_csv(
            CSV_MALFORMED_DIR
            / "malformed_csv_04_formula_injection.csv"
        )

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)

    def test_invalid_priority_is_rejected(self) -> None:
        rows = load_csv(
            CSV_MALFORMED_DIR
            / "malformed_csv_05_invalid_priority.csv"
        )

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)

    def test_negative_resolution_hours_are_rejected(self) -> None:
        rows = [
            {
                "ticket_id": "TKT-NEGATIVE",
                "customer_id": "CUST-NEGATIVE",
                "subscription_id": "SUB-NEGATIVE",
                "priority": "high",
                "category": "technical",
                "status": "open",
                "resolution_hours": "-3",
            }
        ]

        with self.assertRaises(DataValidationError):
            validate_support_records(rows)


class ValidatorDispatchTests(unittest.TestCase):
    def test_json_data_is_dispatched_to_subscription_validator(
        self,
    ) -> None:
        path = JSON_VALID_DIR / "subscription_02.json"
        data = load_json(path)

        records = validate_input_data(data, path)

        self.assertEqual(
            records[0]["subscription_id"],
            "SUB-0002",
        )

    def test_csv_data_is_dispatched_to_support_validator(
        self,
    ) -> None:
        path = CSV_VALID_DIR / "support_tickets_02.csv"
        rows = load_csv(path)

        validated_rows = validate_input_data(rows, path)

        self.assertEqual(len(validated_rows), 3)

    def test_unsupported_validation_type_is_rejected(self) -> None:
        with self.assertRaises(DataValidationError):
            validate_input_data([], ".txt")


if __name__ == "__main__":
    unittest.main()
