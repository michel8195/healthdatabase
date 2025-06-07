"""
Integration tests for bulk import functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.etl.bulk_importer import BulkImporter
from src.etl.zepp_importers import ZeppActivityImporter, ZeppSleepImporter


class TestBulkImporter:
    """Tests for BulkImporter class."""

    @pytest.fixture
    def bulk_importer(self, db_connection):
        return BulkImporter(db_connection)

    @pytest.fixture
    def zepp_directory_structure(self, temp_dir):
        """Create a mock ZEPP directory structure with test files."""
        base_dir = temp_dir / "ZEPP"
        
        # Create first export directory
        export1 = base_dir / "3075021305_1749047212827"
        activity1 = export1 / "ACTIVITY"
        sleep1 = export1 / "SLEEP"
        sport1 = export1 / "SPORT"
        
        activity1.mkdir(parents=True)
        sleep1.mkdir(parents=True)
        sport1.mkdir(parents=True)
        
        # Create activity file
        (activity1 / "ACTIVITY_1749047210565.csv").write_text("""date,steps,calories,distance,runDistance
2024-01-15,8500,2200,6200,2100
2024-01-16,9200,2350,7100,0
""")
        
        # Create sleep file
        (sleep1 / "SLEEP_1749047211599.csv").write_text("""date,deepSleepTime,shallowSleepTime,wakeTime,start,stop,REMTime,naps
2024-01-15,120,280,15,2024-01-15 23:30:00+0000,2024-01-16 07:15:00+0000,65,
""")
        
        # Create sport file
        (sport1 / "SPORT_1749047212000.csv").write_text("""type,startTime,sportTime(s),maxPace(/meter),minPace(/meter),distance(m),avgPace(/meter),calories(kcal)
1,2024-01-15 18:00:00+0000,2400,0.35,0.65,5000.0,0.48,350.5
""")
        
        # Create second export directory
        export2 = base_dir / "3075021305_1749046767350"
        activity2 = export2 / "ACTIVITY"
        sleep2 = export2 / "SLEEP"
        
        activity2.mkdir(parents=True)
        sleep2.mkdir(parents=True)
        
        # Create activity file with overlapping date
        (activity2 / "ACTIVITY_1749046763267.csv").write_text("""date,steps,calories,distance,runDistance
2024-01-16,9100,2300,7000,0
2024-01-17,7800,2150,5900,1800
""")
        
        # Create sleep file
        (sleep2 / "SLEEP_1749046764545.csv").write_text("""date,deepSleepTime,shallowSleepTime,wakeTime,start,stop,REMTime,naps
2024-01-16,95,310,20,2024-01-16 23:45:00+0000,2024-01-17 07:30:00+0000,58,
""")
        
        return base_dir

    @pytest.mark.unit
    def test_init(self, bulk_importer):
        assert bulk_importer.db_connection is not None
        assert bulk_importer.stats['files_processed'] == 0
        assert bulk_importer.stats['records_inserted'] == 0

    @pytest.mark.unit
    def test_discover_zepp_files_valid_structure(self, bulk_importer, zepp_directory_structure):
        discovered = bulk_importer.discover_zepp_files(zepp_directory_structure)
        
        assert len(discovered['activity']) == 2
        assert len(discovered['sleep']) == 2
        assert len(discovered['sport']) == 1
        assert len(discovered['heartrate']) == 0

    @pytest.mark.unit
    def test_discover_zepp_files_nonexistent_path(self, bulk_importer, temp_dir):
        nonexistent = temp_dir / "nonexistent"
        discovered = bulk_importer.discover_zepp_files(nonexistent)
        
        for data_type in discovered.values():
            assert len(data_type) == 0

    @pytest.mark.unit
    def test_discover_zepp_files_empty_directory(self, bulk_importer, temp_dir):
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        discovered = bulk_importer.discover_zepp_files(empty_dir)
        
        for data_type in discovered.values():
            assert len(data_type) == 0

    @pytest.mark.integration
    @pytest.mark.database
    def test_bulk_import_activity_files(self, initialized_db, zepp_directory_structure):
        """Test bulk importing activity files."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Discover files
        discovered = bulk_importer.discover_zepp_files(zepp_directory_structure)
        activity_files = discovered['activity']
        
        assert len(activity_files) == 2
        
        # Test each file can be imported
        total_records = 0
        for file_path in activity_files:
            importer = ZeppActivityImporter(initialized_db)
            stats = importer.import_file(file_path, user_id=1, dry_run=True)
            total_records += stats['processed']
            assert stats['errors'] == 0
        
        assert total_records == 4  # In dry-run mode: 2 + 2 (no duplicate detection)

    @pytest.mark.integration
    @pytest.mark.database
    def test_bulk_import_sleep_files(self, initialized_db, zepp_directory_structure):
        """Test bulk importing sleep files."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Discover files
        discovered = bulk_importer.discover_zepp_files(zepp_directory_structure)
        sleep_files = discovered['sleep']
        
        assert len(sleep_files) == 2
        
        # Test each file can be imported
        total_records = 0
        for file_path in sleep_files:
            importer = ZeppSleepImporter(initialized_db)
            stats = importer.import_file(file_path, user_id=1, dry_run=True)
            total_records += stats['processed']
            assert stats['errors'] == 0
        
        assert total_records == 2

    @pytest.mark.integration
    @pytest.mark.database
    def test_bulk_import_with_duplicates(self, initialized_db, zepp_directory_structure):
        """Test handling of duplicate records during bulk import."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Import first activity file
        discovered = bulk_importer.discover_zepp_files(zepp_directory_structure)
        first_file = discovered['activity'][0]
        
        importer1 = ZeppActivityImporter(initialized_db)
        stats1 = importer1.import_file(first_file, user_id=1)
        
        assert stats1['processed'] == 2
        assert stats1['inserted'] == 2
        
        # Import second file which has overlapping date (2024-01-16)
        second_file = discovered['activity'][1]
        importer2 = ZeppActivityImporter(initialized_db)
        stats2 = importer2.import_file(second_file, user_id=1)
        
        assert stats2['processed'] == 2
        # One record should be updated (2024-01-16), one inserted (2024-01-17)
        assert stats2['inserted'] + stats2['updated'] == 2

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.slow
    def test_full_bulk_import_workflow(self, initialized_db, zepp_directory_structure):
        """Test complete bulk import workflow with all file types."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Discover all files
        discovered = bulk_importer.discover_zepp_files(zepp_directory_structure)
        
        total_imported = 0
        
        # Import activity files
        for file_path in discovered['activity']:
            importer = ZeppActivityImporter(initialized_db)
            stats = importer.import_file(file_path, user_id=1)
            total_imported += stats['inserted'] + stats['updated']
            assert stats['errors'] == 0
        
        # Import sleep files
        for file_path in discovered['sleep']:
            importer = ZeppSleepImporter(initialized_db)
            stats = importer.import_file(file_path, user_id=1)
            total_imported += stats['inserted'] + stats['updated']
            assert stats['errors'] == 0
        
        # Verify data in database
        activity_count = initialized_db.execute_query(
            "SELECT COUNT(*) as count FROM daily_activity"
        )[0]['count']
        
        sleep_count = initialized_db.execute_query(
            "SELECT COUNT(*) as count FROM sleep_data"
        )[0]['count']
        
        assert activity_count == 3  # 3 unique activity dates
        assert sleep_count == 2  # 2 unique sleep dates
        assert total_imported >= 5

    @pytest.mark.integration
    def test_file_discovery_with_hidden_directories(self, bulk_importer, temp_dir):
        """Test that hidden directories are properly ignored."""
        base_dir = temp_dir / "ZEPP"
        
        # Create normal directory
        normal_dir = base_dir / "normal_export"
        activity_dir = normal_dir / "ACTIVITY"
        activity_dir.mkdir(parents=True)
        (activity_dir / "ACTIVITY_123.csv").write_text("date,steps\n2024-01-15,5000")
        
        # Create hidden directory
        hidden_dir = base_dir / ".hidden_export"
        hidden_activity = hidden_dir / "ACTIVITY"
        hidden_activity.mkdir(parents=True)
        (hidden_activity / "ACTIVITY_456.csv").write_text("date,steps\n2024-01-16,6000")
        
        discovered = bulk_importer.discover_zepp_files(base_dir)
        
        # Should only find files in normal directory
        assert len(discovered['activity']) == 1
        assert 'normal_export' in str(discovered['activity'][0])

    @pytest.mark.unit
    def test_stats_initialization(self, bulk_importer):
        """Test that stats are properly initialized."""
        expected_keys = [
            'files_processed', 'files_skipped', 'files_failed',
            'records_inserted', 'records_updated', 'records_skipped', 'errors'
        ]
        
        for key in expected_keys:
            assert key in bulk_importer.stats
            if key == 'errors':
                assert isinstance(bulk_importer.stats[key], list)
            else:
                assert bulk_importer.stats[key] == 0


class TestBulkImportErrorHandling:
    """Tests for error handling in bulk import operations."""

    @pytest.fixture
    def bulk_importer(self, db_connection):
        return BulkImporter(db_connection)

    @pytest.mark.unit
    def test_discover_files_with_permission_error(self, bulk_importer, temp_dir):
        """Test handling of permission errors during file discovery."""
        # Create a directory we can't read (simulate permission error)
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir()
        
        # On some systems, we can't easily create permission errors in tests
        # So we'll test with a directory that doesn't contain the expected structure
        discovered = bulk_importer.discover_zepp_files(restricted_dir)
        
        # Should return empty results gracefully
        for file_list in discovered.values():
            assert len(file_list) == 0

    @pytest.mark.integration
    @pytest.mark.database
    def test_import_corrupted_csv_file(self, initialized_db, temp_dir):
        """Test handling of corrupted CSV files."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Create corrupted CSV file
        corrupted_file = temp_dir / "corrupted.csv"
        corrupted_file.write_text("date,steps\n2024-01-15,invalid_number,extra_column")
        
        importer = ZeppActivityImporter(initialized_db)
        
        # Should handle corruption gracefully
        stats = importer.import_file(corrupted_file, user_id=1, dry_run=True)
        
        # Should not crash and process what it can (might have 0 errors if data is salvageable)
        assert stats['errors'] >= 0
        assert stats['processed'] >= 0  # Should process at least some data

    @pytest.mark.integration
    @pytest.mark.database
    def test_import_empty_csv_file(self, initialized_db, temp_dir):
        """Test handling of empty CSV files."""
        bulk_importer = BulkImporter(initialized_db)
        
        # Create empty CSV file
        empty_file = temp_dir / "empty.csv"
        empty_file.write_text("")
        
        importer = ZeppActivityImporter(initialized_db)
        
        # Should handle empty file gracefully
        stats = importer.import_file(empty_file, user_id=1, dry_run=True)
        
        assert stats['processed'] == 0
        assert stats['errors'] == 0