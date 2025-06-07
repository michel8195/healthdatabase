"""
Database schema management for health data system.

This module handles database schema creation, migration, and verification
using the modular model system.
"""

import logging
from typing import Dict, List, Optional

from src.database.connection import DatabaseConnection
from src.database.models import get_all_models, get_model, BaseModel

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema operations."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize schema manager.

        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
        self.models = get_all_models()

    def create_all_tables(self) -> bool:
        """
        Create all tables defined in the model registry.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating database schema...")

            with self.db_connection.get_cursor() as cursor:
                # Create tables in dependency order
                creation_order = ['users', 'activity', 'sleep', 'sport', 'heart_rate']

                for model_name in creation_order:
                    if model_name in self.models:
                        model = self.models[model_name]
                        self._create_table(cursor, model)
                        self._create_indexes(cursor, model)

                # Create any remaining tables not in creation_order
                for model_name, model in self.models.items():
                    if model_name not in creation_order:
                        self._create_table(cursor, model)
                        self._create_indexes(cursor, model)

                # Create update triggers
                self._create_update_triggers(cursor)

            logger.info("Database schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            return False

    def create_table(self, model: BaseModel) -> None:
        """Create a single table."""
        with self.db_connection.get_cursor() as cursor:
            self._create_table(cursor, model)
            self._create_indexes(cursor, model)

    def _create_table(self, cursor, model: BaseModel) -> None:
        """Create a single table."""
        table_name = model.get_table_name()
        create_sql = model.get_create_sql()

        logger.info(f"Creating table: {table_name}")
        cursor.execute(create_sql)

    def _create_indexes(self, cursor, model: BaseModel) -> None:
        """Create indexes for a model."""
        table_name = model.get_table_name()
        indexes_sql = model.get_indexes_sql()

        for index_sql in indexes_sql:
            logger.debug(f"Creating index for {table_name}: {index_sql}")
            cursor.execute(index_sql)

    def _create_update_triggers(self, cursor) -> None:
        """Create update triggers for timestamp management."""
        tables_with_timestamps = [
            'users', 'daily_activity', 'sleep_data', 'sport_data', 'heart_rate_data'
        ]

        for table_name in tables_with_timestamps:
            trigger_sql = f"""
            CREATE TRIGGER IF NOT EXISTS update_{table_name}_timestamp
            AFTER UPDATE ON {table_name}
            FOR EACH ROW
            BEGIN
                UPDATE {table_name}
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            """
            logger.debug(f"Creating update trigger for {table_name}")
            cursor.execute(trigger_sql)

    def verify_schema(self) -> bool:
        """
        Verify that all required tables and indexes exist.

        Returns:
            True if schema is valid, False otherwise
        """
        try:
            logger.info("Verifying database schema...")

            for model_name, model in self.models.items():
                table_name = model.get_table_name()

                # Check if table exists
                table_info = self.db_connection.get_table_info(table_name)
                if not table_info:
                    logger.error(f"Table {table_name} does not exist")
                    return False

                logger.debug(f"Table {table_name} exists with {len(table_info)} columns")

            logger.info("Database schema verification passed")
            return True

        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False

    def get_schema_stats(self) -> Dict[str, any]:
        """
        Get statistics about the database schema and data.

        Returns:
            Dictionary with schema and data statistics
        """
        try:
            stats = {
                'tables': {},
                'total_records': 0,
                'schema_version': '2.0'  # New multi-table schema
            }

            for model_name, model in self.models.items():
                table_name = model.get_table_name()

                # Get row count
                result = self.db_connection.execute_query(
                    f"SELECT COUNT(*) as count FROM {table_name}"
                )
                row_count = result[0]['count'] if result else 0

                stats['tables'][table_name] = {
                    'model_name': model_name,
                    'row_count': row_count
                }
                stats['total_records'] += row_count

            # Get date ranges for tables with date columns
            self._add_date_ranges(stats)

            return stats

        except Exception as e:
            logger.error(f"Failed to get schema stats: {e}")
            return {}

    def _add_date_ranges(self, stats: Dict) -> None:
        """Add date range information for relevant tables."""
        date_tables = {
            'daily_activity': 'date',
            'sleep_data': 'date',
            'heart_rate_data': 'timestamp'
        }

        for table_name, date_column in date_tables.items():
            if table_name in stats['tables']:
                try:
                    result = self.db_connection.execute_query(
                        f"SELECT MIN({date_column}) as min_date, "
                        f"MAX({date_column}) as max_date FROM {table_name}"
                    )

                    if result and result[0]['min_date']:
                        stats['tables'][table_name]['date_range'] = {
                            'min_date': result[0]['min_date'],
                            'max_date': result[0]['max_date']
                        }

                except Exception as e:
                    logger.warning(f"Failed to get date range for {table_name}: {e}")

    def ensure_default_user(self, user_id: str = "default") -> int:
        """
        Ensure a default user exists and return their ID.

        Args:
            user_id: User identifier string

        Returns:
            Database ID of the user
        """
        try:
            # Check if user exists
            result = self.db_connection.execute_query(
                "SELECT id FROM users WHERE user_id = ?", (user_id,)
            )

            if result:
                return result[0]['id']

            # Create user if doesn't exist
            user_model = get_model('users')
            user_data = user_model.validate_data({
                'user_id': user_id,
                'name': 'Default User'
            })

            with self.db_connection.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (user_id, name) VALUES (?, ?)",
                    (user_data['user_id'], user_data['name'])
                )
                user_db_id = cursor.lastrowid

            logger.info(f"Created default user with ID: {user_db_id}")
            return user_db_id

        except Exception as e:
            logger.error(f"Failed to ensure default user: {e}")
            return 1  # Fallback to ID 1


def create_database_schema(db_connection: DatabaseConnection) -> bool:
    """
    Convenience function to create the complete database schema.

    Args:
        db_connection: Database connection instance

    Returns:
        True if successful, False otherwise
    """
    schema_manager = SchemaManager(db_connection)

    # Create all tables
    if not schema_manager.create_all_tables():
        return False

    # Ensure default user exists
    schema_manager.ensure_default_user()

    # Verify schema
    return schema_manager.verify_schema()


def verify_database_schema(db_connection: DatabaseConnection) -> bool:
    """
    Convenience function to verify the database schema.

    Args:
        db_connection: Database connection instance

    Returns:
        True if schema is valid, False otherwise
    """
    schema_manager = SchemaManager(db_connection)
    return schema_manager.verify_schema()


def get_database_stats(db_connection: DatabaseConnection) -> Dict[str, any]:
    """
    Convenience function to get database statistics.

    Args:
        db_connection: Database connection instance

    Returns:
        Dictionary with database statistics
    """
    schema_manager = SchemaManager(db_connection)
    return schema_manager.get_schema_stats()