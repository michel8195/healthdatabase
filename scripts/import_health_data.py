#!/usr/bin/env python3
"""
Health data import script.

This script can import various types of health data (activity, sleep, etc.)
from different sources using the modular importer system.
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager
from src.etl.zepp_importers import create_zepp_importer
from src.utils.logging_config import setup_logging


def import_data(data_type: str, source: str, file_path: Path,
               dry_run: bool = False) -> Dict[str, Any]:
    """
    Import health data from a file.

    Args:
        data_type: Type of data ('activity', 'sleep', 'sport', or 'heart_rate')
        source: Data source ('zepp', etc.)
        file_path: Path to the data file
        dry_run: If True, validate but don't import

    Returns:
        Import statistics
    """
    logger = logging.getLogger(__name__)

    # Setup database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "health_data.db"

    db_conn = DatabaseConnection(str(db_path))
    schema_manager = SchemaManager(db_conn)

    try:
        # Ensure default user exists
        user_id = schema_manager.ensure_default_user()
        logger.info(f"Using user ID: {user_id}")

        # Create appropriate importer
        if source.lower() == 'zepp':
            importer = create_zepp_importer(data_type, db_conn)
        else:
            raise ValueError(f"Unsupported source: {source}")

        # Import data
        logger.info(f"Importing {data_type} data from {file_path}")
        stats = importer.import_file(file_path, user_id=user_id, dry_run=dry_run)

        return stats

    finally:
        # DatabaseConnection handles its own cleanup
        pass


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Import health data from various sources"
    )
    parser.add_argument(
        "data_type",
        choices=['activity', 'sleep', 'sport', 'heart_rate'],
        help="Type of data to import"
    )
    parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the data file to import"
    )
    parser.add_argument(
        "--source",
        default="zepp",
        choices=['zepp'],
        help="Data source (default: zepp)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data but don't import"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Health Data Import ===")
        logger.info(f"Data type: {args.data_type}")
        logger.info(f"Source: {args.source}")
        logger.info(f"File: {args.file_path}")
        logger.info(f"Dry run: {args.dry_run}")

        # Validate file exists
        if not args.file_path.exists():
            logger.error(f"File not found: {args.file_path}")
            sys.exit(1)

        # Import data
        stats = import_data(
            args.data_type,
            args.source,
            args.file_path,
            dry_run=args.dry_run
        )

        # Display results
        logger.info("\n=== Import Results ===")
        logger.info(f"Processed: {stats['processed']} records")
        logger.info(f"Inserted: {stats['inserted']} records")
        logger.info(f"Updated: {stats['updated']} records")
        logger.info(f"Errors: {stats['errors']} records")

        if args.dry_run:
            logger.info("✓ Dry run completed - no data was imported")
        else:
            logger.info("✅ Import completed successfully!")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Import interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()