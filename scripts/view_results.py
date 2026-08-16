"""Demonstration utility for technical walkthroughs only.

This script is intended for live architecture reviews and demo sessions.
It reads the generated Parquet outputs and prints a polished summary without
modifying any production code under src/.
"""

from pathlib import Path
from typing import Optional

import pandas as pd


CURATED_PATH = Path("data/curated/events_curated.parquet")
QUARANTINE_PATH = Path("data/quarantine/events_invalid.parquet")
RAW_PATH = Path("data/raw/events.csv")


def load_parquet(path: Path) -> Optional[pd.DataFrame]:
    """Load a parquet file if it exists; otherwise return None."""
    if not path.exists():
        print(f"{path.name} not found.")
        return None

    try:
        return pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - demo utility only
        print(f"Unable to read {path}: {exc}")
        return None


def format_section(title: str, width: int = 60) -> str:
    """Return a simple section header line."""
    return f"{title}\n{'=' * width}"


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print(title)
    print("=" * 60)


def print_summary(curated: Optional[pd.DataFrame], quarantine: Optional[pd.DataFrame]) -> None:
    """Print summary metrics for the pipeline outputs."""
    print_section_header("SECTION 1")
    print("Pipeline Output Summary")
    print()

    raw_rows = 0
    if RAW_PATH.exists():
        try:
            raw_rows = len(pd.read_csv(RAW_PATH))
        except Exception:
            raw_rows = 0

    curated_rows = len(curated) if curated is not None else 0
    quarantine_rows = len(quarantine) if quarantine is not None else 0
    valid_before_dedup = max(raw_rows - quarantine_rows, 0)
    duplicates_removed = max(valid_before_dedup - curated_rows, 0)

    validation_pass_rate = (valid_before_dedup / raw_rows * 100) if raw_rows else 0.0
    curated_rate = (curated_rows / raw_rows * 100) if raw_rows else 0.0
    quarantine_rate = (quarantine_rows / raw_rows * 100) if raw_rows else 0.0

    print(f"Input Records        : {raw_rows}")
    print(f"Valid Before Dedup   : {valid_before_dedup}")
    print(f"Quarantine Records   : {quarantine_rows}")
    print(f"Duplicates Removed   : {duplicates_removed}")
    print(f"Curated Records      : {curated_rows}")
    print(f"Validation Pass Rate : {validation_pass_rate:.1f}%")
    print(f"Curated Rate         : {curated_rate:.1f}%")
    print(f"Quarantine Rate      : {quarantine_rate:.1f}%")


def print_dataframe_preview(title: str, df: Optional[pd.DataFrame], label: str) -> None:
    """Print a preview of a DataFrame with columns and shape."""
    print_section_header(title)
    print(label)

    if df is None:
        print("No dataset available.")
        return

    print()
    print(df.head(10).to_string(index=False))
    print()
    print(f"Columns: {list(df.columns)}")
    print(f"Shape: {df.shape}")


def print_validation_error_summary(quarantine: Optional[pd.DataFrame]) -> None:
    """Print the distributed validation error reasons from the quarantine dataset."""
    print_section_header("SECTION 4")
    print("Validation Error Summary")
    print()

    if quarantine is None:
        print("Quarantine dataset not available.")
        return

    error_column = None
    for candidate in ("error_reason", "validation_error", "_validation_errors"):
        if candidate in quarantine.columns:
            error_column = candidate
            break

    if error_column is None:
        print("No validation error column found in quarantine data.")
        return

    error_series = quarantine[error_column].fillna("").astype(str)
    value_counts = error_series[error_series.str.strip() != ""].str.upper().str.split(";").explode()
    value_counts = value_counts.str.strip()
    value_counts = value_counts[value_counts != ""]

    if value_counts.empty:
        print("No validation errors recorded.")
        return

    summary = value_counts.value_counts().sort_values(ascending=False)
    for label, count in summary.items():
        print(f"{label:<25} {count}")


def print_quality_metrics(curated: Optional[pd.DataFrame], quarantine: Optional[pd.DataFrame]) -> None:
    """Print the key quality metrics from the pipeline outputs."""
    print_section_header("SECTION 5")
    print("Data Quality Metrics")
    print()

    raw_rows = 0
    if RAW_PATH.exists():
        try:
            raw_rows = len(pd.read_csv(RAW_PATH))
        except Exception:
            raw_rows = 0

    curated_rows = len(curated) if curated is not None else 0
    quarantine_rows = len(quarantine) if quarantine is not None else 0
    valid_before_dedup = max(raw_rows - quarantine_rows, 0)
    duplicate_removal = max(valid_before_dedup - curated_rows, 0)

    curated_percent = (curated_rows / raw_rows * 100) if raw_rows else 0.0
    quarantine_percent = (quarantine_rows / raw_rows * 100) if raw_rows else 0.0

    print(f"Duplicate Removal Count: {duplicate_removal}")
    print(f"Curated Percentage     : {curated_percent:.1f}%")
    print(f"Quarantine Percentage  : {quarantine_percent:.1f}%")


def print_output_locations() -> None:
    """Print the absolute paths of the pipeline outputs."""
    print_section_header("SECTION 6")
    print("Output Locations")
    print()
    print(f"Curated dataset: {str(CURATED_PATH.resolve())}")
    print(f"Quarantine dataset: {str(QUARANTINE_PATH.resolve())}")


def main() -> None:
    """Run the demonstration report for the generated parquet outputs."""
    print("=" * 60)
    print("PRODUCTION DATA PIPELINE DEMONSTRATION")
    print("=" * 60)

    curated = load_parquet(CURATED_PATH)
    quarantine = load_parquet(QUARANTINE_PATH)

    print_summary(curated, quarantine)
    print_dataframe_preview("SECTION 2", curated, "Curated Dataset Preview")
    print_dataframe_preview("SECTION 3", quarantine, "Quarantine Dataset Preview")
    print_validation_error_summary(quarantine)
    print_quality_metrics(curated, quarantine)
    print_output_locations()


if __name__ == "__main__":
    main()
