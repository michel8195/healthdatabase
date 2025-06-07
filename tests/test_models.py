"""
Tests for database models and validation.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any

from src.database.models import (
    UserModel, ActivityModel, SleepModel, SportModel, HeartRateModel,
    get_model, get_all_models, MODEL_REGISTRY
)


class TestUserModel:
    """Tests for UserModel."""

    @pytest.fixture
    def user_model(self):
        return UserModel()

    @pytest.mark.unit
    def test_get_table_name(self, user_model):
        assert user_model.get_table_name() == "users"

    @pytest.mark.unit
    def test_get_create_sql(self, user_model):
        sql = user_model.get_create_sql()
        assert "CREATE TABLE IF NOT EXISTS users" in sql
        assert "user_id TEXT UNIQUE NOT NULL" in sql
        assert "timezone TEXT DEFAULT 'UTC'" in sql

    @pytest.mark.unit
    def test_get_indexes_sql(self, user_model):
        indexes = user_model.get_indexes_sql()
        assert len(indexes) == 2
        assert any("idx_users_user_id" in idx for idx in indexes)
        assert any("idx_users_email" in idx for idx in indexes)

    @pytest.mark.unit
    def test_validate_data_valid(self, user_model, sample_user_data):
        validated = user_model.validate_data(sample_user_data)
        assert validated['user_id'] == 'test_user_123'
        assert validated['name'] == 'Test User'
        assert validated['email'] == 'test@example.com'
        assert validated['timezone'] == 'America/Sao_Paulo'

    @pytest.mark.unit
    def test_validate_data_missing_required(self, user_model):
        with pytest.raises(ValueError, match="Required field 'user_id' is missing"):
            user_model.validate_data({})

    @pytest.mark.unit
    def test_validate_data_defaults(self, user_model):
        validated = user_model.validate_data({'user_id': 'test123'})
        assert validated['user_id'] == 'test123'
        assert validated['timezone'] == 'UTC'
        assert validated['name'] is None
        assert validated['email'] is None


class TestActivityModel:
    """Tests for ActivityModel."""

    @pytest.fixture
    def activity_model(self):
        return ActivityModel()

    @pytest.mark.unit
    def test_get_table_name(self, activity_model):
        assert activity_model.get_table_name() == "daily_activity"

    @pytest.mark.unit
    def test_get_create_sql(self, activity_model):
        sql = activity_model.get_create_sql()
        assert "CREATE TABLE IF NOT EXISTS daily_activity" in sql
        assert "UNIQUE(user_id, date, data_source)" in sql
        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in sql

    @pytest.mark.unit
    def test_validate_data_valid(self, activity_model, sample_activity_data):
        validated = activity_model.validate_data(sample_activity_data)
        assert validated['user_id'] == 1
        assert validated['date'] == date(2024, 1, 15)
        assert validated['steps'] == 8500
        assert validated['calories'] == 2200.5
        assert validated['distance'] == 6.2
        assert validated['data_source'] == 'zepp'

    @pytest.mark.unit
    def test_validate_data_string_date(self, activity_model):
        data = {'user_id': 1, 'date': '2024-01-15', 'steps': 5000}
        validated = activity_model.validate_data(data)
        assert validated['date'] == date(2024, 1, 15)

    @pytest.mark.unit
    def test_validate_data_invalid_date(self, activity_model):
        data = {'user_id': 1, 'date': 'invalid-date', 'steps': 5000}
        with pytest.raises(ValueError, match="Invalid date format"):
            activity_model.validate_data(data)

    @pytest.mark.unit
    def test_validate_data_negative_values(self, activity_model):
        data = {'user_id': 1, 'date': '2024-01-15', 'steps': -100, 'calories': -50}
        validated = activity_model.validate_data(data)
        assert validated['steps'] == 0  # Negative values become 0
        assert validated['calories'] == 0.0

    @pytest.mark.unit
    def test_validate_data_missing_required(self, activity_model):
        with pytest.raises(ValueError, match="Required field 'user_id' is missing"):
            activity_model.validate_data({'date': '2024-01-15'})


class TestSleepModel:
    """Tests for SleepModel."""

    @pytest.fixture
    def sleep_model(self):
        return SleepModel()

    @pytest.mark.unit
    def test_get_table_name(self, sleep_model):
        assert sleep_model.get_table_name() == "sleep_data"

    @pytest.mark.unit
    def test_validate_data_valid(self, sleep_model, sample_sleep_data):
        validated = sleep_model.validate_data(sample_sleep_data)
        assert validated['user_id'] == 1
        assert validated['date'] == date(2024, 1, 15)
        assert validated['total_sleep_minutes'] == 465
        assert validated['deep_sleep_minutes'] == 120
        assert validated['sleep_efficiency'] == 92.5

    @pytest.mark.unit
    def test_validate_data_timestamp_parsing(self, sleep_model):
        data = {
            'user_id': 1,
            'date': '2024-01-15',
            'sleep_start': '2024-01-15 23:30:00+0000',
            'sleep_end': '2024-01-16 07:15:00+0000'
        }
        validated = sleep_model.validate_data(data)
        assert isinstance(validated['sleep_start'], datetime)
        assert isinstance(validated['sleep_end'], datetime)

    @pytest.mark.unit
    def test_validate_data_calculate_total_sleep(self, sleep_model):
        data = {
            'user_id': 1,
            'date': '2024-01-15',
            'sleep_start': datetime(2024, 1, 15, 23, 30),
            'sleep_end': datetime(2024, 1, 16, 7, 15)
        }
        validated = sleep_model.validate_data(data)
        assert validated['total_sleep_minutes'] == 465  # 7h 45m = 465 minutes

    @pytest.mark.unit
    def test_validate_data_sleep_efficiency_bounds(self, sleep_model):
        data = {'user_id': 1, 'date': '2024-01-15', 'sleep_efficiency': 150.0}
        validated = sleep_model.validate_data(data)
        assert validated['sleep_efficiency'] == 100.0  # Capped at 100%


class TestSportModel:
    """Tests for SportModel."""

    @pytest.fixture
    def sport_model(self):
        return SportModel()

    @pytest.mark.unit
    def test_get_table_name(self, sport_model):
        assert sport_model.get_table_name() == "sport_data"

    @pytest.mark.unit
    def test_validate_data_valid(self, sport_model, sample_sport_data):
        validated = sport_model.validate_data(sample_sport_data)
        assert validated['user_id'] == 1
        assert validated['sport_type'] == 1
        assert validated['duration_seconds'] == 2400
        assert validated['distance_meters'] == 5000.0
        assert validated['calories'] == 350.5

    @pytest.mark.unit
    def test_validate_data_timestamp_parsing(self, sport_model):
        data = {
            'user_id': 1,
            'start_time': '2024-01-15 18:00:00+0000',
            'sport_type': 1
        }
        validated = sport_model.validate_data(data)
        assert isinstance(validated['start_time'], datetime)

    @pytest.mark.unit
    def test_validate_data_missing_required(self, sport_model):
        with pytest.raises(ValueError, match="Required field 'sport_type' is missing"):
            sport_model.validate_data({'user_id': 1, 'start_time': '2024-01-15 18:00:00'})


class TestHeartRateModel:
    """Tests for HeartRateModel."""

    @pytest.fixture
    def heart_rate_model(self):
        return HeartRateModel()

    @pytest.mark.unit
    def test_get_table_name(self, heart_rate_model):
        assert heart_rate_model.get_table_name() == "heart_rate_data"

    @pytest.mark.unit
    def test_validate_data_valid(self, heart_rate_model):
        data = {
            'user_id': 1,
            'timestamp': '2024-01-15 12:00:00+0000',
            'heart_rate': 75,
            'resting_hr': 60,
            'max_hr': 180
        }
        validated = heart_rate_model.validate_data(data)
        assert validated['user_id'] == 1
        assert validated['heart_rate'] == 75
        assert validated['resting_hr'] == 60
        assert validated['max_hr'] == 180

    @pytest.mark.unit
    def test_validate_data_invalid_heart_rate(self, heart_rate_model):
        data = {
            'user_id': 1,
            'timestamp': '2024-01-15 12:00:00',
            'heart_rate': 300  # Invalid heart rate
        }
        with pytest.raises(ValueError, match="Invalid heart rate value"):
            heart_rate_model.validate_data(data)

    @pytest.mark.unit
    def test_validate_data_heart_rate_bounds(self, heart_rate_model):
        # Test lower bound
        data = {
            'user_id': 1,
            'timestamp': '2024-01-15 12:00:00',
            'heart_rate': 20
        }
        with pytest.raises(ValueError, match="Invalid heart rate value"):
            heart_rate_model.validate_data(data)


class TestModelRegistry:
    """Tests for model registry functions."""

    @pytest.mark.unit
    def test_model_registry_contents(self):
        assert 'users' in MODEL_REGISTRY
        assert 'activity' in MODEL_REGISTRY
        assert 'sleep' in MODEL_REGISTRY
        assert 'sport' in MODEL_REGISTRY
        assert 'heart_rate' in MODEL_REGISTRY

    @pytest.mark.unit
    def test_get_model_valid(self):
        model = get_model('activity')
        assert isinstance(model, ActivityModel)

    @pytest.mark.unit
    def test_get_model_invalid(self):
        with pytest.raises(ValueError, match="Unknown model: invalid_model"):
            get_model('invalid_model')

    @pytest.mark.unit
    def test_get_all_models(self):
        models = get_all_models()
        assert len(models) == 5
        assert isinstance(models['users'], UserModel)
        assert isinstance(models['activity'], ActivityModel)
        assert isinstance(models['sleep'], SleepModel)
        assert isinstance(models['sport'], SportModel)
        assert isinstance(models['heart_rate'], HeartRateModel)