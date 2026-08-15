"""
Main entry point for the data pipeline.

Orchestrates the complete data transformation workflow:
1. Read input data from file
2. Validate data quality
3. Transform and standardize
4. Write curated and quarantine outputs
5. Log execution summary
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

from src import config
from src.reader import read_input_file, validate_dataframe_structure
from src.validator import run_all_validations
from src.transformer import transform_pipeline
from src.writer import write_curated_dataset, write_quarantine_dataset, write_pipeline_metadata
from src.utils import logger, log_execution_summary


def main(input_file: Path = None, input_format: str = "csv") -> int:
    """
    Execute the data pipeline.

    Args:
        input_file: Path to input file. If None, uses config.INPUT_FILE_PATH.
        input_format: Input file format ("csv" or "json").

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Data Pipeline Started")
    logger.info("=" * 60)

    try:
        # ============================================================
        # Step 1: Read Input Data
        # ============================================================
        logger.info("\n[STEP 1] Reading input data...")
        try:
            df_raw = read_input_file(file_path=input_file, file_format=input_format)
        except FileNotFoundError as e:
            logger.error(f"Input file not found: {e}")
            return 1
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return 1

        # Validate DataFrame structure
        is_valid, error_msg = validate_dataframe_structure(df_raw, config.REQUIRED_COLUMNS)
        if not is_valid:
            logger.error(f"DataFrame structure invalid: {error_msg}")
            return 1

        initial_row_count = len(df_raw)

        # ============================================================
        # Step 2: Validate Data Quality
        # ============================================================
        logger.info("\n[STEP 2] Running validation checks...")
        df_valid, df_invalid = run_all_validations(df_raw)

        valid_row_count = len(df_valid)
        invalid_row_count = len(df_invalid)

        logger.info(f"Validation Results:")
        logger.info(f"  - Valid records: {valid_row_count}")
        logger.info(f"  - Invalid records: {invalid_row_count}")

        # ============================================================
        # Step 3: Transform Valid Data
        # ============================================================
        logger.info("\n[STEP 3] Transforming valid data...")
        if len(df_valid) > 0:
            df_transformed, transform_metrics = transform_pipeline(df_valid)
            logger.info(f"Transformation Results:")
            logger.info(f"  - Output records: {transform_metrics['output_count']}")
            logger.info(f"  - Duplicates removed: {transform_metrics['duplicate_count']}")
        else:
            logger.warning("No valid records to transform")
            df_transformed = df_valid
            transform_metrics = {
                "input_count": 0,
                "output_count": 0,
                "duplicate_count": 0,
            }

        # ============================================================
        # Step 4: Write Outputs
        # ============================================================
        logger.info("\n[STEP 4] Writing output datasets...")

        # Write curated (valid) dataset
        curated_path = None
        if len(df_transformed) > 0:
            try:
                curated_path = write_curated_dataset(df_transformed)
            except IOError as e:
                logger.error(f"Failed to write curated dataset: {e}")
                return 1

        # Write quarantine (invalid) dataset
        quarantine_path = None
        if len(df_invalid) > 0:
            try:
                quarantine_path = write_quarantine_dataset(df_invalid)
            except IOError as e:
                logger.error(f"Failed to write quarantine dataset: {e}")
                return 1

        # ============================================================
        # Step 5: Execution Summary
        # ============================================================
        logger.info("\n[STEP 5] Pipeline execution summary...")

        execution_time = time.time() - start_time

        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_file": str(input_file or config.INPUT_FILE_PATH),
            "input_rows": initial_row_count,
            "valid_rows": valid_row_count,
            "invalid_rows": invalid_row_count,
            "output_rows": len(df_transformed),
            "duplicates_removed": transform_metrics.get("duplicate_count", 0),
            "curated_output": str(curated_path) if curated_path else "None",
            "quarantine_output": str(quarantine_path) if quarantine_path else "None",
            "execution_time_seconds": round(execution_time, 2),
            "status": "SUCCESS",
        }

        log_execution_summary(metrics)

        # Write metadata for audit trail
        try:
            write_pipeline_metadata(metrics)
        except Exception as e:
            logger.warning(f"Failed to write pipeline metadata: {e}")

        logger.info("=" * 60)
        logger.info("Data Pipeline Completed Successfully")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        logger.error("=" * 60)
        logger.error("Data Pipeline Failed")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    # Parse command-line arguments (optional)
    input_file = None
    input_format = "csv"

    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])

    if len(sys.argv) > 2:
        input_format = sys.argv[2]

    exit_code = main(input_file=input_file, input_format=input_format)
    sys.exit(exit_code)
