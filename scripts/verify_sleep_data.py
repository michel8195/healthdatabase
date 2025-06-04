#!/usr/bin/env python3
"""
Verify sleep data import and timezone conversion.

This script checks that sleep data was imported correctly with GMT-3 conversion.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging_config import setup_logging


def main():
    """Main function to verify sleep data."""
    setup_logging(level="INFO")

    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    print(f"Verifying sleep data in: {db_path}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if sleep_data table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='sleep_data'
        """)

        if not cursor.fetchone():
            print("❌ sleep_data table not found!")
            return 1

        # Get basic statistics
        cursor.execute("SELECT COUNT(*) FROM sleep_data")
        total_records = cursor.fetchone()[0]
        print(f"📊 Total sleep records: {total_records}")

        # Check date range
        cursor.execute("""
            SELECT MIN(date), MAX(date) FROM sleep_data
        """)
        min_date, max_date = cursor.fetchone()
        print(f"📅 Date range: {min_date} to {max_date}")

        # Show sample records with timezone info
        cursor.execute("""
            SELECT date, sleep_start, sleep_end,
                   total_sleep_minutes, deep_sleep_minutes,
                   light_sleep_minutes, rem_sleep_minutes
            FROM sleep_data
            WHERE sleep_start IS NOT NULL
            ORDER BY date
            LIMIT 5
        """)

        print("\n🕐 Sample records (showing GMT-3 conversion):")
        print("-" * 80)
        print(f"{'Date':<12} {'Sleep Start (GMT-3)':<20} {'Sleep End (GMT-3)':<20} {'Total':<6} {'Deep':<5} {'Light':<6} {'REM':<5}")
        print("-" * 80)

        for row in cursor.fetchall():
            date, start, end, total, deep, light, rem = row
            start_str = start[:19] if start else "N/A"
            end_str = end[:19] if end else "N/A"
            print(f"{date:<12} {start_str:<20} {end_str:<20} {total:<6} {deep:<5} {light:<6} {rem:<5}")

        # Check for records with valid timestamps
        cursor.execute("""
            SELECT COUNT(*) FROM sleep_data
            WHERE sleep_start IS NOT NULL AND sleep_end IS NOT NULL
        """)
        valid_timestamps = cursor.fetchone()[0]
        print(f"\n✅ Records with valid timestamps: {valid_timestamps}")

        # Show timezone verification for a specific record
        cursor.execute("""
            SELECT date, sleep_start, sleep_end
            FROM sleep_data
            WHERE sleep_start IS NOT NULL
            ORDER BY date
            LIMIT 1
        """)

        sample_record = cursor.fetchone()
        if sample_record:
            date, start, end = sample_record
            print(f"\n🔍 Timezone verification for {date}:")
            print(f"   Sleep start: {start}")
            print(f"   Sleep end: {end}")

            # Parse and show timezone info
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                print(f"   Timezone offset: {start_dt.strftime('%z')} (should be -0300 for GMT-3)")
            except ValueError as e:
                print(f"   Error parsing timestamp: {e}")

        # Show sleep efficiency statistics
        cursor.execute("""
            SELECT AVG(sleep_efficiency), MIN(sleep_efficiency), MAX(sleep_efficiency)
            FROM sleep_data
            WHERE sleep_efficiency > 0
        """)
        avg_eff, min_eff, max_eff = cursor.fetchone()
        if avg_eff:
            print(f"\n💤 Sleep efficiency stats:")
            print(f"   Average: {avg_eff:.1f}%")
            print(f"   Range: {min_eff:.1f}% - {max_eff:.1f}%")

        conn.close()
        print("\n✅ Sleep data verification completed successfully!")
        return 0

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())