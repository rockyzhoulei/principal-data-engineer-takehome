"""
Utility functions and logging configuration.

This module provides reusable utilities for logging, timestamp parsing, and other common operations.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
import json

from src import config

# Configure logging
def setup_logging() -> logging.Logger:
    """
    Initialize and configure logging for the pipeline.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("pipeline")
    logger.setLevel(config.LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(config.LOG_FORMAT)
    console_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


logger = setup_logging()


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse a timestamp string to datetime object.

    Attempts multiple common formats. Returns None if parsing fails.

    Args:
        timestamp_str: Timestamp string to parse.

    Returns:
        datetime object or None if parsing fails.
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            parsed_dt = datetime.strptime(timestamp_str.strip(), fmt)
            if fmt.endswith("Z"):
                return parsed_dt.replace(tzinfo=timezone.utc)
            return parsed_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def validate_timestamp(timestamp_str: str) -> tuple[bool, Optional[str]]:
    """
    Validate a timestamp string.

    Checks:
    - Valid format (ISO 8601 or common formats)
    - Not a future timestamp

    Args:
        timestamp_str: Timestamp string to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not timestamp_str:
        return False, "Timestamp is missing"

    dt = parse_timestamp(timestamp_str)
    if dt is None:
        return False, f"Invalid timestamp format: {timestamp_str}"

    # Check if timestamp is in the future
    if dt > datetime.now(timezone.utc):
        return False, f"Timestamp is in the future: {timestamp_str}"

    return True, None


def is_valid_uuid_format(value: str) -> bool:
    """
    Simple UUID format check (not cryptographic validation).

    Checks if string matches pattern: 8-4-4-4-12 hex digits.

    Args:
        value: String to check.

    Returns:
        True if matches UUID pattern.
    """
    if not isinstance(value, str):
        return False

    parts = value.split("-")
    if len(parts) != 5:
        return False

    lengths = [8, 4, 4, 4, 12]
    for part, expected_len in zip(parts, lengths):
        if len(part) != expected_len or not all(c in "0123456789abcdefABCDEF" for c in part):
            return False

    return True


def flatten_errors(errors: list[str]) -> str:
    """
    Flatten a list of error messages into a JSON string.

    Args:
        errors: List of error message strings.

    Returns:
        JSON-serialized string of errors.
    """
    return json.dumps(errors)


def log_execution_summary(metrics: dict) -> None:
    """
    Log a summary of pipeline execution metrics.

    Args:
        metrics: Dictionary containing pipeline metrics.
    """
    logger.info("=" * 60)
    logger.info("Pipeline Execution Summary")
    logger.info("=" * 60)
    for key, value in metrics.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 60)
