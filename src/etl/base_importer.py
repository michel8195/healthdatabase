"""
Base importer classes for health data ETL.

This module provides abstract base classes and interfaces for importing
health data from various sources in a consistent, extensible manner.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Iterator
from pathlib import Path
import csv
import json

from src.database.connection import DatabaseConnection
from src.database.models import BaseModel

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Exception raised when data validation fails."""
    pass


class ImportError(Exception):
    """Exception raised when data import fails."""
    pass


class BaseImporter(ABC):
    """Abstract base class for all data importers."""

    def __init__(self, db_connection: DatabaseConnection, model: BaseModel):
        """
        Initialize the importer.

        Args:
            db_connection: Database connection instance
            model: Data model instance for validation and schema
        """
        self.db_connection = db_connection
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def get_data_source_name(self) -> str:
        """Return the name of the data source (e.g., 'zepp', 'fitbit')."""
        pass

    @abstractmethod
    def get_supported_file_types(self) -> List[str]:
        """Return list of supported file extensions (e.g., ['.csv', '.json'])."""
        pass

    @abstractmethod
    def parse_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Parse a data file and yield individual records.

        Args:
            file_path: Path to the data file

        Yields:
            Dictionary containing parsed record data

        Raises:
            ImportError: If file cannot be parsed
        """
        pass

    @abstractmethod
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a raw record into the format expected by the model.

        Args:
            raw_record: Raw record data from the source

        Returns:
            Transformed record data

        Raises:
            DataValidationError: If record cannot be transformed
        """
        pass

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that a file is supported by this importer.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is supported, False otherwise
        """
        if not file_path.exists():
            return False

        return file_path.suffix.lower() in self.get_supported_file_types()

    def import_file(self, file_path: Path, user_id: int = 1,
                   batch_size: int = 100, dry_run: bool = False) -> Dict[str, int]:
        """
        Import data from a file into the database.

        Args:
            file_path: Path to the data file
            user_id: ID of the user this data belongs to
            batch_size: Number of records to process in each batch
            dry_run: If True, validate data but don't insert into database

        Returns:
            Dictionary with import statistics

        Raises:
            ImportError: If import fails
        """
        if not self.validate_file(file_path):
            raise ImportError(f"File not supported: {file_path}")

        stats = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

        batch = []

        try:
            self.logger.info(f"Starting import from {file_path}")

            for raw_record in self.parse_file(file_path):
                try:
                    # Transform and validate record
                    transformed_record = self.transform_record(raw_record)
                    transformed_record['user_id'] = user_id
                    transformed_record['data_source'] = self.get_data_source_name()

                    # Validate using model
                    validated_record = self.model.validate_data(transformed_record)

                    batch.append(validated_record)
                    stats['processed'] += 1

                    # Process batch when it reaches the specified size
                    if len(batch) >= batch_size:
                        if not dry_run:
                            batch_stats = self._insert_batch(batch)
                            stats['inserted'] += batch_stats['inserted']
                            stats['updated'] += batch_stats['updated']
                        batch = []

                except (DataValidationError, ValueError) as e:
                    self.logger.warning(f"Validation error for record: {e}")
                    stats['errors'] += 1
                    continue

                except Exception as e:
                    self.logger.error(f"Unexpected error processing record: {e}")
                    stats['errors'] += 1
                    continue

            # Process remaining records in the final batch
            if batch and not dry_run:
                batch_stats = self._insert_batch(batch)
                stats['inserted'] += batch_stats['inserted']
                stats['updated'] += batch_stats['updated']

            self.logger.info(f"Import completed. Stats: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            raise ImportError(f"Failed to import {file_path}: {e}")

    def _insert_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert a batch of records into the database.

        Args:
            batch: List of validated records to insert

        Returns:
            Dictionary with batch statistics
        """
        stats = {'inserted': 0, 'updated': 0}

        # Generate INSERT OR REPLACE statement
        table_name = self.model.get_table_name()
        columns = list(batch[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)

        sql = f"""
        INSERT OR REPLACE INTO {table_name} ({column_names})
        VALUES ({placeholders})
        """

        with self.db_connection.get_cursor() as cursor:
            for record in batch:
                values = [record[col] for col in columns]
                cursor.execute(sql, values)

                # Check if this was an insert or update
                if cursor.lastrowid:
                    stats['inserted'] += 1
                else:
                    stats['updated'] += 1

        return stats


class CSVImporter(BaseImporter):
    """Base class for CSV-based importers."""

    def __init__(self, db_connection: DatabaseConnection, model: BaseModel,
                 delimiter: str = ',', encoding: str = 'utf-8-sig'):
        """
        Initialize CSV importer.

        Args:
            db_connection: Database connection instance
            model: Data model instance
            delimiter: CSV delimiter character
            encoding: File encoding (utf-8-sig handles BOM)
        """
        super().__init__(db_connection, model)
        self.delimiter = delimiter
        self.encoding = encoding

    def get_supported_file_types(self) -> List[str]:
        """CSV files are supported."""
        return ['.csv']

    def parse_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Parse CSV file and yield records as dictionaries.

        Args:
            file_path: Path to CSV file

        Yields:
            Dictionary with CSV row data
        """
        try:
            with open(file_path, 'r', encoding=self.encoding, newline='') as file:
                reader = csv.DictReader(file, delimiter=self.delimiter)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    # Skip empty rows
                    if not any(row.values()):
                        continue

                    # Clean up field names and values
                    cleaned_row = {}
                    for key, value in row.items():
                        if key:  # Skip empty column names
                            clean_key = key.strip()
                            clean_value = value.strip() if value else None
                            cleaned_row[clean_key] = clean_value

                    yield cleaned_row

        except Exception as e:
            raise ImportError(f"Failed to parse CSV file {file_path}: {e}")


class JSONImporter(BaseImporter):
    """Base class for JSON-based importers."""

    def get_supported_file_types(self) -> List[str]:
        """JSON files are supported."""
        return ['.json']

    def parse_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Parse JSON file and yield records.

        Args:
            file_path: Path to JSON file

        Yields:
            Dictionary with JSON record data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                # Handle different JSON structures
                if isinstance(data, list):
                    # Array of records
                    for record in data:
                        yield record
                elif isinstance(data, dict):
                    # Single record or nested structure
                    if 'data' in data and isinstance(data['data'], list):
                        # Common format: {"data": [...]}
                        for record in data['data']:
                            yield record
                    else:
                        # Single record
                        yield data
                else:
                    raise ImportError(f"Unsupported JSON structure in {file_path}")

        except json.JSONDecodeError as e:
            raise ImportError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ImportError(f"Failed to parse JSON file {file_path}: {e}")