# Sleep Regularity Chart Generator

Generate beautiful sleep regularity charts using real data from your health database, similar to modern health app visualizations.

## Quick Start

### Simple Usage

```bash
# Generate chart from your database
python create_sleep_chart.py
```

This will:
- Load the most recent 7 days of sleep data from your database
- Show actual dates (e.g., `05/29`, `06/01`) instead of day abbreviations
- Create a chart file: `sleep_regularity_chart.png`
- Display sleep metrics (duration, consistency)

### Sample Output

```
Creating Sleep Regularity Chart from Database
==================================================
Loading sleep data from database...
Found 7 days of sleep data:
  05/29: 01:39 - 10:47
  05/30: 00:31 - 12:04
  05/31: 01:17 - 11:32
  06/01: 01:18 - 11:24
  06/02: 03:06 - 10:01
  06/03: 00:49 - 11:04
  06/04: 01:10 - 10:05

Sleep Metrics:
  Average Duration: 9.6 hours
  Sleep Consistency: 84.1%

✅ Chart saved as 'sleep_regularity_chart.png'
✅ Chart created successfully!
```

## Chart Features

- **Real Dates**: Shows actual dates (MM/DD format) instead of day abbreviations
- **Sleep Bars**: Blue bars showing sleep duration for each day
- **Time Labels**: Bedtime and wake time displayed for each day
- **Time Axis**: Reference times (20:00, 03:30, 11:00) on the left
- **Modern Design**: Clean, health app-inspired styling
- **Overnight Sleep**: Properly handles sleep that spans midnight

## Advanced Usage

### Python Code

```python
from database.sleep_queries import get_recent_sleep_data
from visualization.sleep_chart import create_sleep_chart

# Load data from database
sleep_data = get_recent_sleep_data(days=7)

# Create chart
chart = create_sleep_chart(
    sleep_data=sleep_data,
    title="SLEEP REGULARITY",
    figsize=(12, 8),
    save_path="my_sleep_chart.png"
)

chart.show()
```

### Custom Date Range

```python
from database.sleep_queries import get_sleep_data_by_date_range

# Get specific date range
sleep_data = get_sleep_data_by_date_range(
    start_date='2025-05-01',
    end_date='2025-05-31'
)

chart = create_sleep_chart(sleep_data, title="MAY SLEEP PATTERN")
chart.show()
```

### Jupyter Notebook

Use the provided notebook: `notebooks/sleep_chart_database.ipynb`

## Database Requirements

The script expects:
- Database file at: `data/health_data.db`
- Table: `sleep_data`
- Required columns:
  - `date` (DATE)
  - `sleep_start` (TIMESTAMP)
  - `sleep_end` (TIMESTAMP)
  - `user_id` (INTEGER)

## File Structure

```
├── create_sleep_chart.py              # Main script
├── src/
│   ├── database/
│   │   └── sleep_queries.py           # Database integration
│   └── visualization/
│       ├── sleep_chart.py             # Chart generation
│       └── sleep_utils.py             # Utility functions
├── examples/
│   └── sleep_chart_database_demo.py   # Extended demo
├── notebooks/
│   └── sleep_chart_database.ipynb     # Interactive notebook
└── docs/
    └── sleep_chart_guide.md           # Complete documentation
```

## Dependencies

```bash
pip install matplotlib numpy
```

## Troubleshooting

**No data found**: Check that you have valid sleep records with different start/end times in your database.

**Import errors**: Make sure to run from the project root directory where the `src` folder is located.

**Display issues**: The moon emoji might not display properly on some systems, but this doesn't affect chart functionality.

## Chart Customization

The chart displays dates in MM/DD format. You can modify the date format in `src/database/sleep_queries.py`:

```python
# Change this line for different date formats:
formatted_date = date_obj.strftime('%m/%d')  # MM/DD
# formatted_date = date_obj.strftime('%b %d')  # Dec 25
# formatted_date = date_obj.strftime('%d')     # 25
```

## Examples

- **Recent week**: `python create_sleep_chart.py`
- **Extended demo**: `python examples/sleep_chart_database_demo.py`
- **Interactive**: Open `notebooks/sleep_chart_database.ipynb`