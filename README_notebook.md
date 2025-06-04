# Using the Data Overview Notebook

## 📊 What It Does

The `notebooks/data_overview.ipynb` notebook provides a quick overview of all data sources in your health database:

- **Database Statistics**: Schema version, total records, table overview
- **Users Data**: User information and settings
- **Activity Data**: Daily steps, calories, distance with preview
- **Sleep Data**: Sleep stages, duration, efficiency with preview
- **Heart Rate Data**: Ready for future heart rate imports
- **Quick Summary**: Key metrics and averages across all data types

## 🚀 How to Use

### 1. Start Jupyter Notebook

```bash
# Make sure you're in the project directory and virtual environment is active
jupyter notebook
```

### 2. Open the Notebook

Navigate to `notebooks/data_overview.ipynb` in the Jupyter interface.

### 3. Run All Cells

- Click "Cell" → "Run All" in the menu, or
- Use Shift+Enter to run each cell individually

## 📋 Expected Output

The notebook will show:

```
📊 Health Data Analytics System
========================================

🔗 Connecting to database: /path/to/health_data.db
✅ Connected successfully!

📈 Database Statistics
=========================
Schema Version: 2.0
Total Records: 1,001
Total Tables: 4

📋 Table Overview
====================
users: 1 records
daily_activity: 500 records
   📅 2023-01-04 to 2024-09-28
sleep_data: 500 records
   📅 2023-01-04 to 2024-09-28
heart_rate_data: 0 records
```

### Data Previews

Each section will show `df.head()` output for the respective data:

- **Users**: User ID, name, email, timezone
- **Activity**: Date, steps, calories, distance, run_distance
- **Sleep**: Date, sleep start/end times, sleep stage durations, efficiency
- **Heart Rate**: Schema info (no data yet)

### Summary Statistics

Final section shows averages and key metrics:
- Average daily steps and calories
- Average sleep duration and efficiency
- Date ranges for all data types

## 🔧 Customization

You can modify the notebook to:

- Change the number of records shown (`LIMIT 5` → `LIMIT 10`)
- Add specific date range filters
- Calculate additional statistics
- Create visualizations

## ⚠️ Troubleshooting

If you see errors:

1. **Database not found**: Run `python scripts/setup_new_database.py`
2. **Import errors**: Ensure you're in the project root directory
3. **Module not found**: Check that virtual environment is activated

## 🎯 Next Steps

After reviewing the data overview:

1. Use `notebooks/health_data_exploration.ipynb` for detailed analysis
2. Import additional data sources
3. Create custom analysis notebooks
4. Set up automated reporting