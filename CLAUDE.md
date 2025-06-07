# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Database Setup
```bash
# Create new database schema
python scripts/setup_new_database.py

# Verify database integrity and display sample data
python scripts/verify_new_database.py

# Display comprehensive database statistics
python scripts/database_summary.py
```

### Data Import
```bash
# Import single data files
python scripts/import_health_data.py activity path/to/ACTIVITY.csv
python scripts/import_health_data.py sleep path/to/SLEEP.csv
python scripts/import_sport_data.py path/to/SPORT.csv

# Bulk import from multiple files/directories
python scripts/bulk_import_health_data.py raw/ZEPP/

# Common options for imports
--dry-run                    # Test import without database changes
--verbose                    # Detailed logging
--duplicate-strategy update  # Handle duplicates (update/skip/error)
```

### Data Verification
```bash
# Verify specific data types
python scripts/verify_sleep_data.py
python scripts/verify_sport_data.py

# Summary reports
python scripts/sleep_data_summary.py
```

### Analysis

#### Interactive Web Dashboard 🌟
```bash
# Launch the interactive web dashboard (recommended)
python run_dashboard.py
# or directly with streamlit
streamlit run app.py

# Features:
# - Date range selection (last 3 years)
# - Daily values with 7-day and 30-day moving averages
# - Activity metrics: steps, calories, distance, active minutes
# - Sleep metrics: total sleep, deep/light/REM sleep, efficiency
# - Data export to CSV
```

#### Jupyter Notebooks  
```bash
# Start Jupyter for data exploration
jupyter notebook notebooks/health_data_exploration.ipynb

# Generate sleep regularity charts
python create_sleep_chart.py
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only database tests
pytest -m database

# Run tests excluding slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Development Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Core analysis tools: pandas, matplotlib, seaborn, numpy, jupyter
# Web UI tools: streamlit, plotly  
# Testing tools: pytest, pytest-cov
# No external dependencies for core database functionality (uses Python stdlib)
```

## Architecture Overview

This is a modular health data analytics system with a layered architecture:

### Database Layer (`src/database/`)
- **models.py**: Abstract base models with validation for each data type (Activity, Sleep, Sport, HeartRate, User)
- **schema.py**: Schema management and database operations  
- **connection.py**: SQLite database connection management
- **MODEL_REGISTRY**: Central registry mapping data types to model classes

### ETL Layer (`src/etl/`)
- **base_importer.py**: Abstract base classes (`BaseImporter`, `CSVImporter`, `JSONImporter`) 
- **zepp_importers.py**: Zepp-specific importers for activity and sleep data
- **bulk_importer.py**: Advanced bulk import with duplicate detection and handling strategies
- Importers follow factory pattern with consistent interfaces

### Key Design Patterns
- **Abstract Factory**: `BaseImporter` defines interface, concrete importers implement source-specific logic
- **Repository Pattern**: Models define data structure/validation, separate from database operations
- **Strategy Pattern**: Different validation and parsing strategies per data type

### Database Schema
- **users**: User information with timezone support
- **daily_activity**: Steps, calories, distance with unique constraint (user_id, date, data_source)
- **sleep_data**: Sleep stages, efficiency, start/end times with timezone handling
- **sport_data**: Exercise data with sport type classification
- **heart_rate_data**: Schema ready for future heart rate data

### Data Sources
- **Zepp CSV Support**: Activity (`ACTIVITY.csv`), Sleep (`SLEEP.csv`), Sport (`SPORT.csv`)
- **Timezone Handling**: GMT-3 conversion for Zepp data
- **Extensible Framework**: Easy to add new sources (Fitbit, Apple Health, etc.)

### Bulk Import Features
- **File Discovery**: Recursive scanning of directory structures
- **Duplicate Detection**: Uses composite key (user_id, date, data_source)
- **Handling Strategies**: update (default), skip, error
- **Batch Processing**: Configurable batch sizes for memory efficiency

## Key Files to Understand
- `src/database/models.py`: Core data models and validation logic
- `src/etl/base_importer.py`: Import framework architecture
- `scripts/bulk_import_health_data.py`: Advanced bulk import functionality
- `docs/architecture.md`: Detailed architecture documentation with diagrams