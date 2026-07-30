from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class InputLoadError(Exception):
    """Base exception for expected input-loading errors."""


class InputFileNotFoundError(InputLoadError):
    """Raised when the requested input file does not exist."""


class InvalidInputPathError(InputLoadError):
    """Raised when the supplied path is not a normal file."""


class UnsupportedFileTypeError(InputLoadError):
    """Raised when the input file extension is not supported."""


class InputParseError(InputLoadError):
    """Raised when an input file cannot be parsed safely."""


def _validate_input_file(path: str | Path) -> Path:
    """
    Convert a string or Path into a validated Path object.

    The function confirms that:

    - The path exists.
    - The path points to a file.
    - A folder is not being passed as an input file.
    """

    input_path = Path(path).expanduser()

    if not input_path.exists():
        raise InputFileNotFoundError(
            f"Input file does not exist: {input_path}"
        )

    if not input_path.is_file():
        raise InvalidInputPathError(
            f"Input path is not a file: {input_path}"
        )

    return input_path


def _load_json_file(input_path: Path) -> Any:
    """
    Parse a previously validated JSON file.

    UTF-8-SIG is used so that normal UTF-8 files and files containing
    a UTF-8 byte-order mark can both be read safely.
    """

    try:
        with input_path.open(
            mode="r",
            encoding="utf-8-sig",
        ) as json_file:
            return json.load(json_file)

    except json.JSONDecodeError as error:
        raise InputParseError(
            "Invalid JSON in "
            f"'{input_path}' at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    except UnicodeDecodeError as error:
        raise InputParseError(
            f"JSON file is not valid UTF-8: {input_path}"
        ) from error

    except OSError as error:
        raise InputLoadError(
            f"JSON file could not be read: {input_path}. "
            f"Reason: {error}"
        ) from error


def _load_csv_file(input_path: Path) -> list[dict]:
    """
    Parse a previously validated CSV file.

    Each CSV row is returned as a dictionary whose keys come from
    the CSV header.
    """

    try:
        with input_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(
                csv_file,
                strict=True,
            )

            return list(reader)

    except csv.Error as error:
        raise InputParseError(
            f"Invalid CSV syntax in '{input_path}': {error}"
        ) from error

    except UnicodeDecodeError as error:
        raise InputParseError(
            f"CSV file is not valid UTF-8: {input_path}"
        ) from error

    except OSError as error:
        raise InputLoadError(
            f"CSV file could not be read: {input_path}. "
            f"Reason: {error}"
        ) from error


def load_json(path: str | Path) -> Any:
    """
    Load and parse one JSON file.

    This function reads the file only. It does not change, overwrite
    or delete the original input file.
    """

    input_path = _validate_input_file(path)
    return _load_json_file(input_path)


def load_csv(path: str | Path) -> list[dict]:
    """
    Load and parse one CSV file.

    This function reads the file only. It does not change, overwrite
    or delete the original input file.
    """

    input_path = _validate_input_file(path)
    return _load_csv_file(input_path)


def load_input(path: str | Path) -> Any:
    """
    Load a supported input file based on its extension.

    Supported formats:

    - .json
    - .csv
    """

    input_path = _validate_input_file(path)
    extension = input_path.suffix.lower()

    if extension == ".json":
        return _load_json_file(input_path)

    if extension == ".csv":
        return _load_csv_file(input_path)

    raise UnsupportedFileTypeError(
        "Unsupported input format "
        f"'{extension or '[no extension]'}' for file: {input_path}. "
        "Supported formats are .json and .csv."
    )


__all__ = [
    "InputLoadError",
    "InputFileNotFoundError",
    "InvalidInputPathError",
    "UnsupportedFileTypeError",
    "InputParseError",
    "load_json",
    "load_csv",
    "load_input",
]
