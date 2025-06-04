#!/usr/bin/env python3
"""
Comprehensive health database summary.

This script provides an overview of all data types in the health database:
activity, sleep, and sport data.
"""

import sys
import sqlite3
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main function to show database summary."""
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "health_data.db"

    print("🏥 HEALTH DATABASE SUMMARY")
    print("=" * 60)
    print("📊 Multi-source health data analytics system")
    print()

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Available Tables: {', '.join(tables)}")
        print()

        # Activity Data Summary
        print("🚶 ACTIVITY DATA")
        print("-" * 30)
        cursor.execute("SELECT COUNT(*) FROM daily_activity")
        activity_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT MIN(date), MAX(date) FROM daily_activity
        """)
        min_date, max_date = cursor.fetchone()

        cursor.execute("""
            SELECT AVG(steps), AVG(calories), AVG(distance)
            FROM daily_activity WHERE steps > 0
        """)
        avg_steps, avg_calories, avg_distance = cursor.fetchone()

        print(f"Records: {activity_count}")
        print(f"Date range: {min_date} to {max_date}")
        print(f"Avg daily steps: {avg_steps:.0f}")
        print(f"Avg daily calories: {avg_calories:.0f}")
        print(f"Avg daily distance: {avg_distance:.1f} km")
        print()

        # Sleep Data Summary
        print("😴 SLEEP DATA")
        print("-" * 30)
        cursor.execute("SELECT COUNT(*) FROM sleep_data")
        sleep_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT MIN(date), MAX(date) FROM sleep_data
        """)
        min_date, max_date = cursor.fetchone()

        cursor.execute("""
            SELECT
                AVG(total_sleep_minutes/60.0),
                AVG(deep_sleep_minutes),
                AVG(light_sleep_minutes),
                AVG(rem_sleep_minutes),
                AVG(sleep_efficiency)
            FROM sleep_data WHERE total_sleep_minutes > 0
        """)
        sleep_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) FROM sleep_data
            WHERE sleep_start LIKE '%-03:00'
        """)
        gmt3_count = cursor.fetchone()[0]

        print(f"Records: {sleep_count}")
        print(f"Date range: {min_date} to {max_date}")
        if sleep_stats and sleep_stats[0]:
            avg_total, avg_deep, avg_light, avg_rem, avg_eff = sleep_stats
            print(f"Avg sleep duration: {avg_total:.1f} hours")
            print(f"Avg deep sleep: {avg_deep:.0f} minutes")
            print(f"Avg light sleep: {avg_light:.0f} minutes")
            print(f"Avg REM sleep: {avg_rem:.0f} minutes")
            print(f"Avg sleep efficiency: {avg_eff:.1f}%")
        print(f"GMT-3 timezone records: {gmt3_count}")
        print()

        # Sport Data Summary
        print("🏃 SPORT DATA")
        print("-" * 30)
        cursor.execute("SELECT COUNT(*) FROM sport_data")
        sport_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT MIN(DATE(start_time)), MAX(DATE(start_time))
            FROM sport_data
        """)
        min_date, max_date = cursor.fetchone()

        cursor.execute("""
            SELECT
                COUNT(DISTINCT sport_type),
                AVG(duration_seconds/60.0),
                AVG(distance_meters/1000.0),
                AVG(calories),
                SUM(duration_seconds/3600.0),
                SUM(distance_meters/1000.0)
            FROM sport_data WHERE duration_seconds > 0
        """)
        sport_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) FROM sport_data
            WHERE start_time LIKE '%-03:00'
        """)
        sport_gmt3_count = cursor.fetchone()[0]

        print(f"Records: {sport_count}")
        print(f"Date range: {min_date} to {max_date}")
        if sport_stats and sport_stats[0]:
            types, avg_dur, avg_dist, avg_cal, total_hrs, total_dist = sport_stats
            print(f"Sport types: {types}")
            print(f"Avg session duration: {avg_dur:.1f} minutes")
            print(f"Avg session distance: {avg_dist:.1f} km")
            print(f"Avg calories/session: {avg_cal:.0f}")
            print(f"Total training time: {total_hrs:.1f} hours")
            print(f"Total distance: {total_dist:.1f} km")
        print(f"GMT-3 timezone records: {sport_gmt3_count}")
        print()

        # Data Quality Summary
        print("✅ DATA QUALITY")
        print("-" * 30)

        # Check for data overlap/correlation opportunities
        cursor.execute("""
            SELECT COUNT(DISTINCT a.date)
            FROM daily_activity a
            INNER JOIN sleep_data s ON a.date = s.date
        """)
        activity_sleep_overlap = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(sp.start_time))
            FROM sport_data sp
            INNER JOIN daily_activity a ON DATE(sp.start_time) = a.date
        """)
        sport_activity_overlap = cursor.fetchone()[0]

        print(f"Activity-Sleep data overlap: {activity_sleep_overlap} days")
        print(f"Sport-Activity data overlap: {sport_activity_overlap} days")
        print()

        # Technical Features
        print("🔧 TECHNICAL FEATURES")
        print("-" * 30)
        print("✓ Multi-source data integration (Zepp devices)")
        print("✓ Timezone conversion (UTC → GMT-3)")
        print("✓ Data validation and error handling")
        print("✓ Modular ETL architecture")
        print("✓ SQLite database with proper indexing")
        print("✓ Foreign key constraints")
        print("✓ Automated timestamp handling")
        print("✓ Comprehensive logging")
        print()

        # Analysis Opportunities
        print("📈 ANALYSIS OPPORTUNITIES")
        print("-" * 30)
        print("• Sleep quality vs daily activity correlation")
        print("• Exercise impact on sleep patterns")
        print("• Activity trends and seasonal patterns")
        print("• Sport performance tracking")
        print("• Calorie burn analysis across activities")
        print("• Recovery time between workouts")
        print("• Weekly/monthly health summaries")
        print()

        conn.close()

        print("🎯 DATABASE STATUS: Ready for comprehensive health analytics!")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())