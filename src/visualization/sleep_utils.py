"""
Utility functions for sleep data processing and analysis.

This module provides helper functions for working with sleep data,
including time calculations and data validation.
"""

from typing import List, Dict, Tuple
from datetime import datetime


def parse_sleep_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Parse sleep data from CSV file.

    Args:
        file_path: Path to CSV file with columns: day, bedtime, wake_time

    Returns:
        List of sleep data dictionaries
    """
    import csv

    sleep_data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            sleep_data.append({
                'day': row['day'],
                'bedtime': row['bedtime'],
                'wake_time': row['wake_time']
            })

    return sleep_data


def validate_sleep_data(sleep_data: List[Dict[str, str]]) -> bool:
    """
    Validate sleep data format.

    Args:
        sleep_data: List of sleep data dictionaries

    Returns:
        True if data is valid, raises ValueError if invalid
    """
    required_keys = {'day', 'bedtime', 'wake_time'}

    for i, data in enumerate(sleep_data):
        # Check required keys
        if not all(key in data for key in required_keys):
            raise ValueError(f"Missing required keys in sleep data at index {i}")

        # Validate time format
        for time_key in ['bedtime', 'wake_time']:
            time_str = data[time_key]
            try:
                hours, minutes = map(int, time_str.split(':'))
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError(f"Invalid time values in {time_key}: {time_str}")
            except ValueError:
                raise ValueError(f"Invalid time format in {time_key}: {time_str}")

    return True


def calculate_sleep_metrics(sleep_data: List[Dict[str, str]]) -> Dict[str, float]:
    """
    Calculate sleep metrics from sleep data.

    Args:
        sleep_data: List of sleep data dictionaries

    Returns:
        Dictionary with sleep metrics
    """
    def time_to_hours(time_str: str) -> float:
        hours, minutes = map(int, time_str.split(':'))
        return hours + minutes / 60.0

    def calculate_duration(bedtime: str, wake_time: str) -> float:
        bed_hours = time_to_hours(bedtime)
        wake_hours = time_to_hours(wake_time)

        if bed_hours > wake_hours:
            return (24 - bed_hours) + wake_hours
        else:
            return wake_hours - bed_hours

    durations = []
    bedtimes = []
    wake_times = []

    for data in sleep_data:
        duration = calculate_duration(data['bedtime'], data['wake_time'])
        durations.append(duration)
        bedtimes.append(time_to_hours(data['bedtime']))
        wake_times.append(time_to_hours(data['wake_time']))

    return {
        'avg_duration': sum(durations) / len(durations),
        'min_duration': min(durations),
        'max_duration': max(durations),
        'avg_bedtime': sum(bedtimes) / len(bedtimes),
        'avg_wake_time': sum(wake_times) / len(wake_times),
        'sleep_consistency': calculate_consistency(bedtimes, wake_times)
    }


def calculate_consistency(bedtimes: List[float], wake_times: List[float]) -> float:
    """
    Calculate sleep consistency score (0-100).

    Args:
        bedtimes: List of bedtime hours
        wake_times: List of wake time hours

    Returns:
        Consistency score (higher is more consistent)
    """
    import statistics

    bed_std = statistics.stdev(bedtimes) if len(bedtimes) > 1 else 0
    wake_std = statistics.stdev(wake_times) if len(wake_times) > 1 else 0

    # Convert standard deviation to consistency score (0-100)
    # Lower standard deviation = higher consistency
    bed_consistency = max(0, 100 - (bed_std * 20))
    wake_consistency = max(0, 100 - (wake_std * 20))

    return (bed_consistency + wake_consistency) / 2


def generate_sample_data() -> List[Dict[str, str]]:
    """
    Generate sample sleep data for testing.

    Returns:
        List of sample sleep data dictionaries
    """
    return [
        {'day': 'T', 'bedtime': '22:39', 'wake_time': '07:47'},
        {'day': 'F', 'bedtime': '21:31', 'wake_time': '09:04'},
        {'day': 'S', 'bedtime': '22:17', 'wake_time': '08:32'},
        {'day': 'S', 'bedtime': '22:18', 'wake_time': '08:24'},
        {'day': 'M', 'bedtime': '00:06', 'wake_time': '07:01'},
        {'day': 'T', 'bedtime': '21:49', 'wake_time': '08:04'},
        {'day': 'W', 'bedtime': '22:10', 'wake_time': '07:05'}
    ]