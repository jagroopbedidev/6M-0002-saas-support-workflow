from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from src.saas_support.loaders import InputLoadError
from src.saas_support.logging_config import (
    configure_logging,
    get_logger,
    shutdown_logging,
)
from src.saas_support.pipeline import (
    PipelineError,
    process_input_file,
)
from src.saas_support.validators import DataValidationError


EXIT_SUCCESS = 0
EXIT_PROCESSING_ERROR = 1
EXIT_CONFIGURATION_ERROR = 2

VALID_LOG_LEVELS = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}


def _parse_log_level(value: str) -> str:
    """Validate and normalize a command-line logging level."""

    normalized_value = value.strip().upper()

    if normalized_value not in VALID_LOG_LEVELS:
        raise argparse.ArgumentTypeError(
            "Log level must be one of: "
            + ", ".join(sorted(VALID_LOG_LEVELS))
        )

    return normalized_value


def build_parser() -> argparse.ArgumentParser:
    """Create and return the application command-line parser."""

    parser = argparse.ArgumentParser(
        prog="saas-support",
        description=(
            "Load, validate and safely process subscription SaaS "
            "JSON files or customer-support CSV files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input",
        dest="input_path",
        required=True,
        type=Path,
        help="Path to the source .json or .csv file.",
    )

    parser.add_argument(
        "--output",
        dest="output_path",
        required=True,
        type=Path,
        help=(
            "Path to the safely generated output file. "
            "Its extension must match the input extension."
        ),
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/application.jsonl"),
        help="Path to the structured JSONL application log.",
    )

    parser.add_argument(
        "--log-level",
        type=_parse_log_level,
        default="INFO",
        help=(
            "Minimum logging level: DEBUG, INFO, WARNING, "
            "ERROR or CRITICAL."
        ),
    )

    parser.add_argument(
        "--console-log",
        action="store_true",
        help="Also show application log messages in the terminal.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """
    Run the command-line application and return an operating-system exit code.

    Exit codes:

    - 0: Processing completed successfully.
    - 1: Expected input, validation or pipeline failure.
    - 2: Command or application configuration failure.
    """

    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        configure_logging(
            log_path=arguments.log_file,
            level=arguments.log_level,
            console=arguments.console_log,
        )
    except (OSError, ValueError) as error:
        print(
            "Application logging could not be configured.",
            file=sys.stderr,
        )
        print(
            f"Reason: {error}",
            file=sys.stderr,
        )
        return EXIT_CONFIGURATION_ERROR

    logger = get_logger("cli")

    try:
        result = process_input_file(
            arguments.input_path,
            arguments.output_path,
        )

    except (
        InputLoadError,
        DataValidationError,
        PipelineError,
    ) as error:
        print(
            "Processing failed.",
            file=sys.stderr,
        )
        print(
            f"Error type: {type(error).__name__}",
            file=sys.stderr,
        )
        print(
            f"Reason: {error}",
            file=sys.stderr,
        )
        print(
            "Existing output was not modified.",
            file=sys.stderr,
        )

        return EXIT_PROCESSING_ERROR

    except Exception as error:
        logger.exception(
            "Unexpected command-line processing failure",
            extra={
                "event": "cli_unexpected_failure",
                "status": "failed",
                "input_path": str(arguments.input_path),
                "output_path": str(arguments.output_path),
                "error_type": type(error).__name__,
            },
        )

        print(
            "Processing failed because of an unexpected error.",
            file=sys.stderr,
        )
        print(
            f"Error type: {type(error).__name__}",
            file=sys.stderr,
        )
        print(
            "Review the structured application log for details.",
            file=sys.stderr,
        )

        return EXIT_CONFIGURATION_ERROR

    else:
        print("Processing completed successfully.")
        print(f"Input: {result.input_path}")
        print(f"Output: {result.output_path}")
        print(f"File type: {result.file_type}")
        print(f"Records processed: {result.record_count}")
        print(f"Structured log: {arguments.log_file}")

        return EXIT_SUCCESS

    finally:
        shutdown_logging()


if __name__ == "__main__":
    raise SystemExit(main())
