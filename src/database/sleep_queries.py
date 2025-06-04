"""
Sleep data database queries for chart generation.

This module provides functions to extract sleep data from the database
and format it for use with the sleep regularity chart.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os


class SleepDataExtractor:
    """
    Class to extract sleep data from the database for chart generation.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the sleep data extractor.

        Args:
            db_path: Path to the database file. If None, uses default path.
        """
        if db_path is None:
            # Default to the health_data.db in the data directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(project_root, 'data', 'health_data.db')

        self.db_path = db_path

    def get_recent_sleep_data(self, days: int = 7, user_id: int = 1) -> List[Dict[str, str]]:
        """
        Get recent sleep data for chart generation.

        Args:
            days: Number of recent days to retrieve
            user_id: User ID to filter by

        Returns:
            List of sleep data dictionaries formatted for chart
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get recent sleep data with valid start/end times
            query = """
            SELECT date, sleep_start, sleep_end
            FROM sleep_data
            WHERE user_id = ?
            AND sleep_start != sleep_end
            AND sleep_start IS NOT NULL
            AND sleep_end IS NOT NULL
            ORDER BY date DESC
            LIMIT ?
            """

            cursor.execute(query, (user_id, days))
            rows = cursor.fetchall()

            if not rows:
                raise ValueError(f"No sleep data found for user {user_id}")

            # Convert to chart format
            sleep_data = []
            for row in rows:
                date_str, sleep_start_str, sleep_end_str = row

                # Parse the timestamps
                sleep_start = datetime.fromisoformat(sleep_start_str.replace('+00:00', ''))
                sleep_end = datetime.fromisoformat(sleep_end_str.replace('+00:00', ''))

                # Format times as HH:MM
                bedtime = sleep_start.strftime('%H:%M')
                wake_time = sleep_end.strftime('%H:%M')

                # Format date for display (e.g., "12/25" or "Dec 25")
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d')

                sleep_data.append({
                    'day': formatted_date,
                    'bedtime': bedtime,
                    'wake_time': wake_time,
                    'full_date': date_str
                })

            # Reverse to show chronological order (oldest to newest)
            sleep_data.reverse()

            return sleep_data

        finally:
            conn.close()

    def get_sleep_data_by_date_range(self, start_date: str, end_date: str,
                                   user_id: int = 1) -> List[Dict[str, str]]:
        """
        Get sleep data for a specific date range.

        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            user_id: User ID to filter by

        Returns:
            List of sleep data dictionaries formatted for chart
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
            SELECT date, sleep_start, sleep_end
            FROM sleep_data
            WHERE user_id = ?
            AND date BETWEEN ? AND ?
            AND sleep_start != sleep_end
            AND sleep_start IS NOT NULL
            AND sleep_end IS NOT NULL
            ORDER BY date ASC
            """

            cursor.execute(query, (user_id, start_date, end_date))
            rows = cursor.fetchall()

            sleep_data = []
            for row in rows:
                date_str, sleep_start_str, sleep_end_str = row

                # Parse the timestamps
                sleep_start = datetime.fromisoformat(sleep_start_str.replace('+00:00', ''))
                sleep_end = datetime.fromisoformat(sleep_end_str.replace('+00:00', ''))

                # Format times as HH:MM
                bedtime = sleep_start.strftime('%H:%M')
                wake_time = sleep_end.strftime('%H:%M')

                # Format date for display
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d')

                sleep_data.append({
                    'day': formatted_date,
                    'bedtime': bedtime,
                    'wake_time': wake_time,
                    'full_date': date_str
                })

            return sleep_data

        finally:
            conn.close()

    def get_available_date_range(self, user_id: int = 1) -> Dict[str, str]:
        """
        Get the available date range for sleep data.

        Args:
            user_id: User ID to filter by

        Returns:
            Dictionary with 'start_date' and 'end_date'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
            SELECT MIN(date) as start_date, MAX(date) as end_date
            FROM sleep_data
            WHERE user_id = ?
            AND sleep_start != sleep_end
            AND sleep_start IS NOT NULL
            AND sleep_end IS NOT NULL
            """

            cursor.execute(query, (user_id,))
            row = cursor.fetchone()

            return {
                'start_date': row[0] if row[0] else None,
                'end_date': row[1] if row[1] else None
            }

        finally:
            conn.close()


def get_recent_sleep_data(days: int = 7, user_id: int = 1,
                         db_path: str = None) -> List[Dict[str, str]]:
    """
    Convenience function to get recent sleep data.

    Args:
        days: Number of recent days to retrieve
        user_id: User ID to filter by
        db_path: Path to database file

    Returns:
        List of sleep data dictionaries formatted for chart
    """
    extractor = SleepDataExtractor(db_path)
    return extractor.get_recent_sleep_data(days, user_id)


def get_sleep_data_by_date_range(start_date: str, end_date: str,
                               user_id: int = 1, db_path: str = None) -> List[Dict[str, str]]:
    """
    Convenience function to get sleep data by date range.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        user_id: User ID to filter by
        db_path: Path to database file

    Returns:
        List of sleep data dictionaries formatted for chart
    """
    extractor = SleepDataExtractor(db_path)
    return extractor.get_sleep_data_by_date_range(start_date, end_date, user_id)