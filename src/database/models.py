"""
Database models and schema definitions for health data analytics system.
"""

import logging
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


# SQL schema definitions
CREATE_DAILY_ACTIVITY_TABLE = """
CREATE TABLE IF NOT EXISTS daily_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    source VARCHAR(50) NOT NULL DEFAULT 'zepp',
    steps INTEGER,
    calories INTEGER,
    distance REAL,
    run_distance REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_daily_activity_date ON daily_activity(date);",
    "CREATE INDEX IF NOT EXISTS idx_daily_activity_source ON daily_activity(source);",
    "CREATE INDEX IF NOT EXISTS idx_daily_activity_date_source ON daily_activity(date, source);"
]

# Trigger to update the updated_at timestamp
CREATE_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_daily_activity_timestamp
AFTER UPDATE ON daily_activity
FOR EACH ROW
BEGIN
    UPDATE daily_activity
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
"""


def create_tables(db_connection: DatabaseConnection) -> bool:
    """
    Create all database tables and indexes.

    Args:
        db_connection: Database connection instance

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Creating database tables...")

        # Create main table
        with db_connection.get_cursor() as cursor:
            cursor.execute(CREATE_DAILY_ACTIVITY_TABLE)
            logger.info("Created daily_activity table")

            # Create indexes
            for index_sql in CREATE_INDEXES:
                cursor.execute(index_sql)
            logger.info("Created database indexes")

            # Create update trigger
            cursor.execute(CREATE_UPDATE_TRIGGER)
            logger.info("Created update trigger")

        logger.info("Database schema created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def verify_schema(db_connection: DatabaseConnection) -> bool:
    """
    Verify that the database schema is correct.

    Args:
        db_connection: Database connection instance

    Returns:
        True if schema is valid, False otherwise
    """
    try:
        # Check if main table exists
        table_info = db_connection.get_table_info('daily_activity')
        if not table_info:
            logger.error("daily_activity table does not exist")
            return False

        # Verify expected columns
        expected_columns = [
            'id', 'date', 'source', 'steps', 'calories',
            'distance', 'run_distance', 'created_at', 'updated_at'
        ]

        actual_columns = [col[1] for col in table_info]  # col[1] is column name

        for col in expected_columns:
            if col not in actual_columns:
                logger.error(f"Missing column: {col}")
                return False

        logger.info("Database schema verification passed")
        return True

    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def get_table_stats(db_connection: DatabaseConnection) -> dict:
    """
    Get statistics about the database tables.

    Args:
        db_connection: Database connection instance

    Returns:
        Dictionary with table statistics
    """
    try:
        stats = {}

        # Get row count
        result = db_connection.execute_query(
            "SELECT COUNT(*) as count FROM daily_activity"
        )
        stats['total_records'] = result[0]['count'] if result else 0

        # Get date range
        result = db_connection.execute_query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM daily_activity"
        )
        if result and result[0]['min_date']:
            stats['date_range'] = {
                'min_date': result[0]['min_date'],
                'max_date': result[0]['max_date']
            }

        # Get source breakdown
        result = db_connection.execute_query(
            "SELECT source, COUNT(*) as count FROM daily_activity GROUP BY source"
        )
        stats['sources'] = {row['source']: row['count'] for row in result}

        return stats

    except Exception as e:
        logger.error(f"Failed to get table stats: {e}")
        return {}


class DailyActivity:
    """Model class for daily activity data."""

    def __init__(self, date: str, source: str = 'zepp', steps: int = None,
                 calories: int = None, distance: float = None,
                 run_distance: float = None):
        self.date = date
        self.source = source
        self.steps = steps
        self.calories = calories
        self.distance = distance
        self.run_distance = run_distance

    def to_dict(self) -> dict:
        """Convert to dictionary for database operations."""
        return {
            'date': self.date,
            'source': self.source,
            'steps': self.steps,
            'calories': self.calories,
            'distance': self.distance,
            'run_distance': self.run_distance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyActivity':
        """Create instance from dictionary."""
        return cls(
            date=data['date'],
            source=data.get('source', 'zepp'),
            steps=data.get('steps'),
            calories=data.get('calories'),
            distance=data.get('distance'),
            run_distance=data.get('run_distance')
        )