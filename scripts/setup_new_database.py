#!/usr/bin/env python3
"""
Simple database setup script for the refactored health data system.
"""

import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.schema import create_database_schema
from src.utils.logging_config import setup_logging


def main():
    """Set up the health data database."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Setting up Health Data Database ===")

        # Setup database path
        project_root = Path(__file__).parent.parent
        db_path = project_root / "data" / "health_data.db"

        logger.info(f"Database: {db_path}")

        # Create database connection
        db_conn = DatabaseConnection(str(db_path))

        # Create schema
        if create_database_schema(db_conn):
            logger.info("✅ Database schema created successfully!")
        else:
            logger.error("❌ Failed to create database schema")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()