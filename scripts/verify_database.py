#!/usr/bin/env python3
"""
Database verification script for health data analytics system.
"""

import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from utils.logging_config import setup_logging
from database.connection import DatabaseConnection
from database.init_db import check_database_status
from database.models import get_table_stats


def main():
    """Main function to verify the database."""
    # Setup logging
    setup_logging(level="INFO")

    print("Health Data Analytics - Database Verification")
    print("=" * 45)

    # Check database status
    status = check_database_status()

    print(f"Database exists: {'✅' if status['exists'] else '❌'}")
    print(f"Schema valid: {'✅' if status['schema_valid'] else '❌'}")

    if not status['exists'] or not status['schema_valid']:
        print("\n❌ Database is not properly set up!")
        print("Run 'python scripts/setup_database.py' to initialize.")
        return

    # Get detailed statistics
    db_connection = DatabaseConnection()
    stats = get_table_stats(db_connection)

    print(f"\n📊 Database Statistics:")
    print(f"  Total records: {stats.get('total_records', 0)}")

    date_range = stats.get('date_range', {})
    if date_range:
        print(f"  Date range: {date_range['min_date']} to {date_range['max_date']}")

    sources = stats.get('sources', {})
    if sources:
        print(f"  Data sources:")
        for source, count in sources.items():
            print(f"    - {source}: {count} records")

    # Get some sample data
    print(f"\n📋 Sample Data (first 5 records):")
    sample_data = db_connection.execute_query(
        "SELECT date, steps, calories FROM daily_activity ORDER BY date LIMIT 5"
    )

    if sample_data:
        print("  Date       | Steps | Calories")
        print("  -----------|-------|----------")
        for row in sample_data:
            print(f"  {row['date']} | {row['steps']:5} | {row['calories']:8}")

    # Basic data quality checks
    print(f"\n🔍 Data Quality Checks:")

    # Check for missing dates
    missing_steps = db_connection.execute_query(
        "SELECT COUNT(*) as count FROM daily_activity WHERE steps IS NULL"
    )[0]['count']

    missing_calories = db_connection.execute_query(
        "SELECT COUNT(*) as count FROM daily_activity WHERE calories IS NULL"
    )[0]['count']

    print(f"  Records with missing steps: {missing_steps}")
    print(f"  Records with missing calories: {missing_calories}")

    # Check for reasonable ranges
    extreme_steps = db_connection.execute_query(
        "SELECT COUNT(*) as count FROM daily_activity WHERE steps > 50000 OR steps < 0"
    )[0]['count']

    extreme_calories = db_connection.execute_query(
        "SELECT COUNT(*) as count FROM daily_activity WHERE calories > 10000 OR calories < 0"
    )[0]['count']

    print(f"  Records with extreme steps (>50k or <0): {extreme_steps}")
    print(f"  Records with extreme calories (>10k or <0): {extreme_calories}")

    print(f"\n✅ Database verification completed!")


if __name__ == "__main__":
    main()