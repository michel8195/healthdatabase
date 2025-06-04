# Sleep Regularity Chart Guide

This guide explains how to use the sleep regularity chart modules to create visualizations similar to health app sleep charts.

## Overview

The sleep chart modules provide functionality to:
- Create sleep regularity charts showing sleep patterns across days
- Calculate sleep metrics like average duration and consistency
- Handle overnight sleep patterns that span midnight
- Export charts as images

## Quick Start

### Basic Usage

```python
from visualization.sleep_chart import create_sleep_chart
from visualization.sleep_utils import generate_sample_data

# Generate sample data
sleep_data = generate_sample_data()

# Create and display chart
chart = create_sleep_chart(sleep_data)
chart.show()
```

### Sample Data Format

Sleep data should be a list of dictionaries with the following keys:
- `day`: Day abbreviation (e.g., 'T', 'F', 'Mon', 'Tue')
- `bedtime`: Bedtime in "HH:MM" format (e.g., '22:30')
- `wake_time`: Wake time in "HH:MM" format (e.g., '07:00')

```python
sleep_data = [
    {'day': 'T', 'bedtime': '22:39', 'wake_time': '07:47'},
    {'day': 'F', 'bedtime': '21:31', 'wake_time': '09:04'},
    {'day': 'S', 'bedtime': '22:17', 'wake_time': '08:32'},
    # ... more days
]
```

## Modules

### `visualization.sleep_chart`

Main module for creating sleep regularity charts.

#### Classes

**`SleepRegularityChart`**
- Main chart class with customization options
- Methods: `plot_sleep_data()`, `save_chart()`, `show()`, `close()`

#### Functions

**`create_sleep_chart(sleep_data, title, figsize, save_path)`**
- Convenience function to create charts quickly
- Returns `SleepRegularityChart` instance

### `visualization.sleep_utils`

Utility functions for sleep data processing.

#### Functions

**`generate_sample_data()`**
- Returns sample sleep data for testing

**`calculate_sleep_metrics(sleep_data)`**
- Calculates sleep statistics
- Returns dict with avg_duration, consistency, etc.

**`validate_sleep_data(sleep_data)`**
- Validates sleep data format
- Raises ValueError if invalid

**`parse_sleep_csv(file_path)`**
- Parses sleep data from CSV file
- Expected columns: day, bedtime, wake_time

## Examples

### Creating a Basic Chart

```python
from visualization.sleep_chart import create_sleep_chart

sleep_data = [
    {'day': 'Mon', 'bedtime': '23:00', 'wake_time': '07:00'},
    {'day': 'Tue', 'bedtime': '22:30', 'wake_time': '06:45'},
    {'day': 'Wed', 'bedtime': '23:15', 'wake_time': '07:15'},
]

chart = create_sleep_chart(
    sleep_data=sleep_data,
    title="MY SLEEP PATTERN",
    figsize=(10, 6),
    save_path="my_sleep.png"
)

chart.show()
```

### Using the Chart Class Directly

```python
from visualization.sleep_chart import SleepRegularityChart

# Create chart instance
chart = SleepRegularityChart(figsize=(12, 8))

# Plot data
chart.plot_sleep_data(sleep_data, title="WEEKLY SLEEP")

# Save and show
chart.save_chart("weekly_sleep.png", dpi=300)
chart.show()

# Clean up
chart.close()
```

### Loading Data from CSV

```python
from visualization.sleep_utils import parse_sleep_csv
from visualization.sleep_chart import create_sleep_chart

# Load data from CSV file
sleep_data = parse_sleep_csv("my_sleep_data.csv")

# Create chart
chart = create_sleep_chart(sleep_data)
chart.show()
```

CSV format:
```csv
day,bedtime,wake_time
Mon,23:00,07:00
Tue,22:30,06:45
Wed,23:15,07:15
```

### Calculating Sleep Metrics

```python
from visualization.sleep_utils import calculate_sleep_metrics

metrics = calculate_sleep_metrics(sleep_data)

print(f"Average sleep duration: {metrics['avg_duration']:.1f} hours")
print(f"Sleep consistency score: {metrics['sleep_consistency']:.1f}%")
```

## Chart Features

The sleep regularity chart displays:

- **Sleep Bars**: Blue vertical bars showing sleep duration
- **Time Labels**: Bedtime (bottom) and wake time (top) for each day
- **Time Axis**: Reference times (20:00, 03:30, 11:00) on the left
- **Day Labels**: Day abbreviations at the bottom
- **Title**: Customizable chart title with sleep icon

### Visual Elements

- **Colors**: Blue bars (#4A90E2) on light background
- **Layout**: Clean, modern design inspired by health apps
- **Overnight Sleep**: Properly handles sleep spanning midnight
- **Scaling**: Automatic scaling based on data range

## Customization

### Chart Styling

You can customize the chart appearance by modifying the `SleepRegularityChart` class:

```python
chart = SleepRegularityChart()

# Customize colors
chart.sleep_color = '#FF6B6B'  # Red bars
chart.background_color = '#F0F0F0'  # Light gray background
chart.text_color = '#333333'  # Dark text

# Plot with custom styling
chart.plot_sleep_data(sleep_data)
```

### Figure Size and Resolution

```python
# Large high-resolution chart
chart = create_sleep_chart(
    sleep_data=sleep_data,
    figsize=(16, 10),  # Width x Height in inches
    save_path="high_res_chart.png"
)

# Save with custom DPI
chart.save_chart("chart.png", dpi=600)
```

## Troubleshooting

### Common Issues

**Import Error**: Make sure the `src` directory is in your Python path:
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
```

**Invalid Time Format**: Times must be in "HH:MM" format (24-hour):
- Correct: "23:30", "07:00"
- Incorrect: "11:30 PM", "7:00"

**Empty Chart**: Check that your sleep data list is not empty and contains valid entries.

### Data Validation

Use the validation function to check your data:
```python
from visualization.sleep_utils import validate_sleep_data

try:
    validate_sleep_data(my_sleep_data)
    print("Data is valid!")
except ValueError as e:
    print(f"Data error: {e}")
```

## Dependencies

The modules require:
- `matplotlib >= 3.6.0`
- `numpy >= 1.21.0`
- Python standard library modules (csv, typing, statistics)

Install with:
```bash
pip install matplotlib numpy
```

## File Structure

```
src/
└── visualization/
    ├── __init__.py          # Package initialization
    ├── sleep_chart.py       # Main chart functionality
    └── sleep_utils.py       # Utility functions

examples/
└── sleep_chart_demo.py     # Demo script

notebooks/
└── sleep_regularity_example.ipynb  # Jupyter notebook example

docs/
└── sleep_chart_guide.md    # This guide
```