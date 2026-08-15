# Python Implementation Guide

## Project Structure

```
src/
  ├── __init__.py          # Package initialization
  ├── config.py            # Configuration & constants (no hard-coded values)
  ├── models.py            # Schema definitions & type hints
  ├── utils.py             # Logging & helper functions
  ├── reader.py            # File I/O (CSV/JSON to DataFrame)
  ├── validator.py         # Data quality validation
  ├── transformer.py       # Data transformation & standardization
  ├── writer.py            # Output writing (Parquet)
  └── main.py              # Pipeline orchestration

tests/
  ├── __init__.py
  ├── test_validator.py    # Validation tests
  └── test_transformer.py  # Transformation tests

data/
  ├── raw/                 # Input data directory
  ├── curated/             # Curated output directory
  └── quarantine/          # Invalid records directory
```

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **reader.py:** Only handles file I/O and structure validation
- **validator.py:** Only handles data quality checks
- **transformer.py:** Only handles data transformations
- **writer.py:** Only handles output writing
- **config.py:** Centralized configuration (no magic values in code)
- **utils.py:** Shared utilities (logging, helpers)
- **main.py:** Orchestrates the pipeline

### 2. Type Hints
All functions include type hints for clarity and IDE support:
```python
def validate_required_fields(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns tuple of (valid_df, invalid_df)."""
    pass
```

### 3. Logging Instead of Print
All output uses the logging module for production-ready observability:
```python
logger.info(f"Processing {len(df)} records")
logger.error(f"Validation failed: {error_msg}")
```

### 4. Configuration Over Hard-Coding
All constants are defined in `config.py`:
- Required columns
- Accepted values
- Validation thresholds
- Output paths
- Timestamp formats

### 5. Independent Testability
Each function is designed to be tested independently:
- Pure functions where possible
- Explicit inputs and outputs
- No global state dependencies

### 6. Error Handling
- Validation failures route to quarantine (no data loss)
- Transient failures can be retried
- Comprehensive logging for diagnosis

## Module Descriptions

### config.py
**Purpose:** Centralize all configuration.

**Key Components:**
- Path definitions (Bronze/Silver/Gold directories)
- Required columns & field definitions
- Accepted values (currencies, source systems)
- Validation thresholds (amount range, dedup window)
- Logging configuration

**Why:** Enables easy parameter tuning and environment-specific configuration without code changes.

### models.py
**Purpose:** Define data schemas and type hints.

**Key Components:**
- `EventRecord`: TypedDict for raw event structure
- `ValidationResult`: Result of validation operation
- `PipelineMetrics`: Execution metrics
- `CURATED_SCHEMA` & `QUARANTINE_SCHEMA`: Output schemas

**Why:** Lightweight type definitions enable better IDE support and documentation without heavyweight OOP.

### utils.py
**Purpose:** Shared utilities and helpers.

**Key Functions:**
- `setup_logging()`: Configure logging
- `parse_timestamp()`: Parse multiple timestamp formats
- `validate_timestamp()`: Validate timestamp (format + not future)
- `is_valid_uuid_format()`: Validate UUID pattern
- `flatten_errors()`: Serialize errors to JSON
- `log_execution_summary()`: Log pipeline metrics

**Why:** Reduces code duplication and centralizes common operations.

### reader.py
**Purpose:** Read input data.

**Key Functions:**
- `read_input_file()`: Read CSV/JSON to DataFrame
- `validate_dataframe_structure()`: Check required columns

**Why:** Single responsibility - data I/O is isolated from transformation logic.

**Error Handling:**
- FileNotFoundError if file missing
- ValueError if format unsupported
- ParserError if file malformed

### validator.py
**Purpose:** Validate data quality.

**Validation Functions:**
1. `validate_required_fields()`: Check non-null required columns
2. `validate_data_types()`: Check field types (string, numeric)
3. `validate_accepted_values()`: Check categorical values
4. `validate_timestamps()`: Check format & not future-dated
5. `validate_amount_range()`: Check amount within bounds

**Key Design:**
- Each function returns `(valid_df, invalid_df)` tuple
- Invalid records include error details in `_validation_errors` column
- `run_all_validations()` chains all checks

**Why:** 
- Modular validation enables reuse and testing
- Invalid records captured for quarantine (no silent data loss)
- Error tracking enables diagnosis

### transformer.py
**Purpose:** Transform and standardize data.

**Transformation Functions:**
1. `normalize_column_names()`: Lowercase, underscores
2. `standardize_timestamps()`: Parse to UTC datetime
3. `deduplicate_records()`: Remove duplicates (business key + window)
4. `mask_pii()`: Tokenize customer names/emails
5. `standardize_currency()`: Normalize amounts
6. `apply_business_transformations()`: Domain logic

**Key Design:**
- `transform_pipeline()` orchestrates all transformations
- Returns (transformed_df, metrics)
- Metrics track duplicates removed, row counts

**Deduplication Logic:**
- Business key: `{customer_id, source_system, event_id}`
- Window: 72 hours (covers late arrivals)
- Keep: Record with latest `event_timestamp`, then latest `ingestion_timestamp`

**Why:**
- Clear pipeline structure makes it easy to add/remove steps
- Metrics enable monitoring and debugging
- Deduplication uses business logic, not just hashing

### writer.py
**Purpose:** Write curated and quarantine datasets.

**Key Functions:**
- `ensure_output_directory()`: Create output dirs if missing
- `write_curated_dataset()`: Write valid data to Parquet
- `write_quarantine_dataset()`: Write invalid data with errors
- `write_pipeline_metadata()`: (TODO) Write execution metadata

**Why:**
- Parquet format for compression & schema preservation
- Automatic directory creation prevents failures
- Separate paths for curated vs. quarantine

### main.py
**Purpose:** Orchestrate the complete pipeline.

**Pipeline Steps:**
1. Read input file
2. Validate structure
3. Run all validations
4. Transform valid data
5. Write curated output
6. Write quarantine output
7. Log execution summary

**Key Design:**
- Returns exit code (0 = success, 1 = failure)
- Accepts command-line arguments (file, format)
- Comprehensive error handling & logging

**Execution Flow:**
```
main()
├── read_input_file()
├── validate_dataframe_structure()
├── run_all_validations()
│   ├── validate_required_fields()
│   ├── validate_data_types()
│   ├── validate_accepted_values()
│   ├── validate_timestamps()
│   └── validate_amount_range()
├── transform_pipeline()
│   ├── normalize_column_names()
│   ├── standardize_timestamps()
│   ├── deduplicate_records()
│   ├── mask_pii()
│   ├── standardize_currency()
│   └── apply_business_transformations()
├── write_curated_dataset()
├── write_quarantine_dataset()
└── log_execution_summary()
```

## Testing Strategy

### Unit Tests (test_validator.py)
- Required fields validation
- Data type validation
- Accepted values validation
- Timestamp validation
- Amount range validation
- Edge cases & multiple errors

**Example:**
```python
def test_invalid_currency(self):
    df = pd.DataFrame({"currency": ["XYZ"]})
    valid, invalid = validate_accepted_values(df)
    assert len(invalid) == 1
```

### Unit Tests (test_transformer.py)
- Column name normalization
- Timestamp standardization
- Deduplication logic
- PII masking
- Full pipeline execution
- Edge cases (empty DataFrame, single record)

**Example:**
```python
def test_duplicate_detection(self):
    result, dup_count = deduplicate_records(sample_raw_data)
    assert dup_count == 1  # Removed 1 duplicate
```

### Running Tests
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validator.py

# Run specific test class
pytest tests/test_validator.py::TestRequiredFieldsValidation
```

## Running the Pipeline

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```bash
# Run with default input file (data/raw/events.csv)
python -m src.main

# Run with custom input file
python -m src.main /path/to/data.csv csv

# Run with JSON input
python -m src.main /path/to/data.json json
```

### Expected Output
```
============================================================
Data Pipeline Started
============================================================

[STEP 1] Reading input data...
Successfully read 1000 rows from data/raw/events.csv
Columns: ['event_id', 'customer_id', ...]

[STEP 2] Running validation checks...
Validation Results:
  - Valid records: 950
  - Invalid records: 50

[STEP 3] Transforming valid data...
Transformation Results:
  - Output records: 920
  - Duplicates removed: 30

[STEP 4] Writing output datasets...
Successfully wrote 920 records to data/curated/events_curated.parquet
Successfully wrote 50 invalid records to data/quarantine/events_invalid.parquet

[STEP 5] Pipeline execution summary...
============================================================
Pipeline Execution Summary
============================================================
timestamp: 2026-01-15T10:40:00.123456
input_file: data/raw/events.csv
input_rows: 1000
valid_rows: 950
invalid_rows: 50
output_rows: 920
duplicates_removed: 30
curated_output: data/curated/events_curated.parquet
quarantine_output: data/quarantine/events_invalid.parquet
execution_time_seconds: 2.34
status: SUCCESS
============================================================
Data Pipeline Completed Successfully
============================================================
```

## Future Enhancements

### Short Term
1. **Sample Data Generation:** Create synthetic test data in `data/raw/`
2. **Metadata Logging:** Write execution metrics to JSON for audit trail
3. **CLI Improvements:** Add argparse for better command-line interface
4. **Configuration Files:** Support YAML/JSON config files

### Medium Term
1. **Data Quality Monitoring:** Track metrics over time (volume, freshness, duplicates)
2. **Schema Registry:** Track schema versions and enforce compatibility
3. **Reference Data Management:** Handle customer/product dimensions
4. **dbt Integration:** Move transformations to dbt for version control & documentation

### Long Term
1. **Streaming Ingestion:** Add Kafka/Kinesis for real-time events
2. **Spark Support:** Scale to multi-node processing
3. **Orchestration:** Integrate with Airflow for scheduling
4. **Advanced Quality:** ML-based anomaly detection
5. **Lineage Tracking:** Full column-level lineage with OpenLineage

## Production Considerations

### Scalability
- Current implementation uses pandas (in-memory)
- For >10GB files, transition to Spark/Polars
- Streaming architecture for continuous pipelines

### Reliability
- Idempotent operations (safe to re-run)
- Comprehensive error handling & logging
- Quarantine layer prevents data loss

### Observability
- Structured logging with execution metrics
- Quality metrics tracked per run
- Error tracking for diagnosis

### Security
- PII masking in Silver layer
- Configuration-based credentials (environment variables)
- Access control via file permissions

### Cost
- Parquet compression reduces storage 80%
- Partitioning enables efficient queries
- Batch processing cheaper than streaming
