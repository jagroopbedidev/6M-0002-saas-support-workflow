from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

JSON_VALID_DIR = PROJECT_ROOT / "data" / "fixtures" / "json" / "valid"
JSON_MALFORMED_DIR = PROJECT_ROOT / "data" / "fixtures" / "json" / "malformed"

CSV_VALID_DIR = PROJECT_ROOT / "data" / "fixtures" / "csv" / "valid"
CSV_MALFORMED_DIR = PROJECT_ROOT / "data" / "fixtures" / "csv" / "malformed"


def create_directories() -> None:
    """Create all fixture directories when they do not exist."""

    directories = [
        JSON_VALID_DIR,
        JSON_MALFORMED_DIR,
        CSV_VALID_DIR,
        CSV_MALFORMED_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def create_valid_json_fixtures() -> None:
    """Create ten valid subscription JSON fixtures."""

    plans = ["starter", "growth", "business", "enterprise"]
    statuses = ["active", "trial", "past_due", "cancelled"]

    for number in range(1, 11):
        record = {
            "subscription_id": f"SUB-{number:04d}",
            "customer_id": f"CUST-{number:04d}",
            "company_name": f"Sample Company {number}",
            "plan": plans[(number - 1) % len(plans)],
            "status": statuses[(number - 1) % len(statuses)],
            "monthly_revenue": float(499 + number * 100),
            "support_ticket_count": number % 5,
            "churn_risk_score": round((number % 10) / 10, 2),
        }

        output_path = JSON_VALID_DIR / f"subscription_{number:02d}.json"

        output_path.write_text(
            json.dumps(record, indent=2),
            encoding="utf-8",
        )


def create_malformed_json_fixtures() -> None:
    """Create five intentionally invalid subscription JSON fixtures."""

    malformed_fixtures = {
        "malformed_json_01_invalid_syntax.json": """
{
  "subscription_id": "SUB-1001",
  "customer_id": "CUST-1001",
  "plan": "growth",
}
""".strip(),
        "malformed_json_02_missing_subscription_id.json": """
{
  "customer_id": "CUST-1002",
  "plan": "starter",
  "status": "active",
  "monthly_revenue": 799
}
""".strip(),
        "malformed_json_03_wrong_data_type.json": """
{
  "subscription_id": "SUB-1003",
  "customer_id": "CUST-1003",
  "plan": "business",
  "status": "active",
  "monthly_revenue": "not-a-number"
}
""".strip(),
        "malformed_json_04_invalid_status.json": """
{
  "subscription_id": "SUB-1004",
  "customer_id": "CUST-1004",
  "plan": "growth",
  "status": "unknown-status",
  "monthly_revenue": 1499
}
""".strip(),
        "malformed_json_05_duplicate_ids.json": """
[
  {
    "subscription_id": "SUB-DUPLICATE",
    "customer_id": "CUST-2001",
    "plan": "starter",
    "status": "active",
    "monthly_revenue": 499
  },
  {
    "subscription_id": "SUB-DUPLICATE",
    "customer_id": "CUST-2002",
    "plan": "growth",
    "status": "active",
    "monthly_revenue": 999
  }
]
""".strip(),
    }

    for filename, content in malformed_fixtures.items():
        output_path = JSON_MALFORMED_DIR / filename
        output_path.write_text(content + "\n", encoding="utf-8")


def create_valid_csv_fixtures() -> None:
    """Create ten valid customer-support ticket CSV fixtures."""

    fieldnames = [
        "ticket_id",
        "customer_id",
        "subscription_id",
        "priority",
        "category",
        "status",
        "resolution_hours",
    ]

    priorities = ["low", "medium", "high", "urgent"]
    categories = ["billing", "technical", "account", "cancellation"]
    statuses = ["open", "in_progress", "resolved", "closed"]

    for file_number in range(1, 11):
        output_path = CSV_VALID_DIR / f"support_tickets_{file_number:02d}.csv"

        rows = []

        for row_number in range(1, 4):
            identifier = ((file_number - 1) * 3) + row_number

            rows.append(
                {
                    "ticket_id": f"TKT-{identifier:04d}",
                    "customer_id": f"CUST-{identifier:04d}",
                    "subscription_id": f"SUB-{identifier:04d}",
                    "priority": priorities[(identifier - 1) % len(priorities)],
                    "category": categories[(identifier - 1) % len(categories)],
                    "status": statuses[(identifier - 1) % len(statuses)],
                    "resolution_hours": identifier + 2,
                }
            )

        with output_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def create_malformed_csv_fixtures() -> None:
    """Create five intentionally invalid customer-support CSV fixtures."""

    malformed_fixtures = {
        "malformed_csv_01_missing_header.csv": (
            "TKT-1001,CUST-1001,SUB-1001,high,billing,open,4\n"
        ),
        "malformed_csv_02_missing_required_column.csv": (
            "ticket_id,customer_id,priority,status\n"
            "TKT-1002,CUST-1002,high,open\n"
        ),
        "malformed_csv_03_duplicate_ticket.csv": (
            "ticket_id,customer_id,subscription_id,priority,category,status,"
            "resolution_hours\n"
            "TKT-DUPLICATE,CUST-1003,SUB-1003,medium,technical,open,5\n"
            "TKT-DUPLICATE,CUST-1004,SUB-1004,high,billing,resolved,3\n"
        ),
        "malformed_csv_04_formula_injection.csv": (
            "ticket_id,customer_id,subscription_id,priority,category,status,"
            "resolution_hours\n"
            '"=HYPERLINK(""https://unsafe.example"",""Open"")",'
            "CUST-1005,SUB-1005,high,account,open,7\n"
        ),
        "malformed_csv_05_invalid_priority.csv": (
            "ticket_id,customer_id,subscription_id,priority,category,status,"
            "resolution_hours\n"
            "TKT-1006,CUST-1006,SUB-1006,critical-plus,technical,open,6\n"
        ),
    }

    for filename, content in malformed_fixtures.items():
        output_path = CSV_MALFORMED_DIR / filename
        output_path.write_text(content, encoding="utf-8")


def count_fixture_files() -> int:
    """Return the total number of generated fixture files."""

    fixture_root = PROJECT_ROOT / "data" / "fixtures"

    return sum(
        1
        for path in fixture_root.rglob("*")
        if path.is_file()
    )


def main() -> None:
    create_directories()
    create_valid_json_fixtures()
    create_malformed_json_fixtures()
    create_valid_csv_fixtures()
    create_malformed_csv_fixtures()

    fixture_count = count_fixture_files()

    print(f"Generated fixture files: {fixture_count}")

    if fixture_count != 30:
        raise RuntimeError(
            f"Expected 30 fixtures, but found {fixture_count}."
        )

    print("Starter fixtures generated successfully.")


if __name__ == "__main__":
    main()