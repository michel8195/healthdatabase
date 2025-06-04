#!/usr/bin/env python3
"""
Bulk importer for processing multiple health data files and handling
duplicates.
"""

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any
from datetime import datetime

from .zepp_importers import create_zepp_importer
from ..database import DatabaseConnection


logger = logging.getLogger(__name__)


class BulkImporter:
    """Handles bulk importing of health data from multiple files."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize bulk importer.

        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errors': []
        }

    def discover_zepp_files(self, base_path: Path) -> Dict[str, List[Path]]:
        """
        Discover ZEPP data files in directory structure.

        Args:
            base_path: Base directory to search (e.g., raw/ZEPP/)

        Returns:
            Dictionary mapping data types to file paths
        """
        discovered_files = {
            'activity': [],
            'sleep': [],
            'heartrate': []
        }

        if not base_path.exists():
            logger.warning(f"Base path does not exist: {base_path}")
            return discovered_files

        # Search for ZEPP data directories
        for export_dir in base_path.iterdir():
            if not export_dir.is_dir() or export_dir.name.startswith('.'):
                continue

            logger.info(f"Scanning ZEPP export directory: {export_dir.name}")

            # Look for activity files
            activity_dir = export_dir / 'ACTIVITY'
            if activity_dir.exists():
                for file_path in activity_dir.glob('ACTIVITY_*.csv'):
                    discovered_files['activity'].append(file_path)
                    logger.debug(f"Found activity file: {file_path}")

            # Look for sleep files
            sleep_dir = export_dir / 'SLEEP'
            if sleep_dir.exists():
                for file_path in sleep_dir.glob('SLEEP_*.csv'):
                    discovered_files['sleep'].append(file_path)
                    logger.debug(f"Found sleep file: {file_path}")

            # Look for heart rate files
            heartrate_dir = export_dir / 'HEARTRATE'
            if heartrate_dir.exists():
                for file_path in heartrate_dir.glob('HEARTRATE_*.csv'):
                    discovered_files['heartrate'].append(file_path)
                    logger.debug(f"Found heartrate file: {file_path}")

        total_files = sum(len(files) for files in discovered_files.values())
        logger.info(f"Discovery complete: {total_files} total files found")
        for data_type, files in discovered_files.items():
            logger.info(f"  {data_type}: {len(files)} files")

        return discovered_files

    def check_for_duplicates(self, data_type: str,
                             records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Check for duplicate records and separate new vs existing.

        Args:
            data_type: Type of data (activity, sleep, heartrate)
            records: List of records to check

        Returns:
            Tuple of (new_records, existing_records)
        """
        if not records:
            return [], []

        # Get table name from data type
        table_map = {
            'activity': 'daily_activity',
            'sleep': 'sleep_data',
            'heartrate': 'heart_rate_data'
        }

        table_name = table_map.get(data_type)
        if not table_name:
            logger.error(f"Unknown data type: {data_type}")
            return records, []

                # Extract unique keys from records for batch checking
        # Use (user_id, date, data_source) as the unique key
        unique_keys = []
        for record in records:
            key = (record['user_id'], record['date'], record['data_source'])
            unique_keys.append(key)

        # Build query to check for existing records
        key_conditions = []
        query_params = []
        for user_id, date, data_source in unique_keys:
            key_conditions.append("(user_id = ? AND date = ? AND data_source = ?)")
            query_params.extend([user_id, date, data_source])

        query = f"""
            SELECT user_id, date, data_source
            FROM {table_name}
            WHERE {' OR '.join(key_conditions)}
        """

        existing_keys = set()
        try:
            results = self.db_connection.execute_query(query, tuple(query_params))
            existing_keys = {(row['user_id'], row['date'], row['data_source'])
                           for row in results}
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            # If we can't check, assume all are new to be safe
            return records, []

        # Separate records
        new_records = []
        existing_records = []

        for record in records:
            key = (record['user_id'], record['date'], record['data_source'])
            if key in existing_keys:
                existing_records.append(record)
            else:
                new_records.append(record)

        logger.info(f"Duplicate check for {data_type}: "
                   f"{len(new_records)} new, {len(existing_records)} existing")

        return new_records, existing_records

    def handle_duplicate_strategy(self, data_type: str,
                                existing_records: List[Dict[str, Any]],
                                strategy: str = 'update') -> int:
        """
        Handle existing records based on strategy.

        Args:
            data_type: Type of data
            existing_records: Records that already exist
            strategy: How to handle duplicates ('update', 'skip', 'error')

        Returns:
            Number of records processed
        """
        if not existing_records:
            return 0

        if strategy == 'skip':
            logger.info(f"Skipping {len(existing_records)} existing {data_type} records")
            self.stats['records_skipped'] += len(existing_records)
            return len(existing_records)

        elif strategy == 'error':
            error_msg = f"Found {len(existing_records)} duplicate {data_type} records"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            raise ValueError(error_msg)

        elif strategy == 'update':
            logger.info(f"Updating {len(existing_records)} existing {data_type} records")
            return self._update_existing_records(data_type, existing_records)

        else:
            raise ValueError(f"Unknown duplicate strategy: {strategy}")

    def _update_existing_records(self, data_type: str,
                               records: List[Dict[str, Any]]) -> int:
        """
        Update existing records in database.

        Args:
            data_type: Type of data
            records: Records to update

        Returns:
            Number of records updated
        """
        table_map = {
            'activity': 'daily_activity',
            'sleep': 'sleep_data',
            'heartrate': 'heart_rate_data'
        }

        table_name = table_map.get(data_type)
        if not table_name:
            return 0

        updated_count = 0

        try:
            for record in records:
                # Build update query dynamically based on record fields
                set_clauses = []
                values = []

                for key, value in record.items():
                    if key != 'date':  # Don't update the key field
                        set_clauses.append(f"{key} = ?")
                        values.append(value)

                # Add updated timestamp
                set_clauses.append("updated_at = ?")
                values.append(datetime.now().isoformat())

                # Add WHERE clause value
                values.append(record['date'])

                update_query = f"""
                    UPDATE {table_name}
                    SET {', '.join(set_clauses)}
                    WHERE date = ?
                """

                # Use execute_insert method for UPDATE queries too
                with self.db_connection.get_cursor() as cursor:
                    cursor.execute(update_query, tuple(values))
                updated_count += 1

        except Exception as e:
            logger.error(f"Error updating {data_type} records: {e}")
            self.stats['errors'].append(f"Update error for {data_type}: {e}")

        self.stats['records_updated'] += updated_count
        logger.info(f"Successfully updated {updated_count} {data_type} records")
        return updated_count

    def _insert_records(self, data_type: str, records: List[Dict[str, Any]]) -> int:
        """
        Insert new records into database.

        Args:
            data_type: Type of data
            records: Records to insert

        Returns:
            Number of records inserted
        """
        table_map = {
            'activity': 'daily_activity',
            'sleep': 'sleep_data',
            'heartrate': 'heart_rate_data'
        }

        table_name = table_map.get(data_type)
        if not table_name or not records:
            return 0

        inserted_count = 0

        try:
            # Get column names from first record
            columns = list(records[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)

            # Add timestamps
            for record in records:
                record['created_at'] = datetime.now().isoformat()
                record['updated_at'] = datetime.now().isoformat()

            # Update columns list to include timestamps
            if 'created_at' not in columns:
                columns.extend(['created_at', 'updated_at'])
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)

            insert_query = f"""
                INSERT OR REPLACE INTO {table_name} ({column_names})
                VALUES ({placeholders})
            """

            # Prepare data for batch insert
            values_list = []
            for record in records:
                values = [record.get(col) for col in columns]
                values_list.append(tuple(values))

            # Execute batch insert
            inserted_count = self.db_connection.execute_many(
                insert_query, values_list
            )

        except Exception as e:
            logger.error(f"Error inserting {data_type} records: {e}")
            self.stats['errors'].append(f"Insert error for {data_type}: {e}")

        logger.info(f"Successfully inserted {inserted_count} {data_type} records")
        return inserted_count

    def import_files(self, files_by_type: Dict[str, List[Path]],
                    duplicate_strategy: str = 'update',
                    dry_run: bool = False) -> Dict[str, Any]:
        """
        Import multiple files with duplicate handling.

        Args:
            files_by_type: Dictionary mapping data types to file lists
            duplicate_strategy: How to handle duplicates ('update', 'skip', 'error')
            dry_run: If True, don't actually import data

        Returns:
            Import statistics dictionary
        """
        logger.info(f"Starting bulk import with strategy '{duplicate_strategy}'")
        if dry_run:
            logger.info("DRY RUN MODE - No data will be imported")

        # Reset stats
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errors': []
        }

        # Process each data type
        for data_type, file_paths in files_by_type.items():
            if not file_paths:
                continue

            logger.info(f"Processing {len(file_paths)} {data_type} files")

            for file_path in file_paths:
                try:
                    self._import_single_file(
                        file_path, data_type, duplicate_strategy, dry_run
                    )
                except Exception as e:
                    logger.error(f"Failed to import {file_path}: {e}")
                    self.stats['files_failed'] += 1
                    self.stats['errors'].append(f"{file_path}: {e}")

        # Log final stats
        logger.info("Bulk import completed:")
        logger.info(f"  Files processed: {self.stats['files_processed']}")
        logger.info(f"  Files failed: {self.stats['files_failed']}")
        logger.info(f"  Records inserted: {self.stats['records_inserted']}")
        logger.info(f"  Records updated: {self.stats['records_updated']}")
        logger.info(f"  Records skipped: {self.stats['records_skipped']}")

        if self.stats['errors']:
            logger.warning(f"  Errors encountered: {len(self.stats['errors'])}")

        return self.stats

    def _import_single_file(self, file_path: Path, data_type: str,
                          duplicate_strategy: str, dry_run: bool):
        """
        Import a single file with duplicate handling.

        Args:
            file_path: Path to file to import
            data_type: Type of data (activity, sleep, heartrate)
            duplicate_strategy: How to handle duplicates
            dry_run: If True, don't actually import
        """
        logger.info(f"Importing {data_type} file: {file_path.name}")

                # Create appropriate importer
        importer = create_zepp_importer(data_type, self.db_connection)
        if not importer:
            raise ValueError(f"No importer available for {data_type}")

                # Load and transform data using the base importer interface
        logger.debug(f"Loading data from {file_path}")

        # Parse the file directly to get records
        records = []
        for raw_record in importer.parse_file(file_path):
            try:
                transformed_record = importer.transform_record(raw_record)
                transformed_record['user_id'] = 1  # Default user
                transformed_record['data_source'] = importer.get_data_source_name()
                validated_record = importer.model.validate_data(transformed_record)
                records.append(validated_record)
            except Exception as e:
                logger.warning(f"Error processing record: {e}")
                continue

        if not records:
            logger.warning(f"No records found in {file_path}")
            self.stats['files_skipped'] += 1
            return

        logger.info(f"Loaded {len(records)} records from {file_path.name}")

        # Check for duplicates
        new_records, existing_records = self.check_for_duplicates(
            data_type, records
        )

        if dry_run:
            logger.info(f"DRY RUN: Would insert {len(new_records)} new records")
            logger.info(f"DRY RUN: Would handle {len(existing_records)} existing records")
            self.stats['files_processed'] += 1
            return

        # Handle existing records
        if existing_records:
            self.handle_duplicate_strategy(
                data_type, existing_records, duplicate_strategy
            )

        # Import new records
        if new_records:
            logger.info(f"Inserting {len(new_records)} new {data_type} records")
            self._insert_records(data_type, new_records)
            self.stats['records_inserted'] += len(new_records)

        self.stats['files_processed'] += 1
        logger.info(f"Successfully processed {file_path.name}")


def bulk_import_zepp_data(base_path: str,
                         duplicate_strategy: str = 'update',
                         dry_run: bool = False) -> Dict[str, Any]:
    """
    Convenience function to bulk import ZEPP data from a directory.

    Args:
        base_path: Path to directory containing ZEPP exports
        duplicate_strategy: How to handle duplicates ('update', 'skip', 'error')
        dry_run: If True, don't actually import data

    Returns:
        Import statistics
    """
    # Initialize database connection
    db_conn = DatabaseConnection()

    # Create bulk importer
    bulk_importer = BulkImporter(db_conn)

    # Discover files
    files_by_type = bulk_importer.discover_zepp_files(Path(base_path))

    # Import files
    return bulk_importer.import_files(
        files_by_type, duplicate_strategy, dry_run
    )