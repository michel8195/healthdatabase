#!/usr/bin/env python3
"""
Import Zepp sleep data with GMT-3 timezone conversion.

This script imports sleep data from Zepp CSV files, converting sleep timestamps
from UTC to GMT-3 timezone as requested.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.etl.zepp_importers import ZeppSleepImporter
from src.utils.logging_config import setup_logging


def main():
    """Main function to import sleep data."""
    # Set up logging
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)

    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    # Sleep data file path
    sleep_data_path = (
        Path(__file__).parent.parent /
        "raw" / "ZEPP" / "3075021305_1749047212827" / "SLEEP" /
        "SLEEP_1749047211599.csv"
    )

    if not sleep_data_path.exists():
        logger.error(f"Sleep data file not found: {sleep_data_path}")
        return 1

    logger.info(f"Importing sleep data from: {sleep_data_path}")
    logger.info(f"Database: {db_path}")
    logger.info("Timezone conversion: UTC -> GMT-3")

    try:
        # Initialize database connection
        db_conn = DatabaseConnection(str(db_path))

        # Create sleep importer with GMT-3 conversion
        importer = ZeppSleepImporter(db_conn)

        # Set default user_id (assuming single user for now)
        default_user_id = 1

        # Import the data
        result = importer.import_file(
            file_path=sleep_data_path,
            user_id=default_user_id
        )

        logger.info("Import completed successfully!")
        logger.info(f"Records processed: {result.get('processed', 'N/A')}")
        logger.info(f"Records inserted: {result.get('inserted', 'N/A')}")
        logger.info(f"Records updated: {result.get('updated', 'N/A')}")
        logger.info(f"Errors: {result.get('errors', 'N/A')}")

        if result.get('errors', 0) > 0:
            logger.warning(f"Errors encountered: {result['errors']}")
            logger.warning("Check logs for details on specific errors")

        return 0

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())