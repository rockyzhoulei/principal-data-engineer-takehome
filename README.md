# Principal Data Engineer Take-Home Assignment

This project implements a simple, production-oriented batch data pipeline using a Bronze → Silver → Gold pattern. It reads raw event data, validates and quarantines bad records, deduplicates valid events, and writes curated outputs in Parquet format.

## Overview

The solution is intentionally small and maintainable. The core responsibilities are separated across modules in `src/`:
- `reader.py` reads raw input data from CSV/JSON
- `validator.py` applies data quality checks and quarantines invalid rows
- `transformer.py` standardizes and deduplicates valid data
- `writer.py` writes curated and quarantine outputs
- `config.py` centralizes policy and constants

This keeps the pipeline understandable, testable, and aligned with the architecture in [ARCHITECTURE.md](ARCHITECTURE.md).

## Quick Start

- Create a virtual environment
- Activate the virtual environment
- Install dependencies
- Run the pipeline
- Run the tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
pytest
```

The sample data under `data/raw/` is entirely synthetic and is included only to demonstrate validation, deduplication, quarantine handling, and end-to-end pipeline execution.

## Repository Structure

```text
.
├── src/
│   ├── main.py
│   ├── reader.py
│   ├── validator.py
│   ├── transformer.py
│   ├── writer.py
│   ├── config.py
│   ├── models.py
│   └── utils.py
├── tests/
│   ├── test_validator.py
│   └── test_transformer.py
├── data/
│   ├── raw/
│   ├── curated/
│   └── quarantine/
├── ARCHITECTURE.md
├── IMPLEMENTATION.md
├── README.md
├── requirements.txt
├── pytest.ini
├── .gitlab-ci.yml
└── .gitignore
```

## Setup

### Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Run the pipeline

```bash
python -m src.main
```

You can also pass a specific input file and format:

```bash
python -m src.main data/raw/events.csv csv
python -m src.main data/raw/events.json json
```

## Run tests

```bash
pytest
```

Or a specific file:

```bash
pytest tests/test_validator.py
pytest tests/test_transformer.py
```

## Assumptions and constraints

- Batch processing is sufficient; this is not a streaming design.
- Input is structured event data in CSV or JSON format.
- Data quality checks are applied before promotion to curated output.
- The pipeline uses Parquet for storage efficiency and schema stability.
- The design prioritizes correctness, auditability, and simple operations over low-latency streaming.

## Data flow

1. Raw incoming records are read from `data/raw/`.
2. Validation checks identify bad rows and quarantine them.
3. Valid rows continue through transformation.
4. Deduplication removes duplicate business events using the configured business key.
5. Curated records are written to `data/curated/events_curated.parquet`.
6. Invalid records are written to `data/quarantine/events_invalid.parquet`.

## Validation and quarantine behavior

Validation happens before records are promoted to the curated layer. Rows failing checks are not silently dropped; they are written to quarantine for investigation and reprocessing.

Examples of validation rules:
- required fields must be present and non-null
- accepted currencies and source systems are enforced
- timestamps must be valid and not future-dated
- amount must be numeric and within the accepted range

## Deduplication business rule

The deduplication rule is intentionally simple and documented in [ARCHITECTURE.md](ARCHITECTURE.md):
- business key: `{customer_id, source_system, event_id}`
- keep the record with the latest `event_timestamp`
- if timestamps are tied, keep the record with the latest `ingestion_timestamp`
- this is applied only after validation, to the valid records set

## Data quality strategy

The project is designed around a practical data quality workflow:
- fail fast on schema issues
- quarantine invalid records with error details
- keep a clean curated output for downstream consumers
- log execution metrics and counts for operational review

## Architecture summary

This is a Bronze → Silver → Gold pattern. For the full design rationale and layer decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Security and privacy considerations

- Keep raw data access restricted.
- Mask or tokenize PII in downstream layers where appropriate.
- Avoid storing secrets in source files; use environment variables or GitLab CI variables instead.
- Keep quarantine files auditable and reviewable.

## Cost optimization considerations

- Parquet with compression keeps storage costs low.
- Batch processing is cheaper and simpler than streaming for this assignment scale.
- Partitioning by date and avoiding high-cardinality partition keys limits query and storage overhead.

## Observability and lineage strategy

- log execution summaries with row counts and outputs
- track validation and deduplication metrics
- retain raw plus quarantined artifacts for traceability
- use metadata and auditability to support lineage review

## Key trade-offs

- Batch processing is chosen over streaming to keep the solution simple and reliable.
- Quarantine is preferred over silent data loss to maintain auditability.
- The project keeps a small scope and focuses on engineering discipline rather than overbuilding.

## What would be added next for production readiness

- schema versioning and stronger lineage metadata
- richer quality dashboards and alerting
- environment-specific configuration management
- stricter deployment gates and promotion controls
- more comprehensive auditing and retention policies

## Example Execution

The bundled synthetic sample dataset executes successfully with the current pipeline.

- Input Records: 14
- Valid Records: 9
- Invalid Records: 5
- Duplicates Removed: 2
- Curated Output: 7

Output files:
- `data/curated/events_curated.parquet`
- `data/quarantine/events_invalid.parquet`

## Related docs

- [ARCHITECTURE.md](ARCHITECTURE.md) for layer design and assumptions
- [IMPLEMENTATION.md](IMPLEMENTATION.md) for module-level implementation notes
