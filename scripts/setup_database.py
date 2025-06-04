#!/usr/bin/env python3
"""
Database setup script for health data analytics system.

This script creates the database schema with all required tables
for multiple data types (activity, sleep, heart rate, etc.).
"""

import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.schema import create_database_schema, get_database_stats
from src.utils.logging_config import setup_logging


def main():
    """Set up the health data database."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Health Data Database Setup ===")

                # Get database configuration
        project_root = Path(__file__).parent.parent
        db_path = project_root / "data" / "health_data.db"
        db_config = {'database_path': str(db_path)}
        logger.info(f"Database: {db_config['database_path']}")

        # Create database connection
        db_conn = DatabaseConnection(db_config)
        try:
            logger.info("Connected to database successfully")

            # Create schema
            logger.info("Creating database schema...")
            if create_database_schema(db_conn):
                logger.info("✓ Database schema created successfully")

                # Get and display stats
                stats = get_database_stats(db_conn)
                logger.info("\n=== Database Statistics ===")
                logger.info(f"Schema version: {stats.get('schema_version', 'unknown')}")
                logger.info(f"Total tables: {len(stats.get('tables', {}))}")

                for table_name, table_stats in stats.get('tables', {}).items():
                    logger.info(f"  - {table_name}: {table_stats['row_count']} records")

                logger.info("\n✅ Database setup completed successfully!")

            else:
                logger.error("❌ Failed to create database schema")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()