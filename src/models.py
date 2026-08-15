"""
Data model and schema definitions.

This module defines the structure and types for input, intermediate, and output data.
Lightweight type definitions without heavy OOP complexity.
"""

from typing import TypedDict, Dict, Any, Optional
from datetime import datetime


class EventRecord(TypedDict, total=False):
    """Raw event record from source system."""

    event_id: str
    source_system: str
    customer_id: str
    event_type: str
    event_timestamp: str
    amount: float
    currency: str
    ingestion_timestamp: str


class ValidationResult(TypedDict):
    """Result of validation operation."""

    is_valid: bool
    errors: list[str]
    record: Optional[Dict[str, Any]]


class PipelineMetrics(TypedDict, total=False):
    """Execution metrics for pipeline run."""

    input_row_count: int
    valid_row_count: int
    invalid_row_count: int
    duplicate_row_count: int
    output_row_count: int
    processing_time_seconds: float


# Schema specification for curated output
CURATED_SCHEMA = {
    "event_id": "object",
    "customer_id": "object",
    "event_timestamp": "datetime64[ns]",
    "amount": "float64",
    "currency": "object",
    "source_system": "object",
    "ingestion_timestamp": "datetime64[ns]",
}

# Schema specification for quarantine output
QUARANTINE_SCHEMA = {
    "event_id": "object",
    "customer_id": "object",
    "event_timestamp": "object",
    "amount": "object",
    "currency": "object",
    "source_system": "object",
    "ingestion_timestamp": "object",
    "validation_errors": "object",  # JSON string of errors
}
