from __future__ import annotations

import csv
import logging
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from src.saas_support.loaders import load_input
from src.saas_support.validators import validate_input_data


LOGGER = logging.getLogger("saas_support.pipeline")


class PipelineError(Exception):
    """Base exception for input-processing pipeline failures."""


class OutputPathError(PipelineError):
    """Raised when the requested output path is unsafe or invalid."""


class OutputWriteError(PipelineError):
    """Raised when validated data cannot be written safely."""


@dataclass(frozen=True)
class ProcessingResult:
    """Summary returned after successful input processing."""

    input_path: Path
    output_path: Path
    file_type: str
    record_count: int


def _normalise_path(path: str | Path) -> Path:
    """Convert a string or Path object into an expanded Path."""

    return Path(path).expanduser()


def _validate_output_path(
    input_path: Path,
    output_path: Path,
) -> None:
    """
    Verify that the output path is safe for the current input file.

    The function prevents:

    - Writing directly over the original input file.
    - Passing an existing directory as the output file.
    - Writing JSON data to a CSV output or CSV data to JSON output.
    """

    if input_path.resolve() == output_path.resolve():
        raise OutputPathError(
            "Input and output paths must be different. "
            "The original input file will not be overwritten."
        )

    if output_path.exists() and output_path.is_dir():
        raise OutputPathError(
            f"Output path points to a directory: {output_path}"
        )

    input_extension = input_path.suffix.lower()
    output_extension = output_path.suffix.lower()

    if output_extension != input_extension:
        raise OutputPathError(
            "Output extension must match the input extension. "
            f"Input type: '{input_extension or '[no extension]'}'; "
            f"output type: '{output_extension or '[no extension]'}'."
        )


def _record_count(data: Any) -> int:
    """Return the number of logical records contained in loaded data."""

    if isinstance(data, list):
        return len(data)

    return 1


def _write_json(
    output_file: TextIO,
    data: Any,
) -> None:
    """Write JSON data to an already-open temporary file."""

    json.dump(
        data,
        output_file,
        indent=2,
        ensure_ascii=False,
    )

    output_file.write("\n")


def _write_csv(
    output_file: TextIO,
    rows: list[dict[str, Any]],
) -> None:
    """Write validated CSV rows to an already-open temporary file."""

    if not rows:
        raise OutputWriteError(
            "Validated CSV data contains no rows to write."
        )

    fieldnames = list(rows[0].keys())

    writer = csv.DictWriter(
        output_file,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )

    writer.writeheader()
    writer.writerows(rows)


def _process_input_file(
    input_path: str | Path,
    output_path: str | Path,
) -> ProcessingResult:
    """
    Load, validate and safely write one JSON or CSV input file.

    The final output is replaced only after:

    1. The complete input has been loaded.
    2. Every record has passed validation.
    3. The complete temporary output has been written.
    4. The temporary output has been flushed to disk.

    When any operation fails, an existing final output remains unchanged.
    """

    source_path = _normalise_path(input_path)
    destination_path = _normalise_path(output_path)

    _validate_output_path(
        source_path,
        destination_path,
    )

    loaded_data = load_input(source_path)

    validated_records = validate_input_data(
        loaded_data,
        source_path,
    )

    destination_directory = destination_path.parent
    temporary_path: Path | None = None

    try:
        destination_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination_directory,
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            if source_path.suffix.lower() == ".json":
                _write_json(
                    temporary_file,
                    loaded_data,
                )
            else:
                _write_csv(
                    temporary_file,
                    validated_records,
                )

            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(
            temporary_path,
            destination_path,
        )

        temporary_path = None

    except OutputWriteError:
        raise

    except (OSError, TypeError, ValueError, csv.Error) as error:
        raise OutputWriteError(
            f"Validated output could not be written safely to "
            f"'{destination_path}'. Existing output was not modified. "
            f"Reason: {error}"
        ) from error

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()
            except OSError:
                pass

    return ProcessingResult(
        input_path=source_path,
        output_path=destination_path,
        file_type=source_path.suffix.lower().lstrip("."),
        record_count=_record_count(loaded_data),
    )



def process_input_file(
    input_path: str | Path,
    output_path: str | Path,
) -> ProcessingResult:
    """
    Process an input file and record structured success or failure events.

    Record contents and secrets are deliberately excluded from logs.
    """

    source_path = _normalise_path(input_path)
    destination_path = _normalise_path(output_path)

    LOGGER.info(
        "Input processing started",
        extra={
            "event": "processing_started",
            "status": "started",
            "input_path": str(source_path),
            "output_path": str(destination_path),
            "file_type": (
                source_path.suffix.lower().lstrip(".")
                or None
            ),
        },
    )

    try:
        result = _process_input_file(
            source_path,
            destination_path,
        )
    except Exception as error:
        LOGGER.error(
            "Input processing failed: %s",
            error,
            extra={
                "event": "processing_failed",
                "status": "failed",
                "input_path": str(source_path),
                "output_path": str(destination_path),
                "file_type": (
                    source_path.suffix.lower().lstrip(".")
                    or None
                ),
                "error_type": type(error).__name__,
            },
        )
        raise

    LOGGER.info(
        "Input processing completed",
        extra={
            "event": "processing_completed",
            "status": "success",
            "input_path": str(result.input_path),
            "output_path": str(result.output_path),
            "file_type": result.file_type,
            "record_count": result.record_count,
        },
    )

    return result


__all__ = [
    "PipelineError",
    "OutputPathError",
    "OutputWriteError",
    "ProcessingResult",
    "process_input_file",
]
