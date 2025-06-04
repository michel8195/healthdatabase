# Sport Data Implementation

## Overview

This document describes the implementation of sport/exercise data import and integration into the health database system. The sport data functionality adds comprehensive workout and exercise tracking capabilities alongside existing activity and sleep data.

## Database Schema

### Sport Data Table

The `sport_data` table stores exercise and workout information:

```sql
CREATE TABLE sport_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,           -- GMT-3 timezone
    sport_type INTEGER NOT NULL,             -- Numeric sport type code
    duration_seconds INTEGER DEFAULT 0,      -- Exercise duration
    distance_meters REAL DEFAULT 0.0,        -- Distance covered
    calories REAL DEFAULT 0.0,               -- Calories burned
    avg_pace_per_meter REAL DEFAULT 0.0,     -- Average pace
    max_pace_per_meter REAL DEFAULT 0.0,     -- Maximum pace
    min_pace_per_meter REAL DEFAULT 0.0,     -- Minimum pace
    data_source TEXT NOT NULL DEFAULT 'zepp',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Sport Type Mapping

The system recognizes the following sport types from Zepp devices:

| Code | Sport Type        | Description                    |
|------|-------------------|--------------------------------|
| 1    | Walking          | Walking activities             |
| 6    | Cycling          | Bicycle riding                 |
| 9    | Running          | Running/jogging activities     |
| 22   | Strength Training| Weight training, gym workouts  |
| 52   | Other/Indoor     | Indoor activities, misc sports |

## Implementation Components

### 1. SportModel Class

Located in `src/database/models.py`, the `SportModel` class provides:

- Database schema definition
- Data validation and transformation
- Index creation for optimal query performance
- Timezone-aware timestamp handling

### 2. ZeppSportImporter Class

Located in `src/etl/zepp_importers.py`, handles:

- CSV parsing of Zepp sport data files
- Timezone conversion from UTC to GMT-3
- Data validation and error handling
- Pace metric processing (handles -1.0 as invalid values)

### 3. Import Scripts

#### Setup Script
- `scripts/setup_sport_table.py`: Creates the sport_data table and indexes

#### Import Script
- `scripts/import_sport_data.py`: Imports sport data with timezone conversion

#### Verification Scripts
- `scripts/verify_sport_data.py`: Analyzes imported sport data
- `scripts/database_summary.py`: Comprehensive database overview

## Data Processing Features

### Timezone Conversion

All sport timestamps are automatically converted from UTC to GMT-3:

```python
# Example conversion
UTC: "2025-05-18 15:18:00+0000" → GMT-3: "2025-05-18 12:18:00-03:00"
```

### Data Validation

- **Required fields**: user_id, start_time, sport_type
- **Numeric validation**: Duration, distance, calories must be non-negative
- **Pace handling**: Invalid pace values (-1.0) are converted to 0.0
- **Timestamp parsing**: Robust handling of various timestamp formats

### Error Handling

- Graceful handling of malformed data
- Comprehensive logging of import process
- Validation errors logged without stopping import
- Detailed import statistics provided

## Usage Examples

### Import Sport Data

```bash
# Setup the sport table (one-time)
python scripts/setup_sport_table.py

# Import sport data
python scripts/import_sport_data.py
```

### Verify Import

```bash
# Analyze sport data
python scripts/verify_sport_data.py

# View comprehensive database summary
python scripts/database_summary.py
```

### Query Examples

```sql
-- Get running activities
SELECT * FROM sport_data WHERE sport_type = 9;

-- Calculate weekly training volume
SELECT
    strftime('%Y-%W', start_time) as week,
    COUNT(*) as sessions,
    SUM(duration_seconds/3600.0) as total_hours,
    SUM(distance_meters/1000.0) as total_km
FROM sport_data
GROUP BY week;

-- Find longest workout
SELECT start_time, sport_type, duration_seconds/60 as duration_minutes
FROM sport_data
ORDER BY duration_seconds DESC
LIMIT 1;
```

## Import Results

### Data Statistics

From the current import:

- **Total Records**: 87 sport activities
- **Date Range**: October 2024 to May 2025
- **Sport Types**: 5 different activity types
- **Most Popular**: Running (68 activities, 78% of total)
- **Total Training Time**: 101.3 hours
- **Total Distance**: 631.2 km
- **Average Session**: 69.8 minutes, 7.3 km, 358 calories

### Sport Distribution

| Sport Type        | Sessions | Percentage |
|-------------------|----------|------------|
| Running           | 68       | 78.2%      |
| Cycling           | 7        | 8.0%       |
| Other/Indoor      | 6        | 6.9%       |
| Walking           | 4        | 4.6%       |
| Strength Training | 2        | 2.3%       |

## Integration with Existing Data

### Data Relationships

The sport data integrates seamlessly with existing health data:

- **Activity Correlation**: 65 days overlap between sport and daily activity data
- **Sleep Analysis**: Can correlate workout intensity with sleep quality
- **Calorie Tracking**: Sport calories complement daily activity calories

### Analysis Opportunities

1. **Performance Tracking**: Monitor improvements in pace, distance, duration
2. **Recovery Analysis**: Correlate workout intensity with sleep patterns
3. **Activity Balance**: Compare structured exercise vs daily activity
4. **Calorie Analysis**: Total energy expenditure across all activities
5. **Training Load**: Weekly/monthly training volume trends

## Technical Features

### Database Optimization

- **Indexes**: Optimized for common query patterns
  - User + start time for user-specific queries
  - Start time for temporal analysis
  - Sport type for activity-specific analysis
  - Duration and distance for performance queries

### Data Quality

- **Timezone Consistency**: All timestamps in GMT-3
- **Data Validation**: Comprehensive input validation
- **Error Logging**: Detailed error tracking and reporting
- **Import Statistics**: Complete import process metrics

### Extensibility

The modular architecture supports:

- Additional sport types
- New data sources (Fitbit, Garmin, etc.)
- Enhanced metrics (heart rate zones, power data)
- Custom sport classifications

## Files Created/Modified

### New Files

- `scripts/setup_sport_table.py`: Table creation script
- `scripts/import_sport_data.py`: Data import script
- `scripts/verify_sport_data.py`: Data verification and analysis
- `docs/sport_data_implementation.md`: This documentation

### Modified Files

- `src/database/models.py`: Added SportModel class
- `src/etl/zepp_importers.py`: Added ZeppSportImporter class
- `scripts/database_summary.py`: Added sport data summary

## Next Steps

With sport data successfully integrated, the system now supports:

1. **Multi-dimensional Health Analysis**: Activity + Sleep + Sport data
2. **Performance Tracking**: Detailed workout analysis and trends
3. **Comprehensive Dashboards**: Complete health and fitness overview
4. **Advanced Analytics**: Cross-data-type correlations and insights

The health database system is now ready for comprehensive fitness and wellness analytics with rich, multi-source data integration.