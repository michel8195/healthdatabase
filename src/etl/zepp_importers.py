"""
Zepp-specific importers for health data.

This module contains importers specifically designed to handle
Zepp device data formats for various health metrics.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from src.etl.base_importer import CSVImporter, DataValidationError
from src.database.models import ActivityModel, SleepModel, SportModel
from src.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

# GMT-3 timezone (UTC-3)
GMT_MINUS_3 = timezone(timedelta(hours=-3))


class ZeppActivityImporter(CSVImporter):
    """Importer for Zepp activity data (steps, calories, distance)."""

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize Zepp activity importer."""
        super().__init__(db_connection, ActivityModel())

    def get_data_source_name(self) -> str:
        """Return the data source name."""
        return 'zepp'

    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Zepp activity record to standard format.

        Expected Zepp CSV format:
        date,steps,calories,distance,runDistance
        """
        try:
            # Handle missing or None values
            steps = self._safe_int_conversion(raw_record.get('steps'))
            calories = self._safe_float_conversion(raw_record.get('calories'))
            distance = self._safe_float_conversion(raw_record.get('distance'))
            run_distance = self._safe_float_conversion(
                raw_record.get('runDistance', 0)
            )

            return {
                'date': raw_record['date'],
                'steps': steps,
                'calories': calories,
                'distance': distance,
                'run_distance': run_distance,
                'active_minutes': 0  # Not provided in current Zepp data
            }

        except KeyError as e:
            raise DataValidationError(f"Missing required field: {e}")
        except ValueError as e:
            raise DataValidationError(f"Invalid data format: {e}")

    def _safe_int_conversion(self, value: Any) -> int:
        """Safely convert value to integer."""
        if value is None or value == '':
            return 0
        try:
            return int(float(value))  # Handle decimal strings
        except (ValueError, TypeError):
            return 0

    def _safe_float_conversion(self, value: Any) -> float:
        """Safely convert value to float."""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


class ZeppSleepImporter(CSVImporter):
    """Importer for Zepp sleep data."""

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize Zepp sleep importer."""
        super().__init__(db_connection, SleepModel())

    def get_data_source_name(self) -> str:
        """Return the data source name."""
        return 'zepp'

    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Zepp sleep record to standard format.

        Expected Zepp CSV format:
        date,deepSleepTime,shallowSleepTime,wakeTime,start,stop,REMTime,naps
        """
        try:
            # Get basic sleep metrics (in minutes)
            deep_sleep = self._safe_int_conversion(
                raw_record.get('deepSleepTime', 0)
            )
            light_sleep = self._safe_int_conversion(
                raw_record.get('shallowSleepTime', 0)
            )
            wake_time = self._safe_int_conversion(
                raw_record.get('wakeTime', 0)
            )
            rem_sleep = self._safe_int_conversion(
                raw_record.get('REMTime', 0)
            )

            # Parse sleep start/end times
            sleep_start = self._parse_sleep_timestamp(
                raw_record.get('start')
            )
            sleep_end = self._parse_sleep_timestamp(
                raw_record.get('stop')
            )

            # Calculate total sleep time
            total_sleep = deep_sleep + light_sleep + rem_sleep

            # Calculate sleep efficiency if we have valid sleep window
            sleep_efficiency = 0.0
            if sleep_start and sleep_end and sleep_start != sleep_end:
                total_time_in_bed = (sleep_end - sleep_start).total_seconds() / 60
                if total_time_in_bed > 0:
                    sleep_efficiency = (total_sleep / total_time_in_bed) * 100
                    sleep_efficiency = min(100.0, max(0.0, sleep_efficiency))

            return {
                'date': raw_record['date'],
                'sleep_start': sleep_start,
                'sleep_end': sleep_end,
                'total_sleep_minutes': total_sleep,
                'deep_sleep_minutes': deep_sleep,
                'light_sleep_minutes': light_sleep,
                'rem_sleep_minutes': rem_sleep,
                'wake_minutes': wake_time,
                'sleep_efficiency': sleep_efficiency,
                'naps_data': raw_record.get('naps')  # Store as-is for now
            }

        except KeyError as e:
            raise DataValidationError(f"Missing required field: {e}")
        except ValueError as e:
            raise DataValidationError(f"Invalid data format: {e}")

    def _safe_int_conversion(self, value: Any) -> int:
        """Safely convert value to integer."""
        if value is None or value == '':
            return 0
        try:
            return int(float(value))  # Handle decimal strings
        except (ValueError, TypeError):
            return 0

    def _parse_sleep_timestamp(self, timestamp_str: Any) -> Optional[datetime]:
        """
        Parse Zepp sleep timestamp and convert to GMT-3.

        Args:
            timestamp_str: Timestamp string from Zepp (in UTC)

        Returns:
            Parsed datetime object converted to GMT-3 or None if invalid
        """
        if not timestamp_str or timestamp_str.strip() == '':
            return None

        try:
            # Handle Zepp timestamp format: "2023-02-18 02:13:00+0000"
            clean_timestamp = timestamp_str.replace('+0000', '+00:00')
            utc_datetime = datetime.fromisoformat(clean_timestamp)

            # Convert from UTC to GMT-3
            gmt3_datetime = utc_datetime.astimezone(GMT_MINUS_3)

            logger.debug(
                f"Converted timestamp {timestamp_str} from UTC to GMT-3: "
                f"{utc_datetime} -> {gmt3_datetime}"
            )

            return gmt3_datetime
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None


class ZeppSportImporter(CSVImporter):
    """Importer for Zepp sport/exercise data."""

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize Zepp sport importer."""
        super().__init__(db_connection, SportModel())

    def get_data_source_name(self) -> str:
        """Return the data source name."""
        return 'zepp'

    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Zepp sport record to standard format.

        Expected Zepp CSV format:
        type,startTime,sportTime(s),maxPace(/meter),minPace(/meter),
        distance(m),avgPace(/meter),calories(kcal)
        """
        try:
            # Parse start time with timezone conversion to GMT-3
            start_time = self._parse_sport_timestamp(
                raw_record.get('startTime')
            )

            # Get sport metrics
            duration_seconds = self._safe_int_conversion(
                raw_record.get('sportTime(s)', 0)
            )
            distance_meters = self._safe_float_conversion(
                raw_record.get('distance(m)', 0)
            )
            calories = self._safe_float_conversion(
                raw_record.get('calories(kcal)', 0)
            )

            # Get pace metrics - handle -1.0 as invalid/null values
            avg_pace = self._safe_pace_conversion(
                raw_record.get('avgPace(/meter)', 0)
            )
            max_pace = self._safe_pace_conversion(
                raw_record.get('maxPace(/meter)', 0)
            )
            min_pace = self._safe_pace_conversion(
                raw_record.get('minPace(/meter)', 0)
            )

            return {
                'start_time': start_time,
                'sport_type': int(raw_record['type']),
                'duration_seconds': duration_seconds,
                'distance_meters': distance_meters,
                'calories': calories,
                'avg_pace_per_meter': avg_pace,
                'max_pace_per_meter': max_pace,
                'min_pace_per_meter': min_pace
            }

        except KeyError as e:
            raise DataValidationError(f"Missing required field: {e}")
        except ValueError as e:
            raise DataValidationError(f"Invalid data format: {e}")

    def _safe_int_conversion(self, value: Any) -> int:
        """Safely convert value to integer."""
        if value is None or value == '':
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _safe_float_conversion(self, value: Any) -> float:
        """Safely convert value to float."""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_pace_conversion(self, value: Any) -> float:
        """Safely convert pace value, treating -1.0 as invalid."""
        if value is None or value == '':
            return 0.0
        try:
            float_val = float(value)
            if float_val == -1.0:
                return 0.0
            return float_val
        except (ValueError, TypeError):
            return 0.0

    def _parse_sport_timestamp(self, timestamp_str: Any) -> Optional[datetime]:
        """
        Parse Zepp sport timestamp and convert to GMT-3.

        Args:
            timestamp_str: Timestamp string from Zepp (in UTC)

        Returns:
            Parsed datetime object converted to GMT-3 or None if invalid
        """
        if not timestamp_str or timestamp_str.strip() == '':
            return None

        try:
            # Handle Zepp timestamp format: "2025-05-18 15:18:00+0000"
            clean_timestamp = timestamp_str.replace('+0000', '+00:00')
            utc_datetime = datetime.fromisoformat(clean_timestamp)

            # Convert from UTC to GMT-3
            gmt3_datetime = utc_datetime.astimezone(GMT_MINUS_3)

            logger.debug(
                f"Converted sport timestamp {timestamp_str} from UTC to GMT-3: "
                f"{utc_datetime} -> {gmt3_datetime}"
            )

            return gmt3_datetime
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None


def create_zepp_importer(data_type: str,
                        db_connection: DatabaseConnection) -> CSVImporter:
    """
    Factory function to create appropriate Zepp importer.

    Args:
        data_type: Type of data ('activity' or 'sleep')
        db_connection: Database connection instance

    Returns:
        Appropriate importer instance

    Raises:
        ValueError: If data_type is not supported
    """
    importers = {
        'activity': ZeppActivityImporter,
        'sleep': ZeppSleepImporter,
        'sport': ZeppSportImporter
    }

    if data_type not in importers:
        available = ', '.join(importers.keys())
        raise ValueError(f"Unsupported data type '{data_type}'. "
                        f"Available: {available}")

    return importers[data_type](db_connection)