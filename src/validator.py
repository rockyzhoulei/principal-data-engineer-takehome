"""
Data validation module.

Handles validation of required fields, data types, accepted values, and timestamp formats.
Returns valid and invalid records separately for processing and quarantine.
"""

from typing import Optional
import pandas as pd

from src import config
from src.utils import logger, validate_timestamp


def validate_required_fields(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate that all required fields are present and non-null.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df) with validation errors in invalid_df.
    """
    logger.info(f"Validating required fields: {config.REQUIRED_COLUMNS}")

    # Create a copy to avoid modifying original
    df = df.copy()
    df["_validation_errors"] = ""

    # Check for missing required columns
    missing_cols = config.REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        # All rows are invalid if columns missing
        return pd.DataFrame(), df

    # Check for null values in required fields
    for col in config.REQUIRED_COLUMNS:
        null_mask = df[col].isna() | (df[col] == "")
        df.loc[null_mask, "_validation_errors"] += f"NULL_{col}; "

    # Split valid and invalid
    valid_df = df[df["_validation_errors"] == ""].drop(columns=["_validation_errors"])
    invalid_df = df[df["_validation_errors"] != ""]

    logger.info(f"Required fields validation: {len(valid_df)} valid, {len(invalid_df)} invalid")

    return valid_df, invalid_df


def validate_data_types(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate that data types match expected schema.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df).
    """
    logger.info("Validating data types")

    df = df.copy()
    df["_validation_errors"] = ""

    # Validate amount is numeric
    if "amount" in df.columns:
        try:
            # Attempt to convert to float
            amount_numeric = pd.to_numeric(df["amount"], errors="coerce")
            invalid_amount = amount_numeric.isna() & df["amount"].notna()
            df.loc[invalid_amount, "_validation_errors"] += "INVALID_AMOUNT_TYPE; "
        except Exception as e:
            logger.warning(f"Error validating amount type: {e}")

    # Validate event_id is non-empty string
    if "event_id" in df.columns:
        invalid_event_id = (df["event_id"].astype(str).str.strip() == "") | df["event_id"].isna()
        df.loc[invalid_event_id, "_validation_errors"] += "INVALID_EVENT_ID; "

    # Validate customer_id is non-empty string
    if "customer_id" in df.columns:
        invalid_customer_id = (df["customer_id"].astype(str).str.strip() == "") | df["customer_id"].isna()
        df.loc[invalid_customer_id, "_validation_errors"] += "INVALID_CUSTOMER_ID; "

    valid_df = df[df["_validation_errors"] == ""].drop(columns=["_validation_errors"])
    invalid_df = df[df["_validation_errors"] != ""]

    logger.info(f"Data type validation: {len(valid_df)} valid, {len(invalid_df)} invalid")

    return valid_df, invalid_df


def validate_accepted_values(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate that categorical columns contain accepted values.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df).
    """
    logger.info("Validating accepted values")

    df = df.copy()
    df["_validation_errors"] = ""

    # Validate currency
    if "currency" in df.columns:
        invalid_currency = df["currency"].notna() & ~df["currency"].isin(config.ACCEPTED_CURRENCIES)
        df.loc[invalid_currency, "_validation_errors"] += "INVALID_CURRENCY; "

    # Validate source_system
    if "source_system" in df.columns:
        invalid_source = df["source_system"].notna() & ~df["source_system"].isin(config.ACCEPTED_SOURCE_SYSTEMS)
        df.loc[invalid_source, "_validation_errors"] += "INVALID_SOURCE_SYSTEM; "

    valid_df = df[df["_validation_errors"] == ""].drop(columns=["_validation_errors"])
    invalid_df = df[df["_validation_errors"] != ""]

    logger.info(f"Accepted values validation: {len(valid_df)} valid, {len(invalid_df)} invalid")

    return valid_df, invalid_df


def validate_timestamps(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate timestamp fields for correct format and reasonable values.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df).
    """
    logger.info("Validating timestamps")

    df = df.copy()
    df["_validation_errors"] = ""

    # Validate event_timestamp
    if "event_timestamp" in df.columns:
        for idx, row in df.iterrows():
            if pd.notna(row["event_timestamp"]):
                is_valid, error_msg = validate_timestamp(str(row["event_timestamp"]))
                if not is_valid:
                    df.at[idx, "_validation_errors"] += f"INVALID_EVENT_TIMESTAMP: {error_msg}; "

    # Validate ingestion_timestamp
    if "ingestion_timestamp" in df.columns:
        for idx, row in df.iterrows():
            if pd.notna(row["ingestion_timestamp"]):
                is_valid, error_msg = validate_timestamp(str(row["ingestion_timestamp"]))
                if not is_valid:
                    df.at[idx, "_validation_errors"] += f"INVALID_INGESTION_TIMESTAMP: {error_msg}; "

    valid_df = df[df["_validation_errors"] == ""].drop(columns=["_validation_errors"])
    invalid_df = df[df["_validation_errors"] != ""]

    logger.info(f"Timestamp validation: {len(valid_df)} valid, {len(invalid_df)} invalid")

    return valid_df, invalid_df


def validate_amount_range(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate that amounts fall within acceptable range.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df).
    """
    logger.info(f"Validating amount range: {config.MIN_AMOUNT} to {config.MAX_AMOUNT}")

    df = df.copy()
    df["_validation_errors"] = ""

    if "amount" in df.columns:
        try:
            amounts = pd.to_numeric(df["amount"], errors="coerce")
            
            # Check range
            out_of_range = (amounts < config.MIN_AMOUNT) | (amounts > config.MAX_AMOUNT)
            df.loc[out_of_range, "_validation_errors"] += f"AMOUNT_OUT_OF_RANGE; "
        except Exception as e:
            logger.warning(f"Error validating amount range: {e}")

    valid_df = df[df["_validation_errors"] == ""].drop(columns=["_validation_errors"])
    invalid_df = df[df["_validation_errors"] != ""]

    logger.info(f"Amount range validation: {len(valid_df)} valid, {len(invalid_df)} invalid")

    return valid_df, invalid_df


def run_all_validations(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run all validation checks and return valid and invalid records.

    Validation order:
    1. Required fields
    2. Data types
    3. Accepted values
    4. Timestamps
    5. Amount range

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (valid_df, invalid_df) after all validation passes.
    """
    logger.info(f"Starting validation pipeline with {len(df)} input records")

    # Apply validations sequentially, keeping track of invalid records
    all_invalid = pd.DataFrame()

    # Step 1: Required fields
    df, invalid = validate_required_fields(df)
    all_invalid = pd.concat([all_invalid, invalid], ignore_index=True)

    # Step 2: Data types
    df, invalid = validate_data_types(df)
    all_invalid = pd.concat([all_invalid, invalid], ignore_index=True)

    # Step 3: Accepted values
    df, invalid = validate_accepted_values(df)
    all_invalid = pd.concat([all_invalid, invalid], ignore_index=True)

    # Step 4: Timestamps
    df, invalid = validate_timestamps(df)
    all_invalid = pd.concat([all_invalid, invalid], ignore_index=True)

    # Step 5: Amount range
    df, invalid = validate_amount_range(df)
    all_invalid = pd.concat([all_invalid, invalid], ignore_index=True)

    # Remove duplicates from invalid records (same record may fail multiple checks)
    if len(all_invalid) > 0:
        all_invalid = all_invalid.drop_duplicates(subset=config.REQUIRED_COLUMNS, keep="first")

    logger.info(f"Validation complete: {len(df)} valid, {len(all_invalid)} invalid")

    return df, all_invalid
