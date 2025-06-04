"""
Database models for health data.

This module defines the database schema for various health data types
using a modular approach with separate tables for different data types.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Abstract base class for all data models."""

    @abstractmethod
    def get_table_name(self) -> str:
        """Return the table name for this model."""
        pass

    @abstractmethod
    def get_create_sql(self) -> str:
        """Return the SQL statement to create the table."""
        pass

    @abstractmethod
    def get_indexes_sql(self) -> List[str]:
        """Return SQL statements to create indexes."""
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize data before insertion."""
        pass


class UserModel(BaseModel):
    """Model for user information."""

    def get_table_name(self) -> str:
        return "users"

    def get_create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT,
            email TEXT,
            timezone TEXT DEFAULT 'UTC',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    def get_indexes_sql(self) -> List[str]:
        return [
            "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        ]

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user data."""
        required_fields = ['user_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")

        return {
            'user_id': str(data['user_id']),
            'name': data.get('name'),
            'email': data.get('email'),
            'timezone': data.get('timezone', 'UTC')
        }


class ActivityModel(BaseModel):
    """Model for daily activity data (steps, calories, distance)."""

    def get_table_name(self) -> str:
        return "daily_activity"

    def get_create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            steps INTEGER DEFAULT 0,
            calories REAL DEFAULT 0.0,
            distance REAL DEFAULT 0.0,
            run_distance REAL DEFAULT 0.0,
            active_minutes INTEGER DEFAULT 0,
            data_source TEXT NOT NULL DEFAULT 'zepp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date, data_source)
        )
        """

    def get_indexes_sql(self) -> List[str]:
        return [
            "CREATE INDEX IF NOT EXISTS idx_activity_user_date "
            "ON daily_activity(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_activity_date "
            "ON daily_activity(date)",
            "CREATE INDEX IF NOT EXISTS idx_activity_source "
            "ON daily_activity(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_activity_steps "
            "ON daily_activity(steps)"
        ]

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate activity data."""
        required_fields = ['user_id', 'date']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")

        # Parse date if it's a string
        date_val = data['date']
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_val}")

        return {
            'user_id': int(data['user_id']),
            'date': date_val,
            'steps': max(0, int(data.get('steps', 0))),
            'calories': max(0.0, float(data.get('calories', 0.0))),
            'distance': max(0.0, float(data.get('distance', 0.0))),
            'run_distance': max(0.0, float(data.get('run_distance', 0.0))),
            'active_minutes': max(0, int(data.get('active_minutes', 0))),
            'data_source': str(data.get('data_source', 'zepp'))
        }


class SleepModel(BaseModel):
    """Model for sleep data."""

    def get_table_name(self) -> str:
        return "sleep_data"

    def get_create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS sleep_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            sleep_start TIMESTAMP,
            sleep_end TIMESTAMP,
            total_sleep_minutes INTEGER DEFAULT 0,
            deep_sleep_minutes INTEGER DEFAULT 0,
            light_sleep_minutes INTEGER DEFAULT 0,
            rem_sleep_minutes INTEGER DEFAULT 0,
            wake_minutes INTEGER DEFAULT 0,
            sleep_efficiency REAL DEFAULT 0.0,
            naps_data TEXT,  -- JSON string for nap data
            data_source TEXT NOT NULL DEFAULT 'zepp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date, data_source)
        )
        """

    def get_indexes_sql(self) -> List[str]:
        return [
            "CREATE INDEX IF NOT EXISTS idx_sleep_user_date "
            "ON sleep_data(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_sleep_date "
            "ON sleep_data(date)",
            "CREATE INDEX IF NOT EXISTS idx_sleep_source "
            "ON sleep_data(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_sleep_total "
            "ON sleep_data(total_sleep_minutes)",
            "CREATE INDEX IF NOT EXISTS idx_sleep_start "
            "ON sleep_data(sleep_start)"
        ]

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sleep data."""
        required_fields = ['user_id', 'date']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")

        # Parse date if it's a string
        date_val = data['date']
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_val}")

        # Parse timestamps
        sleep_start = None
        sleep_end = None

        if data.get('sleep_start'):
            if isinstance(data['sleep_start'], str):
                try:
                    sleep_start = datetime.fromisoformat(data['sleep_start'].replace('+0000', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid sleep_start format: {data['sleep_start']}")
            else:
                sleep_start = data['sleep_start']

        if data.get('sleep_end'):
            if isinstance(data['sleep_end'], str):
                try:
                    sleep_end = datetime.fromisoformat(data['sleep_end'].replace('+0000', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid sleep_end format: {data['sleep_end']}")
            else:
                sleep_end = data['sleep_end']

        # Calculate total sleep if not provided
        total_sleep = data.get('total_sleep_minutes', 0)
        if not total_sleep and sleep_start and sleep_end:
            total_sleep = int((sleep_end - sleep_start).total_seconds() / 60)

        return {
            'user_id': int(data['user_id']),
            'date': date_val,
            'sleep_start': sleep_start,
            'sleep_end': sleep_end,
            'total_sleep_minutes': max(0, int(total_sleep)),
            'deep_sleep_minutes': max(0, int(data.get('deep_sleep_minutes', 0))),
            'light_sleep_minutes': max(0, int(data.get('light_sleep_minutes', 0))),
            'rem_sleep_minutes': max(0, int(data.get('rem_sleep_minutes', 0))),
            'wake_minutes': max(0, int(data.get('wake_minutes', 0))),
            'sleep_efficiency': max(0.0, min(100.0, float(data.get('sleep_efficiency', 0.0)))),
            'naps_data': data.get('naps_data'),
            'data_source': str(data.get('data_source', 'zepp'))
        }


class SportModel(BaseModel):
    """Model for sport/exercise data."""

    def get_table_name(self) -> str:
        return "sport_data"

    def get_create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS sport_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            sport_type INTEGER NOT NULL,
            duration_seconds INTEGER DEFAULT 0,
            distance_meters REAL DEFAULT 0.0,
            calories REAL DEFAULT 0.0,
            avg_pace_per_meter REAL DEFAULT 0.0,
            max_pace_per_meter REAL DEFAULT 0.0,
            min_pace_per_meter REAL DEFAULT 0.0,
            data_source TEXT NOT NULL DEFAULT 'zepp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """

    def get_indexes_sql(self) -> List[str]:
        return [
            "CREATE INDEX IF NOT EXISTS idx_sport_user_start "
            "ON sport_data(user_id, start_time)",
            "CREATE INDEX IF NOT EXISTS idx_sport_start_time "
            "ON sport_data(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_sport_type "
            "ON sport_data(sport_type)",
            "CREATE INDEX IF NOT EXISTS idx_sport_source "
            "ON sport_data(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_sport_duration "
            "ON sport_data(duration_seconds)",
            "CREATE INDEX IF NOT EXISTS idx_sport_distance "
            "ON sport_data(distance_meters)"
        ]

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sport data."""
        required_fields = ['user_id', 'start_time', 'sport_type']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")

        # Parse start time
        start_time = data['start_time']
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace('+0000', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid start_time format: {start_time}")

        return {
            'user_id': int(data['user_id']),
            'start_time': start_time,
            'sport_type': int(data['sport_type']),
            'duration_seconds': max(0, int(data.get('duration_seconds', 0))),
            'distance_meters': max(0.0, float(data.get('distance_meters', 0.0))),
            'calories': max(0.0, float(data.get('calories', 0.0))),
            'avg_pace_per_meter': float(data.get('avg_pace_per_meter', 0.0)),
            'max_pace_per_meter': float(data.get('max_pace_per_meter', 0.0)),
            'min_pace_per_meter': float(data.get('min_pace_per_meter', 0.0)),
            'data_source': str(data.get('data_source', 'zepp'))
        }


class HeartRateModel(BaseModel):
    """Model for heart rate data."""

    def get_table_name(self) -> str:
        return "heart_rate_data"

    def get_create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS heart_rate_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            heart_rate INTEGER NOT NULL,
            resting_hr INTEGER,
            max_hr INTEGER,
            data_source TEXT NOT NULL DEFAULT 'zepp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """

    def get_indexes_sql(self) -> List[str]:
        return [
            "CREATE INDEX IF NOT EXISTS idx_hr_user_timestamp ON heart_rate_data(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_hr_timestamp ON heart_rate_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_hr_source ON heart_rate_data(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_hr_value ON heart_rate_data(heart_rate)"
        ]

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate heart rate data."""
        required_fields = ['user_id', 'timestamp', 'heart_rate']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")

        # Parse timestamp
        timestamp_val = data['timestamp']
        if isinstance(timestamp_val, str):
            try:
                timestamp_val = datetime.fromisoformat(timestamp_val.replace('+0000', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {timestamp_val}")

        heart_rate = int(data['heart_rate'])
        if heart_rate < 30 or heart_rate > 220:  # Basic heart rate validation
            raise ValueError(f"Invalid heart rate value: {heart_rate}")

        return {
            'user_id': int(data['user_id']),
            'timestamp': timestamp_val,
            'heart_rate': heart_rate,
            'resting_hr': int(data['resting_hr']) if data.get('resting_hr') else None,
            'max_hr': int(data['max_hr']) if data.get('max_hr') else None,
            'data_source': str(data.get('data_source', 'zepp'))
        }


# Model registry for easy access
MODEL_REGISTRY = {
    'users': UserModel(),
    'activity': ActivityModel(),
    'sleep': SleepModel(),
    'sport': SportModel(),
    'heart_rate': HeartRateModel()
}


def get_model(model_name: str) -> BaseModel:
    """Get a model instance by name."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}")
    return MODEL_REGISTRY[model_name]


def get_all_models() -> Dict[str, BaseModel]:
    """Get all available models."""
    return MODEL_REGISTRY.copy()