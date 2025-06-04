#!/usr/bin/env python3
"""
Sleep Regularity Chart Demo

This script demonstrates how to use the sleep regularity chart module
to create visualizations similar to health app sleep charts.
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from visualization.sleep_chart import create_sleep_chart
from visualization.sleep_utils import generate_sample_data, calculate_sleep_metrics


def main():
    """Main demo function."""
    print("Sleep Regularity Chart Demo")
    print("=" * 30)

    # Generate sample data (matching the image you showed)
    sleep_data = generate_sample_data()

    print("\nSample Sleep Data:")
    for data in sleep_data:
        print(f"  {data['day']}: {data['bedtime']} - {data['wake_time']}")

    # Calculate sleep metrics
    metrics = calculate_sleep_metrics(sleep_data)
    print(f"\nSleep Metrics:")
    print(f"  Average Duration: {metrics['avg_duration']:.1f} hours")
    print(f"  Sleep Consistency: {metrics['sleep_consistency']:.1f}%")
    print(f"  Average Bedtime: {metrics['avg_bedtime']:.1f} hours")
    print(f"  Average Wake Time: {metrics['avg_wake_time']:.1f} hours")

    # Create and display the chart
    print("\nGenerating sleep regularity chart...")
    chart = create_sleep_chart(
        sleep_data=sleep_data,
        title="SLEEP REGULARITY",
        figsize=(12, 8),
        save_path="sleep_chart.png"
    )

    print("Chart saved as 'sleep_chart.png'")
    print("Displaying chart...")

    # Show the chart
    chart.show()

    # Clean up
    chart.close()


def create_custom_chart():
    """Example of creating a custom chart with different data."""
    print("\n" + "=" * 30)
    print("Custom Chart Example")
    print("=" * 30)

    # Custom sleep data
    custom_data = [
        {'day': 'Mon', 'bedtime': '23:15', 'wake_time': '06:30'},
        {'day': 'Tue', 'bedtime': '22:45', 'wake_time': '06:45'},
        {'day': 'Wed', 'bedtime': '23:00', 'wake_time': '07:00'},
        {'day': 'Thu', 'bedtime': '22:30', 'wake_time': '06:15'},
        {'day': 'Fri', 'bedtime': '23:45', 'wake_time': '08:00'},
        {'day': 'Sat', 'bedtime': '00:30', 'wake_time': '09:15'},
        {'day': 'Sun', 'bedtime': '23:00', 'wake_time': '07:30'}
    ]

    print("\nCustom Sleep Data:")
    for data in custom_data:
        print(f"  {data['day']}: {data['bedtime']} - {data['wake_time']}")

    # Create custom chart
    chart = create_sleep_chart(
        sleep_data=custom_data,
        title="WEEKLY SLEEP PATTERN",
        figsize=(14, 8),
        save_path="custom_sleep_chart.png"
    )

    print("Custom chart saved as 'custom_sleep_chart.png'")
    chart.show()
    chart.close()


if __name__ == "__main__":
    try:
        main()

        # Ask user if they want to see the custom example
        response = input("\nWould you like to see a custom chart example? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_custom_chart()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError running demo: {e}")
        sys.exit(1)

    print("\nDemo completed successfully!")