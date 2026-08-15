"""
Data writer module.

Handles writing curated datasets and quarantine data to disk.
Creates output directories automatically.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src import config
from src.utils import logger


def ensure_output_directory(output_path: Path) -> None:
    """
    Ensure output directory exists, creating it if necessary.

    Args:
        output_path: Path to output file.
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Output directory ready: {output_dir}")


def write_curated_dataset(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Write curated (valid) dataset to Parquet file.

    Args:
        df: DataFrame containing valid, transformed data.
        output_path: Path to output file. If None, uses config.CURATED_OUTPUT_PATH.

    Returns:
        Path to written file.

    Raises:
        IOError: If write fails.
    """
    if output_path is None:
        output_path = config.CURATED_OUTPUT_PATH

    output_path = Path(output_path)

    # Ensure output directory exists
    ensure_output_directory(output_path)

    logger.info(f"Writing curated dataset: {output_path}")
    logger.info(f"Records: {len(df)}, Columns: {len(df.columns)}")

    try:
        # Write as Parquet for compression and schema preservation
        df.to_parquet(output_path, index=False, compression="snappy")
        logger.info(f"Successfully wrote {len(df)} records to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write curated dataset: {e}")
        raise


def write_quarantine_dataset(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Write invalid records to quarantine for inspection and diagnosis.

    Args:
        df: DataFrame containing invalid records with validation errors.
        output_path: Path to output file. If None, uses config.QUARANTINE_OUTPUT_PATH.

    Returns:
        Path to written file, or None if no invalid records.

    Raises:
        IOError: If write fails.
    """
    if len(df) == 0:
        logger.info("No invalid records to quarantine")
        return None

    if output_path is None:
        output_path = config.QUARANTINE_OUTPUT_PATH

    output_path = Path(output_path)

    # Ensure output directory exists
    ensure_output_directory(output_path)

    logger.info(f"Writing quarantine dataset: {output_path}")
    logger.info(f"Records: {len(df)}, Columns: {len(df.columns)}")

    try:
        # Write as Parquet for compression and schema preservation
        df.to_parquet(output_path, index=False, compression="snappy")
        logger.info(f"Successfully wrote {len(df)} invalid records to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write quarantine dataset: {e}")
        raise


def write_pipeline_metadata(
    metrics: dict,
    output_dir: Optional[Path] = None
) -> None:
    """
    Write pipeline execution metadata to file for audit trail.

    TODO: Implement metadata logging (execution time, record counts, errors, etc.)

    Args:
        metrics: Dictionary of pipeline execution metrics.
        output_dir: Directory for metadata files. If None, uses config.DATA_DIR.
    """
    if output_dir is None:
        output_dir = config.DATA_DIR

    logger.info(f"Pipeline metadata: {metrics}")

    # TODO: Write metrics to JSON/CSV for audit trail
    # File path: {output_dir}/pipeline_metadata_{timestamp}.json
