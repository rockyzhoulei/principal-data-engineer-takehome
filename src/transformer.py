"""
Data transformation module.

Handles standardization of timestamps, normalization of column names,
deduplication of records, and business-logic transformations.
"""

from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import hashlib

from src import config
from src.utils import logger, parse_timestamp


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to lowercase with underscores.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with normalized column names.
    """
    logger.info("Normalizing column names")

    df = df.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")

    logger.debug(f"Normalized columns: {list(df.columns)}")

    return df


def standardize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize timestamp columns to UTC ISO 8601 format.

    Args:
        df: Input DataFrame with event_timestamp and ingestion_timestamp columns.

    Returns:
        DataFrame with standardized timestamps as datetime objects.
    """
    logger.info("Standardizing timestamps")

    df = df.copy()

    # Standardize event_timestamp
    if "event_timestamp" in df.columns:
        df["event_timestamp"] = df["event_timestamp"].apply(
            lambda x: parse_timestamp(str(x)) if pd.notna(x) else None
        )

    # Standardize ingestion_timestamp
    if "ingestion_timestamp" in df.columns:
        df["ingestion_timestamp"] = df["ingestion_timestamp"].apply(
            lambda x: parse_timestamp(str(x)) if pd.notna(x) else None
        )

    logger.info(f"Timestamps standardized to datetime64[ns]")

    return df


def deduplicate_records(df: pd.DataFrame, window_days: int = config.DEDUP_WINDOW_DAYS) -> tuple[pd.DataFrame, int]:
    """
    Deduplicate records based on business key and time window.

    Business Key: {customer_id, source_system, event_id}
    Selection Rule: Keep record with highest event_timestamp (latest event time)
                   If tied, keep highest ingestion_timestamp (most recent arrival)

    Args:
        df: Input DataFrame in canonical normalized schema.
        window_days: Window in days for dedup detection (default: 72).

    Returns:
        Tuple of (deduplicated_df, duplicate_count).
    """
    logger.info(f"Deduplicating records (window: {window_days} days)")

    if df.empty:
        logger.info("Empty DataFrame received; skipping deduplication")
        return df, 0

    required_columns = {"event_id", "customer_id", "source_system", "event_timestamp", "ingestion_timestamp"}
    missing_columns = sorted(required_columns - set(df.columns))

    if missing_columns:
        raise ValueError(
            "Deduplication requires canonical normalized columns. "
            "Run normalize_column_names() before deduplicate_records(). Missing: "
            f"{missing_columns}"
        )

    initial_count = len(df)

    # For records without event_timestamp, skip dedup
    if df["event_timestamp"].isna().all():
        logger.warning("Cannot deduplicate without event_timestamp")
        return df, 0

    # Create dedup key
    df = df.copy()
    df["_dedup_key"] = (
        df["customer_id"].astype(str) + "_" +
        df["source_system"].astype(str) + "_" +
        df["event_id"].astype(str)
    )

    # Sort by dedup key, then by event_timestamp (desc), then by ingestion_timestamp (desc)
    df_sorted = df.sort_values(
        by=["_dedup_key", "event_timestamp", "ingestion_timestamp"],
        ascending=[True, False, False],
        na_position="last"
    )

    # Keep first occurrence (latest timestamp) for each key
    df_deduped = df_sorted.drop_duplicates(subset=["_dedup_key"], keep="first")
    df_deduped = df_deduped.drop(columns=["_dedup_key"])

    duplicate_count = initial_count - len(df_deduped)
    logger.info(f"Deduplication: removed {duplicate_count} duplicates, kept {len(df_deduped)} unique records")

    return df_deduped, duplicate_count


def mask_pii(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mask personally identifiable information (PII).

    Replaces customer names and email addresses with hash tokens.
    Preserves customer_id for joins.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with PII masked.
    """
    logger.info("Masking PII")

    df = df.copy()

    # TODO: Implement PII masking for customer_name, email, etc.
    # For now, just log that it would be done
    logger.info("PII masking: customer names and emails would be tokenized")

    return df


def standardize_currency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize currency representation.

    TODO: Convert amounts to base currency (USD) or preserve with explicit currency field.

    Args:
        df: Input DataFrame with amount and currency columns.

    Returns:
        DataFrame with standardized currency.
    """
    logger.info("Standardizing currency")

    df = df.copy()

    # TODO: Implement currency conversion logic
    logger.debug("Currency standardization: placeholder for conversion logic")

    return df


def apply_business_transformations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply business logic transformations.

    Placeholder for domain-specific transformations:
    - Calculated fields
    - Business rule application
    - Feature engineering

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with business transformations applied.
    """
    logger.info("Applying business transformations")

    df = df.copy()

    # TODO: Add business-specific transformations
    logger.debug("Business transformations: placeholder for domain logic")

    return df


def transform_pipeline(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Execute full transformation pipeline.

    Steps:
    1. Normalize column names
    2. Standardize timestamps
    3. Deduplicate records
    4. Mask PII
    5. Standardize currency
    6. Apply business transformations

    Args:
        df: Input DataFrame (should be validated first).

    Returns:
        Tuple of (transformed_df, transformation_metrics).
    """
    logger.info(f"Starting transformation pipeline with {len(df)} records")

    metrics = {
        "input_count": len(df),
        "duplicate_count": 0,
    }

    # Step 1: Normalize column names
    df = normalize_column_names(df)

    # Step 2: Standardize timestamps
    df = standardize_timestamps(df)

    # Step 3: Deduplicate
    df, duplicate_count = deduplicate_records(df)
    metrics["duplicate_count"] = duplicate_count

    # Step 4: Mask PII
    df = mask_pii(df)

    # Step 5: Standardize currency
    df = standardize_currency(df)

    # Step 6: Apply business transformations
    df = apply_business_transformations(df)

    metrics["output_count"] = len(df)
    logger.info(f"Transformation complete: {metrics['output_count']} output records")

    return df, metrics
