#!/usr/bin/env python3
"""
Zepp data import script for health data analytics system.
"""

import sys
import argparse
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from utils.logging_config import setup_logging
from database.connection import DatabaseConnection
from database.init_db import check_database_status
from etl.zepp_importer import ZeppImporter


def main():
    """Main function to import Zepp data."""
    parser = argparse.ArgumentParser(
        description="Import Zepp activity data from CSV files"
    )
    parser.add_argument(
        "input_path",
        help="Path to CSV file or directory containing CSV files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    print("Health Data Analytics - Zepp Data Import")
    print("=" * 40)

    # Check database status
    print("Checking database status...")
    status = check_database_status()

    if not status['exists'] or not status['schema_valid']:
        print("❌ Database is not properly initialized!")
        print("Please run 'python scripts/setup_database.py' first.")
        sys.exit(1)

    print("✅ Database is ready")
    print(f"Current stats: {status['stats']}")

    # Validate input path
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ Input path does not exist: {input_path}")
        sys.exit(1)

    # Initialize importer
    db_connection = DatabaseConnection()
    importer = ZeppImporter(db_connection)

    # Import data
    try:
        if input_path.is_file():
            print(f"Importing single file: {input_path}")
            imported, skipped, errors = importer.import_csv_file(str(input_path))

            print(f"Import completed:")
            print(f"  - Imported: {imported} records")
            print(f"  - Skipped: {skipped} records")

            if errors:
                print(f"  - Errors: {len(errors)}")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"    * {error}")
                if len(errors) > 5:
                    print(f"    ... and {len(errors) - 5} more errors")

        elif input_path.is_dir():
            print(f"Importing directory: {input_path}")
            results = importer.import_directory(str(input_path))

            print(f"Import completed:")
            print(f"  - Files processed: {results['total_files']}")
            print(f"  - Records imported: {results['imported_count']}")
            print(f"  - Records skipped: {results['skipped_count']}")

            if results['error_messages']:
                print(f"  - Errors: {len(results['error_messages'])}")
                for error in results['error_messages'][:5]:
                    print(f"    * {error}")
                if len(results['error_messages']) > 5:
                    remaining = len(results['error_messages']) - 5
                    print(f"    ... and {remaining} more errors")

        else:
            print(f"❌ Invalid input path: {input_path}")
            sys.exit(1)

        # Show final database stats
        print("\nFinal database statistics:")
        final_status = check_database_status()
        print(f"  - Total records: {final_status['stats'].get('total_records', 0)}")
        date_range = final_status['stats'].get('date_range', {})
        if date_range:
            print(f"  - Date range: {date_range['min_date']} to {date_range['max_date']}")

        print("✅ Import completed successfully!")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()