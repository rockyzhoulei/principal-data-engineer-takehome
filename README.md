# Principal Data Engineer Take-Home Assignment

## Overview
This is a Python project for the Principal Data Engineer take-home assignment. The project follows a clean, modular structure suitable for production-grade data engineering work.

## Project Structure
```
principal-data-engineer-takehome/
├── .venv/                  # Python virtual environment
├── src/                    # Source code
│   ├── main.py            # Main entry point
│   ├── reader.py          # Data reading module
│   ├── validator.py       # Data validation module
│   ├── transformer.py     # Data transformation module
│   └── writer.py          # Data writing module
├── tests/                 # Test suite
│   └── test_validator.py  # Validator tests
├── data/                  # Data directories
│   ├── raw/               # Raw input data
│   ├── curated/           # Processed data
│   └── quarantine/        # Invalid data
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── .gitlab-ci.yml        # CI/CD configuration
```

## Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation
1. Create and activate the virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests
```bash
pytest tests/
```

## Running the Application
```bash
python src/main.py
```

## Development Notes
- Add new modules to the `src/` directory
- Write tests in the `tests/` directory with `test_` prefix
- Store raw data in `data/raw/`
- Store processed data in `data/curated/`
- Store invalid data in `data/quarantine/`
