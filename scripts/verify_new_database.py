#!/usr/bin/env python3
"""
Database verification script for the refactored health data system.
"""

import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.schema import get_database_stats
from src.utils.logging_config import setup_logging


def main():
    """Verify the health data database."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Health Data Database Verification ===")

        # Setup database path
        project_root = Path(__file__).parent.parent
        db_path = project_root / "data" / "health_data.db"

        if not db_path.exists():
            logger.error(f"Database file not found: {db_path}")
            sys.exit(1)

        logger.info(f"Database: {db_path}")

        # Create database connection
        db_conn = DatabaseConnection(str(db_path))

        # Get database statistics
        stats = get_database_stats(db_conn)

        logger.info("\n=== Database Statistics ===")
        logger.info(f"Schema version: {stats.get('schema_version', 'unknown')}")
        logger.info(f"Total records: {stats.get('total_records', 0)}")
        logger.info(f"Total tables: {len(stats.get('tables', {}))}")

        logger.info("\n=== Table Details ===")
        for table_name, table_stats in stats.get('tables', {}).items():
            logger.info(f"\n{table_name.upper()}:")
            logger.info(f"  Records: {table_stats['row_count']}")
            logger.info(f"  Model: {table_stats['model_name']}")

            if 'date_range' in table_stats:
                date_range = table_stats['date_range']
                logger.info(f"  Date range: {date_range['min_date']} to {date_range['max_date']}")

        # Sample some data
        logger.info("\n=== Sample Data ===")

        # Activity data sample
        activity_sample = db_conn.execute_query(
            "SELECT date, steps, calories, distance FROM daily_activity ORDER BY date LIMIT 5"
        )
        if activity_sample:
            logger.info("\nActivity Data (first 5 records):")
            for row in activity_sample:
                logger.info(f"  {row['date']}: {row['steps']} steps, {row['calories']} cal, {row['distance']} km")

        # Sleep data sample
        sleep_sample = db_conn.execute_query(
            "SELECT date, total_sleep_minutes, deep_sleep_minutes, light_sleep_minutes, rem_sleep_minutes "
            "FROM sleep_data WHERE total_sleep_minutes > 0 ORDER BY date LIMIT 5"
        )
        if sleep_sample:
            logger.info("\nSleep Data (first 5 records with sleep):")
            for row in sleep_sample:
                total = row['total_sleep_minutes']
                deep = row['deep_sleep_minutes']
                light = row['light_sleep_minutes']
                rem = row['rem_sleep_minutes']
                logger.info(f"  {row['date']}: {total}min total ({deep}min deep, {light}min light, {rem}min REM)")

        logger.info("\n✅ Database verification completed successfully!")

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()