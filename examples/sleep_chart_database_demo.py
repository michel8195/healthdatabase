#!/usr/bin/env python3
"""
Sleep Regularity Chart from Database Demo

This script demonstrates how to create sleep regularity charts using
real data from the database, showing actual dates instead of day abbreviations.
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from visualization.sleep_chart import create_sleep_chart, SleepRegularityChart
from database.sleep_queries import get_recent_sleep_data, get_sleep_data_by_date_range, SleepDataExtractor


def main():
    """Main demo function using database data."""
    print("Sleep Regularity Chart from Database Demo")
    print("=" * 45)

    try:
        # Create extractor instance
        extractor = SleepDataExtractor()

        # Get available date range
        date_range = extractor.get_available_date_range()
        print(f"Available sleep data range:")
        print(f"  From: {date_range['start_date']}")
        print(f"  To: {date_range['end_date']}")

        # Get recent 7 days of sleep data
        print(f"\nLoading recent 7 days of sleep data...")
        sleep_data = get_recent_sleep_data(days=7)

        if not sleep_data:
            print("No sleep data found! Using sample data instead.")
            from visualization.sleep_utils import generate_sample_data
            sleep_data = generate_sample_data()
        else:
            print(f"Found {len(sleep_data)} days of sleep data:")
            for data in sleep_data:
                print(f"  {data['day']}: {data['bedtime']} - {data['wake_time']}")

        # Create and display the chart with dates
        print("\nGenerating sleep regularity chart with real dates...")
        chart = create_sleep_chart(
            sleep_data=sleep_data,
            title="SLEEP REGULARITY - RECENT WEEK",
            figsize=(12, 8),
            save_path="database_sleep_chart.png"
        )

        print("Chart saved as 'database_sleep_chart.png'")
        print("Displaying chart...")

        # Show the chart
        chart.show()

        # Clean up
        chart.close()

    except Exception as e:
        print(f"Error loading database data: {e}")
        print("This might be because the database path is incorrect or no valid sleep data exists.")
        return False

    return True


def create_custom_date_range_chart():
    """Example of creating a chart for a specific date range."""
    print("\n" + "=" * 45)
    print("Custom Date Range Chart Example")
    print("=" * 45)

    try:
        extractor = SleepDataExtractor()

        # Get a specific date range (last 14 days of available data)
        date_range = extractor.get_available_date_range()

        if not date_range['end_date']:
            print("No sleep data available for date range selection.")
            return False

        from datetime import datetime, timedelta

        # Calculate 14 days back from the last available date
        end_date = datetime.strptime(date_range['end_date'], '%Y-%m-%d')
        start_date = end_date - timedelta(days=13)  # 14 days total

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        print(f"Loading sleep data from {start_date_str} to {end_date_str}...")

        sleep_data = get_sleep_data_by_date_range(start_date_str, end_date_str)

        if not sleep_data:
            print("No sleep data found for the specified date range.")
            return False

        print(f"Found {len(sleep_data)} days of sleep data:")
        for data in sleep_data:
            print(f"  {data['day']}: {data['bedtime']} - {data['wake_time']}")

        # Create custom chart with more data points
        chart = create_sleep_chart(
            sleep_data=sleep_data,
            title="SLEEP REGULARITY - 2 WEEK PATTERN",
            figsize=(16, 8),
            save_path="database_sleep_chart_2weeks.png"
        )

        print("Extended chart saved as 'database_sleep_chart_2weeks.png'")
        chart.show()
        chart.close()

        return True

    except Exception as e:
        print(f"Error creating custom date range chart: {e}")
        return False


def show_sleep_statistics():
    """Display sleep statistics from the database."""
    print("\n" + "=" * 45)
    print("Sleep Statistics from Database")
    print("=" * 45)

    try:
        # Get recent sleep data for statistics
        sleep_data = get_recent_sleep_data(days=30)  # Last 30 days

        if not sleep_data:
            print("No sleep data available for statistics.")
            return

        from visualization.sleep_utils import calculate_sleep_metrics

        metrics = calculate_sleep_metrics(sleep_data)

        print(f"Sleep Statistics (last {len(sleep_data)} days):")
        print(f"  Average Duration: {metrics['avg_duration']:.1f} hours")
        print(f"  Min Duration: {metrics['min_duration']:.1f} hours")
        print(f"  Max Duration: {metrics['max_duration']:.1f} hours")
        print(f"  Sleep Consistency: {metrics['sleep_consistency']:.1f}%")
        print(f"  Average Bedtime: {metrics['avg_bedtime']:.1f} hours ({int(metrics['avg_bedtime'])}:{int((metrics['avg_bedtime'] % 1) * 60):02d})")
        print(f"  Average Wake Time: {metrics['avg_wake_time']:.1f} hours ({int(metrics['avg_wake_time'])}:{int((metrics['avg_wake_time'] % 1) * 60):02d})")

    except Exception as e:
        print(f"Error calculating statistics: {e}")


if __name__ == "__main__":
    try:
        success = main()

        if success:
            # Ask user if they want to see more examples
            response = input("\nWould you like to see a 2-week chart? (y/n): ")
            if response.lower() in ['y', 'yes']:
                create_custom_date_range_chart()

            response = input("\nWould you like to see sleep statistics? (y/n): ")
            if response.lower() in ['y', 'yes']:
                show_sleep_statistics()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError running demo: {e}")
        sys.exit(1)

    print("\nDemo completed successfully!")