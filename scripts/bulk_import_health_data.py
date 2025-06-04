#!/usr/bin/env python3
"""
Bulk import health data from multiple files with duplicate handling.

This script can process multiple ZEPP data export directories and handle
duplicate records using different strategies.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl import bulk_import_zepp_data  # pylint: disable=wrong-import-position


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def main():
    """Main function for bulk import script."""
    parser = argparse.ArgumentParser(
        description='Bulk import health data from multiple files'
    )

    parser.add_argument(
        'data_path',
        help='Path to directory containing health data files (e.g., raw/ZEPP/)'
    )

    parser.add_argument(
        '--duplicate-strategy',
        choices=['update', 'skip', 'error'],
        default='update',
        help='How to handle duplicate records (default: update)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without importing data'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate data path
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"Data path does not exist: {data_path}")
        sys.exit(1)

    if not data_path.is_dir():
        logger.error(f"Data path is not a directory: {data_path}")
        sys.exit(1)

    # Log configuration
    logger.info("Starting bulk import with configuration:")
    logger.info(f"  Data path: {data_path}")
    logger.info(f"  Duplicate strategy: {args.duplicate_strategy}")
    logger.info(f"  Dry run: {args.dry_run}")

    try:
        # Perform bulk import
        stats = bulk_import_zepp_data(
            base_path=str(data_path),
            duplicate_strategy=args.duplicate_strategy,
            dry_run=args.dry_run
        )

        # Print summary
        print("\n" + "="*50)
        print("BULK IMPORT SUMMARY")
        print("="*50)
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files failed: {stats['files_failed']}")
        print(f"Records inserted: {stats['records_inserted']}")
        print(f"Records updated: {stats['records_updated']}")
        print(f"Records skipped: {stats['records_skipped']}")

        if stats['errors']:
            print(f"\nErrors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")

        if args.dry_run:
            print("\n⚠️  This was a dry run - no data was actually imported")
        else:
            print("\n✅ Bulk import completed successfully!")

    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()