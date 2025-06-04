"""
Database initialization module for health data analytics system.
"""

import logging
from database.connection import DatabaseConnection
from database.models import create_tables, verify_schema, get_table_stats

logger = logging.getLogger(__name__)


def initialize_database(db_path: str = None) -> bool:
    """
    Initialize the database with all required tables and indexes.

    Args:
        db_path: Optional custom database path

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        logger.info("Initializing health data database...")

        # Create database connection
        db_connection = DatabaseConnection(db_path)

        # Create tables and schema
        if not create_tables(db_connection):
            logger.error("Failed to create database tables")
            return False

        # Verify schema
        if not verify_schema(db_connection):
            logger.error("Database schema verification failed")
            return False

        # Log database stats
        stats = get_table_stats(db_connection)
        logger.info(f"Database initialized successfully. Stats: {stats}")

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def reset_database(db_path: str = None) -> bool:
    """
    Reset the database by dropping and recreating all tables.

    Args:
        db_path: Optional custom database path

    Returns:
        True if reset successful, False otherwise
    """
    try:
        logger.warning("Resetting database - all data will be lost!")

        db_connection = DatabaseConnection(db_path)

        # Drop existing tables
        with db_connection.get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS daily_activity")
            logger.info("Dropped existing tables")

        # Recreate tables
        return initialize_database(db_path)

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


def check_database_status(db_path: str = None) -> dict:
    """
    Check the status of the database.

    Args:
        db_path: Optional custom database path

    Returns:
        Dictionary with database status information
    """
    try:
        db_connection = DatabaseConnection(db_path)

        status = {
            'exists': db_connection.database_exists(),
            'schema_valid': False,
            'stats': {}
        }

        if status['exists']:
            status['schema_valid'] = verify_schema(db_connection)
            if status['schema_valid']:
                status['stats'] = get_table_stats(db_connection)

        return status

    except Exception as e:
        logger.error(f"Failed to check database status: {e}")
        return {'exists': False, 'schema_valid': False, 'stats': {}}


if __name__ == "__main__":
    # Setup basic logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize database
    success = initialize_database()
    if success:
        print("Database initialized successfully!")

        # Show status
        status = check_database_status()
        print(f"Database status: {status}")
    else:
        print("Database initialization failed!")
        exit(1)