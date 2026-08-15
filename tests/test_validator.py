"""
Unit tests for the validator module.

Tests validation functions for required fields, data types,
accepted values, timestamps, and amount ranges.
"""

import pytest
import pandas as pd
from datetime import datetime

from src.validator import (
    validate_required_fields,
    validate_data_types,
    validate_accepted_values,
    validate_timestamps,
    validate_amount_range,
)


@pytest.fixture
def sample_valid_record():
    """Fixture providing a valid sample record."""
    return pd.DataFrame({
        "event_id": ["evt-001"],
        "customer_id": ["cust-123"],
        "event_timestamp": ["2026-01-15T10:30:00Z"],
        "amount": [125.50],
        "currency": ["USD"],
        "source_system": ["crm"],
        "ingestion_timestamp": ["2026-01-15T10:35:00Z"],
    })


@pytest.fixture
def sample_invalid_records():
    """Fixture providing various invalid records."""
    return pd.DataFrame({
        "event_id": ["evt-001", None, "evt-003", "evt-004"],
        "customer_id": ["cust-123", "cust-456", None, "cust-789"],
        "event_timestamp": ["2026-01-15T10:30:00Z", "2026-01-16T10:30:00Z", "invalid", "2099-01-01T00:00:00Z"],
        "amount": [125.50, "not-a-number", 100.0, 2000000.0],
        "currency": ["USD", "INVALID", "EUR", "USD"],
        "source_system": ["crm", "api", "crm", "invalid_system"],
        "ingestion_timestamp": ["2026-01-15T10:35:00Z", "2026-01-16T10:35:00Z", "2026-01-17T10:35:00Z", "2026-01-18T10:35:00Z"],
    })


class TestRequiredFieldsValidation:
    """Tests for required fields validation."""

    def test_all_required_fields_present(self, sample_valid_record):
        """Test that records with all required fields pass validation."""
        valid, invalid = validate_required_fields(sample_valid_record)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_missing_required_field(self, sample_invalid_records):
        """Test that records with missing required fields are invalid."""
        # Record with NULL event_id should fail
        valid, invalid = validate_required_fields(sample_invalid_records)
        assert len(valid) < len(sample_invalid_records)
        assert len(invalid) > 0

    def test_null_values_detected(self, sample_invalid_records):
        """Test that NULL values in required fields are detected."""
        valid, invalid = validate_required_fields(sample_invalid_records)
        # Rows 1 and 2 have NULLs in event_id and customer_id
        assert len(invalid) >= 2


class TestDataTypesValidation:
    """Tests for data type validation."""

    def test_valid_numeric_amount(self, sample_valid_record):
        """Test that valid numeric amounts pass."""
        valid, invalid = validate_data_types(sample_valid_record)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_invalid_amount_type(self, sample_invalid_records):
        """Test that non-numeric amounts are detected."""
        valid, invalid = validate_data_types(sample_invalid_records)
        # Row with "not-a-number" should be invalid
        assert len(invalid) > 0

    def test_empty_event_id_detected(self):
        """Test that empty event_id is detected."""
        df = pd.DataFrame({
            "event_id": ["", "evt-002"],
            "customer_id": ["cust-1", "cust-2"],
            "event_timestamp": ["2026-01-15T10:30:00Z", "2026-01-15T10:30:00Z"],
            "amount": [100.0, 200.0],
        })
        valid, invalid = validate_data_types(df)
        assert len(invalid) >= 1


class TestAcceptedValuesValidation:
    """Tests for accepted values validation."""

    def test_valid_currency(self, sample_valid_record):
        """Test that accepted currency values pass."""
        valid, invalid = validate_accepted_values(sample_valid_record)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_invalid_currency(self):
        """Test that invalid currency is rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "amount": [100.0],
            "currency": ["XYZ"],  # Invalid currency
            "source_system": ["crm"],
        })
        valid, invalid = validate_accepted_values(df)
        assert len(invalid) == 1
        assert len(valid) == 0

    def test_invalid_source_system(self):
        """Test that invalid source_system is rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "amount": [100.0],
            "currency": ["USD"],
            "source_system": ["invalid_system"],  # Invalid source
        })
        valid, invalid = validate_accepted_values(df)
        assert len(invalid) == 1


class TestTimestampValidation:
    """Tests for timestamp validation."""

    def test_valid_timestamp(self, sample_valid_record):
        """Test that valid timestamps pass."""
        valid, invalid = validate_timestamps(sample_valid_record)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp format is rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "event_timestamp": ["not-a-timestamp"],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z"],
        })
        valid, invalid = validate_timestamps(df)
        assert len(invalid) >= 1

    def test_future_timestamp_rejected(self):
        """Test that future timestamps are rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "event_timestamp": ["2099-01-01T00:00:00Z"],  # Future date
            "ingestion_timestamp": ["2026-01-15T10:35:00Z"],
        })
        valid, invalid = validate_timestamps(df)
        assert len(invalid) >= 1


class TestAmountRangeValidation:
    """Tests for amount range validation."""

    def test_valid_amount_range(self, sample_valid_record):
        """Test that amounts within valid range pass."""
        valid, invalid = validate_amount_range(sample_valid_record)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_amount_exceeds_max(self):
        """Test that amounts exceeding max are rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "amount": [2000000.0],  # Exceeds MAX_AMOUNT
        })
        valid, invalid = validate_amount_range(df)
        assert len(invalid) == 1

    def test_negative_amount(self):
        """Test that negative amounts are rejected."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "amount": [-50.0],  # Negative amount
        })
        valid, invalid = validate_amount_range(df)
        assert len(invalid) == 1


class TestMultipleValidationErrors:
    """Tests for records with multiple validation errors."""

    def test_record_with_multiple_errors(self):
        """Test that records with multiple errors are caught."""
        df = pd.DataFrame({
            "event_id": [None],  # Missing required field
            "customer_id": ["cust-123"],
            "amount": ["invalid"],  # Invalid type
            "currency": ["XYZ"],  # Invalid value
            "event_timestamp": ["invalid"],  # Invalid timestamp
        })
        # After first validation, record should be invalid
        valid, invalid = validate_required_fields(df)
        assert len(invalid) == 1
