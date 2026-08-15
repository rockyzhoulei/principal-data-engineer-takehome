"""
Configuration constants for the data pipeline.

This module centralizes all configurable values, paths, and validation rules.
No hard-coded values should exist in business logic.
"""

from pathlib import Path
from typing import Set

# Project root and data directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CURATED_DATA_DIR = DATA_DIR / "curated"
QUARANTINE_DATA_DIR = DATA_DIR / "quarantine"

# Ensure directories exist
for directory in [RAW_DATA_DIR, CURATED_DATA_DIR, QUARANTINE_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Input file configuration
INPUT_FILE_PATH = RAW_DATA_DIR / "events.csv"  # Can be overridden via CLI
INPUT_FILE_FORMAT = "csv"  # "csv" or "json"

# Output file configuration
CURATED_OUTPUT_PATH = CURATED_DATA_DIR / "events_curated.parquet"
QUARANTINE_OUTPUT_PATH = QUARANTINE_DATA_DIR / "events_invalid.parquet"

# Required columns (must be present in all input files)
REQUIRED_COLUMNS: Set[str] = {
    "event_id",
    "customer_id",
    "event_timestamp",
    "amount",
}

# Column data types (expected types after validation)
EXPECTED_DTYPES = {
    "event_id": "object",
    "source_system": "object",
    "customer_id": "object",
    "event_type": "object",
    "event_timestamp": "object",  # Will be parsed as datetime
    "amount": "float64",
    "currency": "object",
    "ingestion_timestamp": "object",  # Will be parsed as datetime
}

# Accepted values for categorical columns
ACCEPTED_CURRENCIES: Set[str] = {"USD", "EUR", "GBP", "JPY"}

ACCEPTED_SOURCE_SYSTEMS: Set[str] = {"crm", "api", "events", "database"}

# Validation rules
MIN_AMOUNT = 0.0
MAX_AMOUNT = 1_000_000.0

# Deduplication configuration
DEDUP_WINDOW_DAYS = 72  # Keep duplicates within 72 hours
DEDUP_BUSINESS_KEY = ["customer_id", "source_system", "event_id"]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Timestamp format
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601 UTC
