# Health Data Analytics System

A personal health data management and analysis system using SQLite to consolidate data from multiple health tracking sources.

## 🎯 Project Goals

- Consolidate health data from multiple sources (Whoop, Zepp, Hevy, Sibio)
- Provide correlation analysis between different health metrics
- Maintain data quality and integrity
- Automate backups and data preservation
- Generate insights through visualizations and reports


## 🚀 Current Status

**✅ Step 1 Complete: Database Creation**
- SQLite database with daily activity schema
- 500 records imported from Zepp data (2023-01-04 to 2024-09-28)
- Data validation and quality checks implemented
- Average daily steps: 9,839 | Average daily calories: 625

## 📁 Project Structure

```
healthdatabase/
├── data/                    # Data storage
│   └── health_data.db      # SQLite database (✅ Created)
├── src/                    # Source code (✅ Implemented)
│   ├── database/           # Database models and connection
│   │   ├── connection.py   # Database connection management
│   │   ├── models.py       # Schema definitions and models
│   │   └── init_db.py      # Database initialization
│   ├── etl/               # Extract, Transform, Load pipeline
│   │   └── zepp_importer.py # Zepp CSV data importer
│   └── utils/             # Utility functions
│       └── logging_config.py # Logging configuration
├── scripts/               # Utility scripts (✅ Created)
│   ├── setup_database.py  # Database initialization script
│   ├── import_zepp_data.py # Data import script
│   └── verify_database.py # Database verification script
├── tests/                 # Unit tests (📋 Planned)
├── raw/                   # Raw export files (✅ Contains Zepp data)
└── requirements.txt       # Python dependencies (✅ Created)
```

## 🛠️ Quick Start

1. **Initialize Database:**
   ```bash
   python3 scripts/setup_database.py
   ```

2. **Import Zepp Data:**
   ```bash
   python3 scripts/import_zepp_data.py raw/3075021305_1749046767350/ACTIVITY/
   ```

3. **Verify Database:**
   ```bash
   python3 scripts/verify_database.py
   ```
