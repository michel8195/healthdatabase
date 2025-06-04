#!/usr/bin/env python3
"""
Setup sport_data table in the database.

This script creates the sport_data table and its indexes.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import SportModel
from src.utils.logging_config import setup_logging


def main():
    """Main function to setup sport table."""
    # Set up logging
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)

    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    logger.info(f"Setting up sport_data table in: {db_path}")

    try:
        # Initialize database connection
        db_conn = DatabaseConnection(str(db_path))

        # Get the sport model
        sport_model = SportModel()

                # Create the table
        logger.info("Creating sport_data table...")
        with db_conn.get_cursor() as cursor:
            cursor.execute(sport_model.get_create_sql())

            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in sport_model.get_indexes_sql():
                cursor.execute(index_sql)

        logger.info("Sport table setup completed successfully!")

        # Verify table exists
        with db_conn.get_cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sport_data'
            """)

            if cursor.fetchone():
                logger.info("✅ sport_data table verified")
            else:
                logger.error("❌ sport_data table not found")
                return 1

        return 0

    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())