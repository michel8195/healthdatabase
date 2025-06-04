"""
Zepp data importer for health data analytics system.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sqlite3

from database.connection import DatabaseConnection
from database.models import DailyActivity

logger = logging.getLogger(__name__)


class ZeppImporter:
    """Imports Zepp activity data from CSV files."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize the Zepp importer.

        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection

    def validate_row(self, row: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate a single row of CSV data.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            if 'date' not in row or not row['date'].strip():
                return False, "Missing or empty date field"

            # Validate date format
            try:
                datetime.strptime(row['date'], '%Y-%m-%d')
            except ValueError:
                return False, f"Invalid date format: {row['date']}"

            # Validate numeric fields (they can be empty/None)
            numeric_fields = ['steps', 'calories', 'distance', 'runDistance']
            for field in numeric_fields:
                if field in row and row[field].strip():
                    try:
                        value = float(row[field])
                        if field in ['steps', 'calories'] and value < 0:
                            return False, f"Negative value for {field}: {value}"
                        if field in ['steps', 'calories'] and value > 100000:
                            return False, f"Unrealistic value for {field}: {value}"
                    except ValueError:
                        return False, f"Invalid numeric value for {field}: {row[field]}"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def convert_row_to_activity(self, row: Dict[str, str]) -> DailyActivity:
        """
        Convert a CSV row to a DailyActivity object.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            DailyActivity object
        """
        def safe_int(value: str) -> Optional[int]:
            if not value or not value.strip():
                return None
            try:
                return int(float(value))  # Handle decimal strings
            except ValueError:
                return None

        def safe_float(value: str) -> Optional[float]:
            if not value or not value.strip():
                return None
            try:
                return float(value)
            except ValueError:
                return None

        return DailyActivity(
            date=row['date'],
            source='zepp',
            steps=safe_int(row.get('steps', '')),
            calories=safe_int(row.get('calories', '')),
            distance=safe_float(row.get('distance', '')),
            run_distance=safe_float(row.get('runDistance', ''))
        )

    def import_csv_file(self, csv_file_path: str) -> Tuple[int, int, List[str]]:
        """
        Import data from a single CSV file.

        Args:
            csv_file_path: Path to the CSV file

        Returns:
            Tuple of (imported_count, skipped_count, error_messages)
        """
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

        imported_count = 0
        skipped_count = 0
        error_messages = []

        logger.info(f"Importing data from {csv_file_path}")

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)

                # Validate CSV headers
                logger.debug(f"CSV fieldnames: {reader.fieldnames}")
                expected_headers = {'date', 'steps', 'calories'}
                actual_headers = set(reader.fieldnames or [])
                logger.debug(f"Expected headers: {expected_headers}")
                logger.debug(f"Actual headers: {actual_headers}")
                if not expected_headers.issubset(actual_headers):
                    missing = expected_headers - actual_headers
                    raise ValueError(f"Missing required CSV headers: {missing}")

                activities_to_insert = []

                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    # Validate row
                    is_valid, error_msg = self.validate_row(row)
                    if not is_valid:
                        error_messages.append(f"Row {row_num}: {error_msg}")
                        skipped_count += 1
                        continue

                    # Convert to activity object
                    try:
                        activity = self.convert_row_to_activity(row)
                        activities_to_insert.append(activity)
                    except Exception as e:
                        error_messages.append(f"Row {row_num}: Failed to convert: {e}")
                        skipped_count += 1

                # Batch insert activities
                if activities_to_insert:
                    imported_count = self._batch_insert_activities(activities_to_insert)
                    logger.info(f"Imported {imported_count} records from {csv_file_path}")

        except Exception as e:
            error_msg = f"Failed to import CSV file {csv_file_path}: {e}"
            logger.error(error_msg)
            error_messages.append(error_msg)

        return imported_count, skipped_count, error_messages

    def _batch_insert_activities(self, activities: List[DailyActivity]) -> int:
        """
        Insert a batch of activities into the database.

        Args:
            activities: List of DailyActivity objects

        Returns:
            Number of records actually inserted
        """
        insert_query = """
        INSERT OR REPLACE INTO daily_activity
        (date, source, steps, calories, distance, run_distance)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        params_list = []
        for activity in activities:
            params_list.append((
                activity.date,
                activity.source,
                activity.steps,
                activity.calories,
                activity.distance,
                activity.run_distance
            ))

        try:
            inserted_count = self.db_connection.execute_many(insert_query, params_list)
            logger.info(f"Batch inserted {inserted_count} activities")
            return len(activities)  # Return number of activities processed
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return 0

    def import_directory(self, directory_path: str) -> Dict[str, any]:
        """
        Import all CSV files from a directory.

        Args:
            directory_path: Path to directory containing CSV files

        Returns:
            Dictionary with import statistics
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        csv_files = list(directory.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {directory_path}")
            return {
                'total_files': 0,
                'imported_count': 0,
                'skipped_count': 0,
                'error_messages': []
            }

        total_imported = 0
        total_skipped = 0
        all_errors = []

        logger.info(f"Found {len(csv_files)} CSV files in {directory_path}")

        for csv_file in csv_files:
            imported, skipped, errors = self.import_csv_file(str(csv_file))
            total_imported += imported
            total_skipped += skipped
            all_errors.extend(errors)

        return {
            'total_files': len(csv_files),
            'imported_count': total_imported,
            'skipped_count': total_skipped,
            'error_messages': all_errors
        }