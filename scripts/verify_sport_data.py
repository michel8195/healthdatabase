#!/usr/bin/env python3
"""
Verify sport data import and analyze sport activities.

This script checks the imported sport data and provides analysis of
different sport types and activities.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging_config import setup_logging


# Sport type mapping based on common Zepp codes
SPORT_TYPES = {
    1: "Walking",
    6: "Cycling",
    9: "Running",
    22: "Strength Training",
    52: "Other/Indoor"
}


def main():
    """Main function to verify sport data."""
    setup_logging(level="INFO")

    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    print(f"Verifying sport data in: {db_path}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if sport_data table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='sport_data'
        """)

        if not cursor.fetchone():
            print("❌ sport_data table not found!")
            return 1

        # Get basic statistics
        cursor.execute("SELECT COUNT(*) FROM sport_data")
        total_records = cursor.fetchone()[0]
        print(f"🏃 Total sport records: {total_records}")

        # Check date range
        cursor.execute("""
            SELECT MIN(DATE(start_time)), MAX(DATE(start_time)) FROM sport_data
        """)
        min_date, max_date = cursor.fetchone()
        print(f"📅 Date range: {min_date} to {max_date}")

        # Sport type distribution
        cursor.execute("""
            SELECT sport_type, COUNT(*) as count
            FROM sport_data
            GROUP BY sport_type
            ORDER BY count DESC
        """)

        print("\n🏅 Sport Type Distribution:")
        print("-" * 40)
        for sport_type, count in cursor.fetchall():
            sport_name = SPORT_TYPES.get(sport_type, f"Unknown ({sport_type})")
            print(f"{sport_name:<20} {count:>3} activities")

        # Sample records with timezone info
        cursor.execute("""
            SELECT start_time, sport_type, duration_seconds,
                   distance_meters, calories
            FROM sport_data
            WHERE start_time IS NOT NULL
            ORDER BY start_time DESC
            LIMIT 5
        """)

        print("\n🕐 Recent Activities (GMT-3 timezone):")
        print("-" * 80)
        print(f"{'Date & Time':<20} {'Sport':<15} {'Duration':<10} {'Distance':<10} {'Calories':<8}")
        print("-" * 80)

        for row in cursor.fetchall():
            start_time, sport_type, duration, distance, calories = row
            sport_name = SPORT_TYPES.get(sport_type, f"Type {sport_type}")

            try:
                dt = datetime.fromisoformat(start_time)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
                timezone_str = dt.strftime("%z")
            except:
                time_str = start_time[:16] if start_time else "N/A"
                timezone_str = ""

            duration_min = duration // 60
            distance_km = distance / 1000 if distance > 0 else 0

            print(f"{time_str:<20} {sport_name:<15} {duration_min:>3}m {distance_km:>6.1f}km {calories:>6.0f}")

        # Verify timezone conversion
        cursor.execute("""
            SELECT start_time FROM sport_data
            WHERE start_time LIKE '%-03:00'
            LIMIT 1
        """)

        sample_tz = cursor.fetchone()
        if sample_tz:
            print(f"\n✅ Timezone conversion verified: {sample_tz[0]}")
            print("   Timestamps show -03:00 offset (GMT-3)")

        # Activity statistics
        cursor.execute("""
            SELECT
                AVG(duration_seconds/60.0) as avg_duration_min,
                AVG(distance_meters/1000.0) as avg_distance_km,
                AVG(calories) as avg_calories,
                SUM(duration_seconds/3600.0) as total_hours,
                SUM(distance_meters/1000.0) as total_distance_km,
                SUM(calories) as total_calories
            FROM sport_data
            WHERE duration_seconds > 0
        """)

        stats = cursor.fetchone()
        if stats and stats[0]:
            avg_dur, avg_dist, avg_cal, total_hrs, total_dist, total_cal = stats
            print(f"\n📊 Activity Statistics:")
            print(f"   Average duration: {avg_dur:.1f} minutes")
            print(f"   Average distance: {avg_dist:.1f} km")
            print(f"   Average calories: {avg_cal:.0f}")
            print(f"   Total training time: {total_hrs:.1f} hours")
            print(f"   Total distance: {total_dist:.1f} km")
            print(f"   Total calories burned: {total_cal:.0f}")

        # Most active sport
        cursor.execute("""
            SELECT sport_type,
                   COUNT(*) as sessions,
                   SUM(duration_seconds/3600.0) as total_hours,
                   SUM(distance_meters/1000.0) as total_km,
                   AVG(calories) as avg_calories
            FROM sport_data
            WHERE duration_seconds > 0
            GROUP BY sport_type
            ORDER BY sessions DESC
            LIMIT 1
        """)

        top_sport = cursor.fetchone()
        if top_sport:
            sport_type, sessions, hours, km, calories = top_sport
            sport_name = SPORT_TYPES.get(sport_type, f"Type {sport_type}")
            print(f"\n🏆 Most Active Sport: {sport_name}")
            print(f"   Sessions: {sessions}")
            print(f"   Total time: {hours:.1f} hours")
            print(f"   Total distance: {km:.1f} km")
            print(f"   Avg calories/session: {calories:.0f}")

        conn.close()
        print("\n✅ Sport data verification completed successfully!")
        return 0

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())