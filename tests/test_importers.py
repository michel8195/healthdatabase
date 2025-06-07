"""
Tests for ETL importers and data transformation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from src.etl.base_importer import BaseImporter, CSVImporter, DataValidationError, ImportError
from src.etl.zepp_importers import (
    ZeppActivityImporter, ZeppSleepImporter, ZeppSportImporter,
    create_zepp_importer, GMT_MINUS_3
)
from src.database.models import ActivityModel, SleepModel, SportModel


class TestBaseImporter:
    """Tests for BaseImporter base class."""

    @pytest.fixture
    def mock_model(self):
        model = Mock()
        model.get_table_name.return_value = "test_table"
        model.validate_data.return_value = {"id": 1, "data": "test"}
        return model

    @pytest.fixture
    def mock_db_connection(self):
        return Mock()

    @pytest.fixture
    def test_importer(self, mock_db_connection, mock_model):
        class TestImporter(BaseImporter):
            def get_data_source_name(self):
                return "test_source"
            
            def get_supported_file_types(self):
                return [".csv"]
            
            def parse_file(self, file_path):
                yield {"test": "data"}
            
            def transform_record(self, raw_record):
                return raw_record

        return TestImporter(mock_db_connection, mock_model)

    @pytest.mark.unit
    def test_validate_file_exists(self, test_importer, test_csv_file):
        assert test_importer.validate_file(test_csv_file) is True

    @pytest.mark.unit
    def test_validate_file_not_exists(self, test_importer, temp_dir):
        non_existent = temp_dir / "not_exist.csv"
        assert test_importer.validate_file(non_existent) is False

    @pytest.mark.unit
    def test_validate_file_wrong_extension(self, test_importer, temp_dir):
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("test")
        assert test_importer.validate_file(txt_file) is False


class TestCSVImporter:
    """Tests for CSVImporter base class."""

    @pytest.fixture
    def csv_importer(self, db_connection):
        model = Mock()
        model.get_table_name.return_value = "test_table"
        model.validate_data.side_effect = lambda x: x  # Pass through

        class TestCSVImporter(CSVImporter):
            def get_data_source_name(self):
                return "test"
            
            def transform_record(self, raw_record):
                return raw_record

        return TestCSVImporter(db_connection, model)

    @pytest.mark.unit
    def test_get_supported_file_types(self, csv_importer):
        assert csv_importer.get_supported_file_types() == ['.csv']

    @pytest.mark.unit
    def test_parse_file_valid_csv(self, csv_importer, test_csv_file):
        records = list(csv_importer.parse_file(test_csv_file))
        assert len(records) == 3
        assert records[0]['date'] == '2024-01-15'
        assert records[0]['steps'] == '8500'

    @pytest.mark.unit
    def test_parse_file_empty_rows_skipped(self, csv_importer, temp_dir):
        csv_content = """date,steps
2024-01-15,8500

2024-01-16,9200
"""
        csv_file = temp_dir / "test_with_empty.csv"
        csv_file.write_text(csv_content)
        
        records = list(csv_importer.parse_file(csv_file))
        assert len(records) == 2  # Empty row skipped

    @pytest.mark.unit
    def test_parse_file_nonexistent(self, csv_importer, temp_dir):
        non_existent = temp_dir / "not_exist.csv"
        with pytest.raises(ImportError, match="Failed to parse CSV file"):
            list(csv_importer.parse_file(non_existent))


class TestZeppActivityImporter:
    """Tests for ZeppActivityImporter."""

    @pytest.fixture
    def activity_importer(self, db_connection):
        return ZeppActivityImporter(db_connection)

    @pytest.mark.unit
    def test_get_data_source_name(self, activity_importer):
        assert activity_importer.get_data_source_name() == 'zepp'

    @pytest.mark.unit
    def test_transform_record_valid(self, activity_importer):
        raw_record = {
            'date': '2024-01-15',
            'steps': '8500',
            'calories': '2200.5',
            'distance': '6200',
            'runDistance': '2100'
        }
        
        transformed = activity_importer.transform_record(raw_record)
        
        assert transformed['date'] == '2024-01-15'
        assert transformed['steps'] == 8500
        assert transformed['calories'] == 2200.5
        assert transformed['distance'] == 6200.0
        assert transformed['run_distance'] == 2100.0
        assert transformed['active_minutes'] == 0

    @pytest.mark.unit
    def test_transform_record_missing_optional_fields(self, activity_importer):
        raw_record = {
            'date': '2024-01-15',
            'steps': '8500',
            'calories': '2200'
        }
        
        transformed = activity_importer.transform_record(raw_record)
        
        assert transformed['distance'] == 0.0
        assert transformed['run_distance'] == 0.0

    @pytest.mark.unit
    def test_transform_record_empty_values(self, activity_importer):
        raw_record = {
            'date': '2024-01-15',
            'steps': '',
            'calories': None,
            'distance': '6200'
        }
        
        transformed = activity_importer.transform_record(raw_record)
        
        assert transformed['steps'] == 0
        assert transformed['calories'] == 0.0
        assert transformed['distance'] == 6200.0

    @pytest.mark.unit
    def test_transform_record_missing_required_field(self, activity_importer):
        raw_record = {
            'steps': '8500',
            'calories': '2200'
            # Missing 'date'
        }
        
        with pytest.raises(DataValidationError, match="Missing required field"):
            activity_importer.transform_record(raw_record)

    @pytest.mark.unit
    def test_safe_int_conversion(self, activity_importer):
        assert activity_importer._safe_int_conversion('123') == 123
        assert activity_importer._safe_int_conversion('123.5') == 123
        assert activity_importer._safe_int_conversion('') == 0
        assert activity_importer._safe_int_conversion(None) == 0
        assert activity_importer._safe_int_conversion('invalid') == 0

    @pytest.mark.unit
    def test_safe_float_conversion(self, activity_importer):
        assert activity_importer._safe_float_conversion('123.5') == 123.5
        assert activity_importer._safe_float_conversion('123') == 123.0
        assert activity_importer._safe_float_conversion('') == 0.0
        assert activity_importer._safe_float_conversion(None) == 0.0
        assert activity_importer._safe_float_conversion('invalid') == 0.0


class TestZeppSleepImporter:
    """Tests for ZeppSleepImporter."""

    @pytest.fixture
    def sleep_importer(self, db_connection):
        return ZeppSleepImporter(db_connection)

    @pytest.mark.unit
    def test_get_data_source_name(self, sleep_importer):
        assert sleep_importer.get_data_source_name() == 'zepp'

    @pytest.mark.unit
    def test_transform_record_valid(self, sleep_importer):
        raw_record = {
            'date': '2024-01-15',
            'deepSleepTime': '120',
            'shallowSleepTime': '280',
            'wakeTime': '15',
            'start': '2024-01-15 23:30:00+0000',
            'stop': '2024-01-16 07:15:00+0000',
            'REMTime': '65',
            'naps': ''
        }
        
        transformed = sleep_importer.transform_record(raw_record)
        
        assert transformed['date'] == '2024-01-15'
        assert transformed['deep_sleep_minutes'] == 120
        assert transformed['light_sleep_minutes'] == 280
        assert transformed['rem_sleep_minutes'] == 65
        assert transformed['wake_minutes'] == 15
        assert transformed['total_sleep_minutes'] == 465  # 120 + 280 + 65
        assert isinstance(transformed['sleep_start'], datetime)
        assert isinstance(transformed['sleep_end'], datetime)

    @pytest.mark.unit
    def test_transform_record_empty_timestamps(self, sleep_importer):
        raw_record = {
            'date': '2024-01-15',
            'deepSleepTime': '120',
            'shallowSleepTime': '280',
            'wakeTime': '15',
            'start': '',
            'stop': '',
            'REMTime': '65'
        }
        
        transformed = sleep_importer.transform_record(raw_record)
        
        assert transformed['sleep_start'] is None
        assert transformed['sleep_end'] is None
        assert transformed['sleep_efficiency'] == 0.0

    @pytest.mark.unit
    def test_parse_sleep_timestamp_valid(self, sleep_importer):
        timestamp_str = '2024-01-15 23:30:00+0000'
        result = sleep_importer._parse_sleep_timestamp(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == GMT_MINUS_3

    @pytest.mark.unit
    def test_parse_sleep_timestamp_invalid(self, sleep_importer):
        assert sleep_importer._parse_sleep_timestamp('') is None
        assert sleep_importer._parse_sleep_timestamp('invalid') is None
        assert sleep_importer._parse_sleep_timestamp(None) is None

    @pytest.mark.unit
    def test_sleep_efficiency_calculation(self, sleep_importer):
        raw_record = {
            'date': '2024-01-15',
            'deepSleepTime': '120',
            'shallowSleepTime': '280',
            'wakeTime': '15',
            'start': '2024-01-15 23:30:00+0000',
            'stop': '2024-01-16 07:30:00+0000',  # 8 hours total
            'REMTime': '65'
        }
        
        transformed = sleep_importer.transform_record(raw_record)
        
        total_sleep = 120 + 280 + 65  # 465 minutes
        total_time = 8 * 60  # 480 minutes
        expected_efficiency = (465 / 480) * 100  # ~96.875%
        
        assert abs(transformed['sleep_efficiency'] - expected_efficiency) < 0.1


class TestZeppSportImporter:
    """Tests for ZeppSportImporter."""

    @pytest.fixture
    def sport_importer(self, db_connection):
        return ZeppSportImporter(db_connection)

    @pytest.mark.unit
    def test_get_data_source_name(self, sport_importer):
        assert sport_importer.get_data_source_name() == 'zepp'

    @pytest.mark.unit
    def test_transform_record_valid(self, sport_importer):
        raw_record = {
            'type': '1',
            'startTime': '2024-01-15 18:00:00+0000',
            'sportTime(s)': '2400',
            'distance(m)': '5000.0',
            'calories(kcal)': '350.5',
            'avgPace(/meter)': '0.48',
            'maxPace(/meter)': '0.35',
            'minPace(/meter)': '0.65'
        }
        
        transformed = sport_importer.transform_record(raw_record)
        
        assert transformed['sport_type'] == 1
        assert transformed['duration_seconds'] == 2400
        assert transformed['distance_meters'] == 5000.0
        assert transformed['calories'] == 350.5
        assert transformed['avg_pace_per_meter'] == 0.48
        assert isinstance(transformed['start_time'], datetime)
        assert transformed['start_time'].tzinfo == GMT_MINUS_3

    @pytest.mark.unit
    def test_transform_record_invalid_pace_values(self, sport_importer):
        raw_record = {
            'type': '1',
            'startTime': '2024-01-15 18:00:00+0000',
            'sportTime(s)': '2400',
            'avgPace(/meter)': '-1.0',  # Invalid pace
            'maxPace(/meter)': '',     # Empty pace
            'minPace(/meter)': None    # None pace
        }
        
        transformed = sport_importer.transform_record(raw_record)
        
        assert transformed['avg_pace_per_meter'] == 0.0
        assert transformed['max_pace_per_meter'] == 0.0
        assert transformed['min_pace_per_meter'] == 0.0

    @pytest.mark.unit
    def test_parse_sport_timestamp(self, sport_importer):
        timestamp_str = '2024-01-15 18:00:00+0000'
        result = sport_importer._parse_sport_timestamp(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == GMT_MINUS_3

    @pytest.mark.unit
    def test_safe_pace_conversion(self, sport_importer):
        assert sport_importer._safe_pace_conversion('0.48') == 0.48
        assert sport_importer._safe_pace_conversion('-1.0') == 0.0
        assert sport_importer._safe_pace_conversion('') == 0.0
        assert sport_importer._safe_pace_conversion(None) == 0.0


class TestZeppImporterFactory:
    """Tests for create_zepp_importer factory function."""

    @pytest.mark.unit
    def test_create_activity_importer(self, db_connection):
        importer = create_zepp_importer('activity', db_connection)
        assert isinstance(importer, ZeppActivityImporter)

    @pytest.mark.unit
    def test_create_sleep_importer(self, db_connection):
        importer = create_zepp_importer('sleep', db_connection)
        assert isinstance(importer, ZeppSleepImporter)

    @pytest.mark.unit
    def test_create_sport_importer(self, db_connection):
        importer = create_zepp_importer('sport', db_connection)
        assert isinstance(importer, ZeppSportImporter)

    @pytest.mark.unit
    def test_create_invalid_importer(self, db_connection):
        with pytest.raises(ValueError, match="Unsupported data type 'invalid'"):
            create_zepp_importer('invalid', db_connection)


class TestIntegrationImport:
    """Integration tests for full import process."""

    @pytest.mark.integration
    @pytest.mark.database
    def test_activity_import_integration(self, initialized_db, test_csv_file):
        importer = ZeppActivityImporter(initialized_db)
        
        stats = importer.import_file(test_csv_file, user_id=1, dry_run=True)
        
        assert stats['processed'] == 3
        assert stats['errors'] == 0

    @pytest.mark.integration
    @pytest.mark.database
    def test_sleep_import_integration(self, initialized_db, test_sleep_csv_file):
        importer = ZeppSleepImporter(initialized_db)
        
        stats = importer.import_file(test_sleep_csv_file, user_id=1, dry_run=True)
        
        assert stats['processed'] == 2
        assert stats['errors'] == 0