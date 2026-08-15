"""
Unit tests for the transformer module.

Tests transformation functions for normalization, standardization,
deduplication, and business logic transformations.
"""

from pathlib import Path

import pytest
import pandas as pd
from datetime import datetime

from src.main import main
from src.transformer import (
    normalize_column_names,
    standardize_timestamps,
    deduplicate_records,
    mask_pii,
    transform_pipeline,
)


@pytest.fixture
def sample_raw_data():
    """Fixture providing sample raw data."""
    return pd.DataFrame({
        "Event ID": ["evt-001", "evt-002", "evt-001"],  # Duplicate
        "Customer ID": ["cust-123", "cust-456", "cust-123"],
        "Event Timestamp": ["2026-01-15T10:30:00Z", "2026-01-16T11:00:00Z", "2026-01-15T10:30:00Z"],
        "Amount": [100.0, 200.0, 100.0],
        "Currency": ["USD", "EUR", "USD"],
        "Source System": ["crm", "api", "crm"],
        "Ingestion Timestamp": ["2026-01-15T10:35:00Z", "2026-01-16T11:05:00Z", "2026-01-15T10:40:00Z"],
    })


class TestNormalizeColumnNames:
    """Tests for column name normalization."""

    def test_lowercase_conversion(self):
        """Test that column names are converted to lowercase."""
        df = pd.DataFrame({
            "Event ID": [1],
            "Customer ID": [2],
        })
        result = normalize_column_names(df)
        assert "event_id" in result.columns.str.lower()
        assert "customer_id" in result.columns.str.lower()

    def test_space_to_underscore(self):
        """Test that spaces are replaced with underscores."""
        df = pd.DataFrame({
            "Event ID": [1],
            "Customer ID": [2],
        })
        result = normalize_column_names(df)
        assert "event_id" in result.columns
        assert "customer_id" in result.columns

    def test_hyphen_to_underscore(self):
        """Test that hyphens are replaced with underscores."""
        df = pd.DataFrame({
            "event-id": [1],
            "customer-id": [2],
        })
        result = normalize_column_names(df)
        assert "event_id" in result.columns
        assert "customer_id" in result.columns

    def test_normalization_preserves_data(self, sample_raw_data):
        """Test that normalization doesn't alter data values."""
        original_data = sample_raw_data.copy()
        result = normalize_column_names(sample_raw_data)
        
        # Data values should be unchanged
        assert len(result) == len(original_data)
        assert result.iloc[0, 2] == original_data.iloc[0, 2]  # Check first row, third column


class TestStandardizeTimestamps:
    """Tests for timestamp standardization."""

    def test_valid_iso_8601_timestamp(self):
        """Test that valid ISO 8601 timestamps are parsed correctly."""
        df = pd.DataFrame({
            "event_timestamp": ["2026-01-15T10:30:00Z"],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z"],
        })
        result = standardize_timestamps(df)
        
        assert pd.api.types.is_datetime64_any_dtype(result["event_timestamp"])
        assert result["event_timestamp"].iloc[0].year == 2026

    def test_various_timestamp_formats(self):
        """Test that various timestamp formats are handled."""
        df = pd.DataFrame({
            "event_timestamp": ["2026-01-15T10:30:00Z", "2026-01-16 11:00:00", "2026-01-17"],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z", "2026-01-16 11:05:00", "2026-01-17"],
        })
        result = standardize_timestamps(df)
        
        # All should be datetime
        assert pd.api.types.is_datetime64_any_dtype(result["event_timestamp"])

    def test_null_timestamps_preserved(self):
        """Test that NULL timestamps are preserved as NaT."""
        df = pd.DataFrame({
            "event_timestamp": ["2026-01-15T10:30:00Z", None],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z", None],
        })
        result = standardize_timestamps(df)
        
        assert pd.isna(result["event_timestamp"].iloc[1])


class TestDeduplicateRecords:
    """Tests for record deduplication."""

    def test_duplicate_detection(self, sample_raw_data):
        """Test that duplicates are detected on normalized canonical columns."""
        df = normalize_column_names(sample_raw_data)
        result, dup_count = deduplicate_records(df)

        # sample_raw_data has 3 rows, 1 duplicate -> 2 unique
        assert len(result) == 2
        assert dup_count == 1

    def test_keeps_latest_timestamp(self, sample_raw_data):
        """Test that when duplicates exist, latest timestamp is kept."""
        # Normalize first to ensure timestamp parsing
        df = normalize_column_names(sample_raw_data)
        df = standardize_timestamps(df)
        
        result, _ = deduplicate_records(df)
        
        # For the duplicate evt-001, should keep the one with latest ingestion_timestamp
        evt_001_records = result[result["event_id"] == "evt-001"]
        assert len(evt_001_records) == 1

    def test_no_duplicates(self):
        """Test that unique records pass through unchanged."""
        df = pd.DataFrame({
            "customer_id": ["cust-1", "cust-2"],
            "event_id": ["evt-1", "evt-2"],
            "source_system": ["crm", "api"],
            "event_timestamp": ["2026-01-15T10:30:00Z", "2026-01-16T11:00:00Z"],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z", "2026-01-16T11:05:00Z"],
        })
        result, dup_count = deduplicate_records(df)
        
        assert len(result) == 2
        assert dup_count == 0


class TestMaskPII:
    """Tests for PII masking."""

    def test_pii_masking_placeholder(self, sample_raw_data):
        """Test that PII masking function runs (placeholder implementation)."""
        result = mask_pii(sample_raw_data)
        
        # Should not raise exception
        assert len(result) == len(sample_raw_data)
        # TODO: Add assertions for actual PII masking when implemented


class TestTransformPipeline:
    """Tests for complete transformation pipeline."""

    def test_pipeline_execution(self, sample_raw_data):
        """Test that full transformation pipeline executes successfully."""
        result, metrics = transform_pipeline(sample_raw_data)
        
        # Should return transformed data and metrics
        assert len(result) > 0
        assert "input_count" in metrics
        assert "output_count" in metrics
        assert "duplicate_count" in metrics

    def test_pipeline_reduces_duplicates(self, sample_raw_data):
        """Test that pipeline reduces row count due to deduplication."""
        result, metrics = transform_pipeline(sample_raw_data)
        
        # Input has 3 rows, 1 duplicate -> output should be 2
        assert metrics["output_count"] < metrics["input_count"]
        assert metrics["duplicate_count"] == 1

    def test_pipeline_preserves_data_integrity(self, sample_raw_data):
        """Test that pipeline doesn't lose important data."""
        result, metrics = transform_pipeline(sample_raw_data)
        
        # At least some records should survive
        assert metrics["output_count"] > 0


class TestTransformationEdgeCases:
    """Tests for edge cases in transformation."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame({
            "event_id": [],
            "customer_id": [],
        })
        result, metrics = transform_pipeline(df)
        
        assert len(result) == 0
        assert metrics["output_count"] == 0

    def test_single_record(self):
        """Test handling of single record."""
        df = pd.DataFrame({
            "event_id": ["evt-001"],
            "customer_id": ["cust-123"],
            "event_timestamp": ["2026-01-15T10:30:00Z"],
            "ingestion_timestamp": ["2026-01-15T10:35:00Z"],
            "source_system": ["crm"],
        })
        result, metrics = transform_pipeline(df)
        
        assert len(result) == 1
        assert metrics["output_count"] == 1


class TestEndToEndPipeline:
    """Integration tests for the real sample dataset."""

    def test_sample_dataset_pipeline(self):
        """Run the real pipeline on the sample CSV and validate the resulting outputs."""
        repo_root = Path(__file__).resolve().parents[1]
        input_path = repo_root / "data" / "raw" / "events.csv"
        curated_path = repo_root / "data" / "curated" / "events_curated.parquet"
        quarantine_path = repo_root / "data" / "quarantine" / "events_invalid.parquet"

        raw_df = pd.read_csv(input_path)
        assert len(raw_df) == 14

        exit_code = main(input_file=input_path, input_format="csv")
        assert exit_code == 0

        curated_df = pd.read_parquet(curated_path)
        quarantine_df = pd.read_parquet(quarantine_path)

        assert len(raw_df) == 14
        assert len(raw_df) - len(quarantine_df) == 9
        assert len(quarantine_df) == 5
        assert len(curated_df) == 7
        assert len(raw_df) - len(curated_df) == 7

        assert quarantine_df["_validation_errors"].fillna("").astype(str).str.strip().ne("").all()

        curated_key = curated_df[["customer_id", "source_system", "event_id"]].copy()
        assert not curated_key.duplicated().any()
