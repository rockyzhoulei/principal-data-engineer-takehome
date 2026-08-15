"""
Data reader module.

Handles reading input data from various file formats (CSV, JSON).
Validates file existence and readability.
"""

import pandas as pd
from pathlib import Path
from typing import Optional

from src import config
from src.utils import logger


def read_input_file(
    file_path: Optional[Path] = None,
    file_format: str = "csv"
) -> pd.DataFrame:
    """
    Read input data file into a pandas DataFrame.

    Args:
        file_path: Path to input file. If None, uses config.INPUT_FILE_PATH.
        file_format: File format ("csv" or "json").

    Returns:
        pandas.DataFrame containing the input data.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is unsupported.
        pd.errors.ParserError: If file cannot be parsed.
    """
    if file_path is None:
        file_path = config.INPUT_FILE_PATH

    file_path = Path(file_path)

    # Validate file existence
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Path is not a file: {file_path}")

    logger.info(f"Reading input file: {file_path}")

    try:
        if file_format.lower() == "csv":
            df = pd.read_csv(file_path)
        elif file_format.lower() == "json":
            df = pd.read_json(file_path, orient="records")
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        logger.info(f"Successfully read {len(df)} rows from {file_path}")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise


def validate_dataframe_structure(df: pd.DataFrame, required_columns: set[str]) -> tuple[bool, Optional[str]]:
    """
    Validate that DataFrame has required columns.

    Args:
        df: DataFrame to validate.
        required_columns: Set of column names that must be present.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if df is None or len(df) == 0:
        return False, "DataFrame is empty or None"

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"

    return True, None
