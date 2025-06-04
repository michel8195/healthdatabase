#!/usr/bin/env python3
"""
Import Zepp sport data with GMT-3 timezone conversion.

This script imports sport/exercise data from Zepp CSV files, converting
timestamps from UTC to GMT-3 timezone.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.etl.zepp_importers import ZeppSportImporter
from src.utils.logging_config import setup_logging


def main():
    """Main function to import sport data."""
    # Set up logging
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)

    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    # Sport data file path
    sport_data_path = (
        Path(__file__).parent.parent /
        "raw" / "ZEPP" / "3075021305_1749047212827" / "SPORT" /
        "SPORT_1749047212545.csv"
    )

    if not sport_data_path.exists():
        logger.error(f"Sport data file not found: {sport_data_path}")
        return 1

    logger.info(f"Importing sport data from: {sport_data_path}")
    logger.info(f"Database: {db_path}")
    logger.info("Timezone conversion: UTC -> GMT-3")

    try:
        # Initialize database connection
        db_conn = DatabaseConnection(str(db_path))

        # Create sport importer with GMT-3 conversion
        importer = ZeppSportImporter(db_conn)

        # Set default user_id (assuming single user for now)
        default_user_id = 1

        # Import the data
        result = importer.import_file(
            file_path=sport_data_path,
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