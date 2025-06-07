"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from datetime import datetime, date

from src.database.connection import DatabaseConnection
from src.database.models import get_all_models
from src.database.schema import SchemaManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_db_path(temp_dir: Path) -> Path:
    """Create a temporary database file path."""
    return temp_dir / "test_health.db"


@pytest.fixture
def db_connection(test_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    """Create a test database connection."""
    connection = DatabaseConnection(str(test_db_path))
    yield connection
    # DatabaseConnection doesn't need explicit closing as it uses context managers


@pytest.fixture
def initialized_db(db_connection: DatabaseConnection) -> DatabaseConnection:
    """Create a database with all tables initialized and a default user."""
    schema_manager = SchemaManager(db_connection)
    models = get_all_models()
    
    for model in models.values():
        schema_manager.create_table(model)
    
    # Create a default test user that integration tests can use
    with db_connection.get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (user_id, name, email, timezone) VALUES (?, ?, ?, ?)",
            ("test_user", "Test User", "test@example.com", "America/Sao_Paulo")
        )
    
    return db_connection


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        'user_id': 'test_user_123',
        'name': 'Test User',
        'email': 'test@example.com',
        'timezone': 'America/Sao_Paulo'
    }


@pytest.fixture
def sample_activity_data() -> Dict[str, Any]:
    """Sample activity data for testing."""
    return {
        'user_id': 1,
        'date': '2024-01-15',
        'steps': 8500,
        'calories': 2200.5,
        'distance': 6.2,
        'run_distance': 2.1,
        'active_minutes': 45,
        'data_source': 'zepp'
    }


@pytest.fixture
def sample_sleep_data() -> Dict[str, Any]:
    """Sample sleep data for testing."""
    return {
        'user_id': 1,
        'date': '2024-01-15',
        'sleep_start': '2024-01-15 23:30:00+00:00',
        'sleep_end': '2024-01-16 07:15:00+00:00',
        'total_sleep_minutes': 465,
        'deep_sleep_minutes': 120,
        'light_sleep_minutes': 280,
        'rem_sleep_minutes': 65,
        'wake_minutes': 15,
        'sleep_efficiency': 92.5,
        'data_source': 'zepp'
    }


@pytest.fixture
def sample_sport_data() -> Dict[str, Any]:
    """Sample sport data for testing."""
    return {
        'user_id': 1,
        'start_time': '2024-01-15 18:00:00+00:00',
        'sport_type': 1,
        'duration_seconds': 2400,
        'distance_meters': 5000.0,
        'calories': 350.5,
        'avg_pace_per_meter': 0.48,
        'max_pace_per_meter': 0.35,
        'min_pace_per_meter': 0.65,
        'data_source': 'zepp'
    }


@pytest.fixture
def sample_csv_activity_content() -> str:
    """Sample CSV content for activity data."""
    return """date,steps,calories,distance,runDistance
2024-01-15,8500,2200,6200,2100
2024-01-16,9200,2350,7100,0
2024-01-17,7800,2150,5900,1800
"""


@pytest.fixture
def sample_csv_sleep_content() -> str:
    """Sample CSV content for sleep data."""
    return """date,deepSleepTime,shallowSleepTime,wakeTime,start,stop,REMTime,naps
2024-01-15,120,280,15,2024-01-15 23:30:00+0000,2024-01-16 07:15:00+0000,65,
2024-01-16,95,310,20,2024-01-16 23:45:00+0000,2024-01-17 07:30:00+0000,58,
"""


@pytest.fixture
def test_csv_file(temp_dir: Path, sample_csv_activity_content: str) -> Path:
    """Create a test CSV file with activity data."""
    csv_file = temp_dir / "test_activity.csv"
    csv_file.write_text(sample_csv_activity_content)
    return csv_file


@pytest.fixture
def test_sleep_csv_file(temp_dir: Path, sample_csv_sleep_content: str) -> Path:
    """Create a test CSV file with sleep data."""
    csv_file = temp_dir / "test_sleep.csv"
    csv_file.write_text(sample_csv_sleep_content)
    return csv_file