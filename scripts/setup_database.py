#!/usr/bin/env python3
"""
Database setup script for health data analytics system.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from utils.logging_config import setup_logging
from database.init_db import initialize_database, check_database_status

def main():
    """Main function to setup the database."""
    # Setup logging
    setup_logging(level="INFO")

    print("Health Data Analytics - Database Setup")
    print("=" * 40)

    # Check current database status
    print("Checking current database status...")
    status = check_database_status()

    if status['exists'] and status['schema_valid']:
        print("Database already exists and is valid!")
        print(f"Current stats: {status['stats']}")

        response = input("Do you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    # Initialize database
    print("Initializing database...")
    success = initialize_database()

    if success:
        print("✅ Database setup completed successfully!")

        # Show final status
        final_status = check_database_status()
        print(f"Database location: {project_root}/data/health_data.db")
        print(f"Final stats: {final_status['stats']}")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()