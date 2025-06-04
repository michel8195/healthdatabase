#!/usr/bin/env python3
"""
Create Sleep Regularity Chart from Database

This script creates a sleep regularity chart using real data from your database,
showing actual dates instead of day abbreviations.
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.sleep_queries import get_recent_sleep_data, SleepDataExtractor
from visualization.sleep_chart import create_sleep_chart
from visualization.sleep_utils import calculate_sleep_metrics


def main():
    """Generate sleep chart from database."""
    print("Creating Sleep Regularity Chart from Database")
    print("=" * 50)

    try:
        # Get recent sleep data from database
        print("Loading sleep data from database...")
        sleep_data = get_recent_sleep_data(days=7)

        if not sleep_data:
            print("No sleep data found in database!")
            return

        print(f"Found {len(sleep_data)} days of sleep data:")
        for data in sleep_data:
            date_display = data['day']
            bedtime = data['bedtime']
            wake_time = data['wake_time']
            print(f"  {date_display}: {bedtime} - {wake_time}")

        # Calculate metrics
        metrics = calculate_sleep_metrics(sleep_data)
        print(f"\nSleep Metrics:")
        print(f"  Average Duration: {metrics['avg_duration']:.1f} hours")
        print(f"  Sleep Consistency: {metrics['sleep_consistency']:.1f}%")

        # Create chart with real dates
        print("\nGenerating chart...")
        chart = create_sleep_chart(
            sleep_data=sleep_data,
            title="SLEEP REGULARITY",
            figsize=(12, 8),
            save_path="sleep_regularity_chart.png"
        )

        print("✅ Chart saved as 'sleep_regularity_chart.png'")
        print("✅ Chart created successfully!")

        # Show chart (comment out if running headless)
        try:
            chart.show()
        except Exception:
            print("(Chart display not available in this environment)")

        chart.close()

        # Show available date range
        extractor = SleepDataExtractor()
        date_range = extractor.get_available_date_range()
        print(f"\nAvailable data range: {date_range['start_date']} to {date_range['end_date']}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure the database file exists at 'data/health_data.db'")
        print("- Ensure you have valid sleep data in the sleep_data table")
        print("- Check that matplotlib is installed: pip install matplotlib")


if __name__ == "__main__":
    main()