"""
Database connection management for health data analytics system.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages SQLite database connections for the health data system."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        if db_path is None:
            # Default to data/health_data.db relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / "data" / "health_data.db"
        else:
            self.db_path = Path(db_path)

        # Ensure the directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Database path: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper configuration.

        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(str(self.db_path))

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Set row factory to return rows as dictionaries
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for database operations with automatic commit/rollback.

        Yields:
            SQLite cursor object
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str,
                      params: Optional[tuple] = None) -> list:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def execute_insert(self, query: str,
                       params: Optional[tuple] = None) -> Optional[int]:
        """
        Execute an INSERT query and return the last row ID.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            ID of the inserted row, or None if no row was inserted
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: list) -> int:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def database_exists(self) -> bool:
        """
        Check if the database file exists.

        Returns:
            True if database exists, False otherwise
        """
        return self.db_path.exists()

    def get_table_info(self, table_name: str) -> list:
        """
        Get information about a table's structure.

        Args:
            table_name: Name of the table

        Returns:
            List of column information
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

    def query_to_dataframe(self, query: str,
                           params: Optional[tuple] = None):
        """
        Execute a query and return results as a pandas DataFrame with
        proper column names.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            pandas DataFrame with proper column names

        Raises:
            ImportError: If pandas is not available
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for query_to_dataframe method"
            )

        rows = self.execute_query(query, params)
        if not rows:
            return pd.DataFrame()

        # Convert sqlite3.Row objects to dictionaries to preserve
        # column names
        data = [dict(row) for row in rows]
        return pd.DataFrame(data)