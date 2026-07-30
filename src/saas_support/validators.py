from __future__ import annotations

from pathlib import Path
from typing import Any


SUBSCRIPTION_REQUIRED_FIELDS = {
    "subscription_id",
    "customer_id",
    "plan",
    "status",
    "monthly_revenue",
}

SUPPORT_REQUIRED_FIELDS = {
    "ticket_id",
    "customer_id",
    "subscription_id",
    "priority",
    "category",
    "status",
    "resolution_hours",
}

ALLOWED_SUBSCRIPTION_PLANS = {
    "starter",
    "growth",
    "business",
    "enterprise",
}

ALLOWED_SUBSCRIPTION_STATUSES = {
    "active",
    "trial",
    "past_due",
    "cancelled",
}

ALLOWED_TICKET_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}

ALLOWED_TICKET_CATEGORIES = {
    "billing",
    "technical",
    "account",
    "cancellation",
}

ALLOWED_TICKET_STATUSES = {
    "open",
    "in_progress",
    "resolved",
    "closed",
}

FORMULA_PREFIXES = ("=", "+", "-", "@")


class DataValidationError(Exception):
    """Raised when loaded input data violates one or more validation rules."""

    def __init__(self, errors: list[str]) -> None:
        if not errors:
            errors = ["Input data failed validation."]

        self.errors = tuple(errors)

        message = "Validation failed:\n- " + "\n- ".join(errors)
        super().__init__(message)


def _is_non_empty_string(value: Any) -> bool:
    """Return True when the value is a non-empty string."""

    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    """Return True for integers or floats, but not Boolean values."""

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def _contains_formula_prefix(value: Any) -> bool:
    """
    Detect values that spreadsheet applications may interpret as formulas.

    CSV formula injection can begin with =, +, - or @.
    """

    if not isinstance(value, str):
        return False

    return value.lstrip().startswith(FORMULA_PREFIXES)


def _check_formula_values(
    record: dict[str, Any],
    record_label: str,
) -> list[str]:
    """Return validation errors for formula-like string values."""

    errors: list[str] = []

    for field_name, value in record.items():
        if field_name is None:
            errors.append(
                f"{record_label} contains more values than its CSV header."
            )
            continue

        if _contains_formula_prefix(value):
            errors.append(
                f"{record_label} field '{field_name}' contains a "
                "potential spreadsheet formula."
            )

    return errors


def _normalise_subscription_records(
    data: Any,
) -> list[dict[str, Any]]:
    """
    Convert one subscription dictionary or a list of dictionaries into a list.
    """

    if isinstance(data, dict):
        return [data]

    if isinstance(data, list):
        if not data:
            raise DataValidationError(
                ["Subscription input contains no records."]
            )

        invalid_positions = [
            str(index)
            for index, record in enumerate(data, start=1)
            if not isinstance(record, dict)
        ]

        if invalid_positions:
            raise DataValidationError(
                [
                    "Subscription records must be JSON objects. "
                    "Invalid record positions: "
                    + ", ".join(invalid_positions)
                ]
            )

        return data

    raise DataValidationError(
        [
            "Subscription input must be a JSON object "
            "or a list of JSON objects."
        ]
    )


def validate_subscription_records(
    data: Any,
) -> list[dict[str, Any]]:
    """
    Validate subscription SaaS records.

    The original loaded records are returned when all records are valid.
    This function does not modify the input data.
    """

    records = _normalise_subscription_records(data)
    errors: list[str] = []
    seen_subscription_ids: set[str] = set()

    for index, record in enumerate(records, start=1):
        record_label = f"Subscription record {index}"

        missing_fields = sorted(
            field
            for field in SUBSCRIPTION_REQUIRED_FIELDS
            if field not in record
        )

        if missing_fields:
            errors.append(
                f"{record_label} is missing required fields: "
                + ", ".join(missing_fields)
            )

        subscription_id = record.get("subscription_id")

        if "subscription_id" in record:
            if not _is_non_empty_string(subscription_id):
                errors.append(
                    f"{record_label} field 'subscription_id' "
                    "must be a non-empty string."
                )
            else:
                cleaned_subscription_id = subscription_id.strip()

                if cleaned_subscription_id in seen_subscription_ids:
                    errors.append(
                        f"{record_label} contains duplicate "
                        f"subscription_id '{cleaned_subscription_id}'."
                    )
                else:
                    seen_subscription_ids.add(cleaned_subscription_id)

        customer_id = record.get("customer_id")

        if (
            "customer_id" in record
            and not _is_non_empty_string(customer_id)
        ):
            errors.append(
                f"{record_label} field 'customer_id' "
                "must be a non-empty string."
            )

        plan = record.get("plan")

        if "plan" in record:
            if not _is_non_empty_string(plan):
                errors.append(
                    f"{record_label} field 'plan' "
                    "must be a non-empty string."
                )
            elif plan.strip().lower() not in ALLOWED_SUBSCRIPTION_PLANS:
                errors.append(
                    f"{record_label} contains invalid plan '{plan}'. "
                    "Allowed plans are: "
                    + ", ".join(sorted(ALLOWED_SUBSCRIPTION_PLANS))
                    + "."
                )

        status = record.get("status")

        if "status" in record:
            if not _is_non_empty_string(status):
                errors.append(
                    f"{record_label} field 'status' "
                    "must be a non-empty string."
                )
            elif (
                status.strip().lower()
                not in ALLOWED_SUBSCRIPTION_STATUSES
            ):
                errors.append(
                    f"{record_label} contains invalid status "
                    f"'{status}'. Allowed statuses are: "
                    + ", ".join(
                        sorted(ALLOWED_SUBSCRIPTION_STATUSES)
                    )
                    + "."
                )

        monthly_revenue = record.get("monthly_revenue")

        if "monthly_revenue" in record:
            if not _is_number(monthly_revenue):
                errors.append(
                    f"{record_label} field 'monthly_revenue' "
                    "must be a number."
                )
            elif monthly_revenue < 0:
                errors.append(
                    f"{record_label} field 'monthly_revenue' "
                    "cannot be negative."
                )

        support_ticket_count = record.get("support_ticket_count")

        if "support_ticket_count" in record:
            if (
                not isinstance(support_ticket_count, int)
                or isinstance(support_ticket_count, bool)
            ):
                errors.append(
                    f"{record_label} field 'support_ticket_count' "
                    "must be an integer."
                )
            elif support_ticket_count < 0:
                errors.append(
                    f"{record_label} field 'support_ticket_count' "
                    "cannot be negative."
                )

        churn_risk_score = record.get("churn_risk_score")

        if "churn_risk_score" in record:
            if not _is_number(churn_risk_score):
                errors.append(
                    f"{record_label} field 'churn_risk_score' "
                    "must be a number."
                )
            elif not 0 <= churn_risk_score <= 1:
                errors.append(
                    f"{record_label} field 'churn_risk_score' "
                    "must be between 0 and 1."
                )

        errors.extend(
            _check_formula_values(
                record,
                record_label,
            )
        )

    if errors:
        raise DataValidationError(errors)

    return records


def validate_support_records(
    rows: Any,
) -> list[dict[str, Any]]:
    """
    Validate customer-support ticket records loaded from a CSV file.

    CSV values are normally strings. Numeric fields are therefore checked
    by safely converting their string representation.
    """

    if not isinstance(rows, list):
        raise DataValidationError(
            ["Support-ticket input must be a list of CSV rows."]
        )

    if not rows:
        raise DataValidationError(
            [
                "CSV input contains no data rows or does not contain "
                "a valid header row."
            ]
        )

    errors: list[str] = []
    seen_ticket_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        record_label = f"Support record {index}"

        if not isinstance(row, dict):
            errors.append(
                f"{record_label} must be represented as a CSV row."
            )
            continue

        row_fields = {
            field_name
            for field_name in row
            if isinstance(field_name, str)
        }

        missing_fields = sorted(
            SUPPORT_REQUIRED_FIELDS - row_fields
        )

        if missing_fields:
            errors.append(
                f"{record_label} is missing required CSV columns: "
                + ", ".join(missing_fields)
            )

        if None in row:
            errors.append(
                f"{record_label} contains more values "
                "than its CSV header."
            )

        ticket_id = row.get("ticket_id")

        if "ticket_id" in row:
            if not _is_non_empty_string(ticket_id):
                errors.append(
                    f"{record_label} field 'ticket_id' "
                    "must be a non-empty string."
                )
            else:
                cleaned_ticket_id = ticket_id.strip()

                if cleaned_ticket_id in seen_ticket_ids:
                    errors.append(
                        f"{record_label} contains duplicate "
                        f"ticket_id '{cleaned_ticket_id}'."
                    )
                else:
                    seen_ticket_ids.add(cleaned_ticket_id)

        for identifier_field in (
            "customer_id",
            "subscription_id",
        ):
            if (
                identifier_field in row
                and not _is_non_empty_string(
                    row.get(identifier_field)
                )
            ):
                errors.append(
                    f"{record_label} field '{identifier_field}' "
                    "must be a non-empty string."
                )

        priority = row.get("priority")

        if "priority" in row:
            if not _is_non_empty_string(priority):
                errors.append(
                    f"{record_label} field 'priority' "
                    "must be a non-empty string."
                )
            elif priority.strip().lower() not in ALLOWED_TICKET_PRIORITIES:
                errors.append(
                    f"{record_label} contains invalid priority "
                    f"'{priority}'. Allowed priorities are: "
                    + ", ".join(
                        sorted(ALLOWED_TICKET_PRIORITIES)
                    )
                    + "."
                )

        category = row.get("category")

        if "category" in row:
            if not _is_non_empty_string(category):
                errors.append(
                    f"{record_label} field 'category' "
                    "must be a non-empty string."
                )
            elif category.strip().lower() not in ALLOWED_TICKET_CATEGORIES:
                errors.append(
                    f"{record_label} contains invalid category "
                    f"'{category}'. Allowed categories are: "
                    + ", ".join(
                        sorted(ALLOWED_TICKET_CATEGORIES)
                    )
                    + "."
                )

        status = row.get("status")

        if "status" in row:
            if not _is_non_empty_string(status):
                errors.append(
                    f"{record_label} field 'status' "
                    "must be a non-empty string."
                )
            elif status.strip().lower() not in ALLOWED_TICKET_STATUSES:
                errors.append(
                    f"{record_label} contains invalid status "
                    f"'{status}'. Allowed statuses are: "
                    + ", ".join(
                        sorted(ALLOWED_TICKET_STATUSES)
                    )
                    + "."
                )

        resolution_hours = row.get("resolution_hours")

        if "resolution_hours" in row:
            try:
                parsed_resolution_hours = int(
                    str(resolution_hours).strip()
                )
            except (TypeError, ValueError):
                errors.append(
                    f"{record_label} field 'resolution_hours' "
                    "must be an integer."
                )
            else:
                if parsed_resolution_hours < 0:
                    errors.append(
                        f"{record_label} field 'resolution_hours' "
                        "cannot be negative."
                    )

        errors.extend(
            _check_formula_values(
                row,
                record_label,
            )
        )

    if errors:
        raise DataValidationError(errors)

    return rows


def validate_input_data(
    data: Any,
    file_type: str | Path,
) -> list[dict[str, Any]]:
    """
    Dispatch loaded data to the correct validator.

    file_type can be '.json', 'json', '.csv', 'csv' or a Path object.
    """

    if isinstance(file_type, Path):
        extension = file_type.suffix.lower()
    else:
        text_value = str(file_type).strip().lower()
        extension = (
            text_value
            if text_value.startswith(".")
            else f".{text_value}"
        )

    if extension == ".json":
        return validate_subscription_records(data)

    if extension == ".csv":
        return validate_support_records(data)

    raise DataValidationError(
        [
            f"Validation is not available for file type "
            f"'{extension}'. Supported types are .json and .csv."
        ]
    )


__all__ = [
    "DataValidationError",
    "validate_subscription_records",
    "validate_support_records",
    "validate_input_data",
]
