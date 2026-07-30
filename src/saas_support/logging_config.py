from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOGGER_NAME = "saas_support"

OPTIONAL_LOG_FIELDS = (
    "event",
    "status",
    "input_path",
    "output_path",
    "file_type",
    "record_count",
    "error_type",
)


class JsonLineFormatter(logging.Formatter):
    """
    Convert each Python log record into one JSON object.

    Each JSON object is written on a separate line, producing a JSONL file.
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created,
            tz=timezone.utc,
        ).isoformat(timespec="milliseconds")

        if timestamp.endswith("+00:00"):
            timestamp = timestamp[:-6] + "Z"

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in OPTIONAL_LOG_FIELDS:
            value = getattr(record, field_name, None)

            if value is not None:
                payload[field_name] = value

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def _resolve_log_level(level: str | int) -> int:
    """Convert a logging-level name or integer into a valid level."""

    if isinstance(level, int):
        return level

    level_name = str(level).strip().upper()
    resolved_level = logging.getLevelNamesMapping().get(level_name)

    if resolved_level is None:
        raise ValueError(
            f"Invalid logging level '{level}'. "
            "Use DEBUG, INFO, WARNING, ERROR or CRITICAL."
        )

    return resolved_level


def shutdown_logging() -> None:
    """
    Close and remove handlers owned by the application logger.

    Closing file handlers is especially important during automated tests
    and on Windows, where an open file cannot always be deleted.
    """

    logger = logging.getLogger(LOGGER_NAME)

    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)


def configure_logging(
    log_path: str | Path = "logs/application.jsonl",
    level: str | int = "INFO",
    *,
    console: bool = False,
) -> logging.Logger:
    """
    Configure structured JSONL application logging.

    Parameters:

    - log_path: Destination JSONL log file.
    - level: Minimum log level.
    - console: Also show human-readable messages in the terminal.
    """

    resolved_level = _resolve_log_level(level)
    output_path = Path(log_path).expanduser()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(LOGGER_NAME)

    shutdown_logging()

    logger.setLevel(resolved_level)
    logger.propagate = False

    file_handler = logging.FileHandler(
        output_path,
        encoding="utf-8",
    )

    file_handler.setLevel(resolved_level)
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(resolved_level)
        console_handler.setFormatter(
            logging.Formatter(
                "%(levelname)s: %(message)s"
            )
        )
        logger.addHandler(console_handler)

    logger.info(
        "Application logging configured",
        extra={
            "event": "logging_configured",
            "status": "success",
            "output_path": str(output_path),
        },
    )

    return logger


def get_logger(component: str | None = None) -> logging.Logger:
    """
    Return the application logger or a named child logger.

    Example:

        get_logger("pipeline")

    returns:

        saas_support.pipeline
    """

    if component:
        cleaned_component = component.strip(".")

        if cleaned_component:
            return logging.getLogger(
                f"{LOGGER_NAME}.{cleaned_component}"
            )

    return logging.getLogger(LOGGER_NAME)


__all__ = [
    "JsonLineFormatter",
    "configure_logging",
    "get_logger",
    "shutdown_logging",
]
