#!/usr/bin/env python3
"""
Health Data Analytics Dashboard

Interactive web UI for visualizing health data with date range selection,
daily values, and moving averages (7-day and 30-day).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import DatabaseConnection

# Page configuration
st.set_page_config(
    page_title="Health Data Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_activity_data():
    """Load activity data from database."""
    try:
        db = DatabaseConnection("data/health_data.db")
        
        query = """
        SELECT 
            date,
            steps,
            calories,
            distance,
            run_distance,
            active_minutes,
            data_source
        FROM daily_activity 
        WHERE date >= date('now', '-3 years')
        ORDER BY date
        """
        
        results = db.execute_query(query)
        if not results:
            return pd.DataFrame()
        
        # Convert sqlite3.Row objects to dictionaries
        data = []
        for row in results:
            data.append(dict(row))
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"Error loading activity data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_heart_rate_data():
    """Load heart rate data from database."""
    try:
        db = DatabaseConnection("data/health_data.db")
        
        query = """
        SELECT 
            timestamp,
            heart_rate,
            resting_hr,
            max_hr,
            data_source
        FROM heart_rate_data 
        WHERE timestamp >= datetime('now', '-3 years')
        ORDER BY timestamp
        """
        
        results = db.execute_query(query)
        if not results:
            return pd.DataFrame()
        
        # Convert sqlite3.Row objects to dictionaries
        data = []
        for row in results:
            data.append(dict(row))
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        return df
    except Exception as e:
        st.error(f"Error loading heart rate data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_sport_data():
    """Load sport data from database."""
    try:
        db = DatabaseConnection("data/health_data.db")
        
        query = """
        SELECT 
            start_time,
            sport_type,
            duration_seconds,
            distance_meters,
            calories,
            avg_pace_per_meter,
            data_source
        FROM sport_data 
        WHERE start_time >= datetime('now', '-3 years')
        ORDER BY start_time
        """
        
        results = db.execute_query(query)
        if not results:
            return pd.DataFrame()
        
        # Convert sqlite3.Row objects to dictionaries
        data = []
        for row in results:
            data.append(dict(row))
        
        df = pd.DataFrame(data)
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['date'] = df['start_time'].dt.date
        
        # Convert duration to minutes and distance to km
        df['duration_minutes'] = df['duration_seconds'] / 60
        df['distance_km'] = df['distance_meters'] / 1000
        
        # Add sport type labels
        df['sport_name'] = df['sport_type'].map(get_sport_type_mapping())
        
        return df
    except Exception as e:
        st.error(f"Error loading sport data: {e}")
        return pd.DataFrame()

def get_sport_type_mapping():
    """Get mapping of sport type codes to names."""
    return {
        1: 'Running',
        6: 'Cycling', 
        8: 'Swimming',
        9: 'Walking',
        10: 'Hiking',
        17: 'Yoga',
        21: 'Basketball',
        22: 'Football',
        42: 'Tennis',
        52: 'Strength Training',
        53: 'Fitness',
        60: 'Elliptical',
        105: 'Treadmill'
    }

@st.cache_data
def load_sleep_data():
    """Load sleep data from database."""
    try:
        db = DatabaseConnection("data/health_data.db")
        
        query = """
        SELECT 
            date,
            sleep_start,
            sleep_end,
            total_sleep_minutes,
            deep_sleep_minutes,
            light_sleep_minutes,
            rem_sleep_minutes,
            wake_minutes,
            sleep_efficiency,
            data_source
        FROM sleep_data 
        WHERE date >= date('now', '-3 years')
        ORDER BY date
        """
        
        results = db.execute_query(query)
        if not results:
            return pd.DataFrame()
        
        # Convert sqlite3.Row objects to dictionaries
        data = []
        for row in results:
            data.append(dict(row))
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert minutes to hours for better readability
        df['total_sleep_hours'] = df['total_sleep_minutes'] / 60
        df['deep_sleep_hours'] = df['deep_sleep_minutes'] / 60
        df['light_sleep_hours'] = df['light_sleep_minutes'] / 60
        df['rem_sleep_hours'] = df['rem_sleep_minutes'] / 60
        
        # Parse sleep times and extract bed time and wake time
        df['sleep_start_dt'] = pd.to_datetime(df['sleep_start'], utc=True).dt.tz_convert('America/Sao_Paulo')
        df['sleep_end_dt'] = pd.to_datetime(df['sleep_end'], utc=True).dt.tz_convert('America/Sao_Paulo')
        
        # Extract bed time as time of day (in decimal hours)
        df['bed_time_hours'] = df['sleep_start_dt'].dt.hour + df['sleep_start_dt'].dt.minute / 60
        
        # Extract wake time as time of day (in decimal hours)
        df['wake_time_hours'] = df['sleep_end_dt'].dt.hour + df['sleep_end_dt'].dt.minute / 60
        
        return df
    except Exception as e:
        st.error(f"Error loading sleep data: {e}")
        return pd.DataFrame()

def calculate_moving_averages(df, column, date_col='date'):
    """Calculate 7-day and 30-day moving averages."""
    if df.empty or column not in df.columns:
        return df
    
    df = df.copy()
    df[f'{column}_ma7'] = df[column].rolling(window=7, center=True).mean()
    df[f'{column}_ma30'] = df[column].rolling(window=30, center=True).mean()
    
    return df

def create_activity_chart(df, metric, date_range, chart_type='line'):
    """Create activity metric chart with moving averages or bar plots."""
    if df.empty:
        return None
    
    # Filter data by date range
    mask = (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        return None
    
    metric_labels = {
        'steps': 'Steps',
        'calories': 'Calories',
        'distance': 'Distance (m)',
        'run_distance': 'Run Distance (m)',
        'active_minutes': 'Active Minutes'
    }
    
    if chart_type == 'line':
        # Calculate moving averages
        filtered_df = calculate_moving_averages(filtered_df, metric)
        
        # Create line chart
        fig = go.Figure()
        
        # Daily values (lighter)
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[metric],
            mode='lines',
            name='Daily',
            line=dict(color='lightblue', width=1),
            opacity=0.6
        ))
        
        # 7-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma7'],
            mode='lines',
            name='7-day MA',
            line=dict(color='orange', width=2)
        ))
        
        # 30-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma30'],
            mode='lines',
            name='30-day MA',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f"{metric_labels.get(metric, metric).title()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric_labels.get(metric, metric),
            hovermode='x unified',
            height=400
        )
        
    else:  # bar chart
        # Create aggregated data based on chart_type
        if chart_type == 'week':
            filtered_df['period'] = filtered_df['date'].dt.to_period('W-MON')  # Week starting Monday
            period_label = "Week"
            date_format = lambda x: f"Week of {x.start_time.strftime('%Y-%m-%d')}"
        elif chart_type == 'month':
            filtered_df['period'] = filtered_df['date'].dt.to_period('M')
            period_label = "Month"
            date_format = lambda x: x.strftime('%Y-%m')
        elif chart_type == 'quarter':
            filtered_df['period'] = filtered_df['date'].dt.to_period('Q')
            period_label = "Quarter"
            date_format = lambda x: f"Q{x.quarter} {x.year}"
        
        # Calculate averages per period
        agg_data = filtered_df.groupby('period')[metric].mean().reset_index()
        agg_data['period_label'] = agg_data['period'].apply(date_format)
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=agg_data['period_label'],
            y=agg_data[metric],
            name=f'Average {metric_labels.get(metric, metric)}',
            marker_color='steelblue',
            text=[f'{val:.0f}' for val in agg_data[metric]],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Average {metric_labels.get(metric, metric).title()} per {period_label}",
            xaxis_title=period_label,
            yaxis_title=f"Average {metric_labels.get(metric, metric)}",
            height=400,
            xaxis={'tickangle': 45}
        )
    
    return fig

def create_sleep_chart(df, metric, date_range, chart_type='line'):
    """Create sleep metric chart with moving averages or bar plots."""
    if df.empty:
        return None
    
    # Filter data by date range
    mask = (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        return None
    
    metric_labels = {
        'total_sleep_hours': 'Total Sleep (hours)',
        'deep_sleep_hours': 'Deep Sleep (hours)',
        'light_sleep_hours': 'Light Sleep (hours)',
        'rem_sleep_hours': 'REM Sleep (hours)',
        'sleep_efficiency': 'Sleep Efficiency (%)',
        'bed_time_hours': 'Bed Time',
        'wake_time_hours': 'Wake Time'
    }
    
    if chart_type == 'line':
        # Calculate moving averages
        filtered_df = calculate_moving_averages(filtered_df, metric)
        
        # Create line chart
        fig = go.Figure()
        
        # Daily values (lighter)
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[metric],
            mode='lines',
            name='Daily',
            line=dict(color='lightblue', width=1),
            opacity=0.6
        ))
        
        # 7-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma7'],
            mode='lines',
            name='7-day MA',
            line=dict(color='orange', width=2)
        ))
        
        # 30-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma30'],
            mode='lines',
            name='30-day MA',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f"{metric_labels.get(metric, metric).title()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric_labels.get(metric, metric),
            hovermode='x unified',
            height=400
        )
        
    else:  # bar chart
        # Create aggregated data based on chart_type
        if chart_type == 'week':
            filtered_df['period'] = filtered_df['date'].dt.to_period('W-MON')  # Week starting Monday
            period_label = "Week"
            date_format = lambda x: f"Week of {x.start_time.strftime('%Y-%m-%d')}"
        elif chart_type == 'month':
            filtered_df['period'] = filtered_df['date'].dt.to_period('M')
            period_label = "Month"
            date_format = lambda x: x.strftime('%Y-%m')
        elif chart_type == 'quarter':
            filtered_df['period'] = filtered_df['date'].dt.to_period('Q')
            period_label = "Quarter"
            date_format = lambda x: f"Q{x.quarter} {x.year}"
        
        # Calculate averages per period
        agg_data = filtered_df.groupby('period')[metric].mean().reset_index()
        agg_data['period_label'] = agg_data['period'].apply(date_format)
        
        # Create bar chart
        fig = go.Figure()
        
        # Format values based on metric type
        if metric in ['bed_time_hours', 'wake_time_hours']:
            # Convert decimal hours back to time format
            def time_format(val):
                if metric == 'bed_time_hours' and val >= 24:
                    val = val - 24  # Convert back from next-day representation
                hour = int(val)
                minute = int((val - hour) * 60)
                return f'{hour:02d}:{minute:02d}'
            text_format = time_format
        elif 'hours' in metric:
            text_format = lambda val: f'{val:.1f}h'
        elif 'efficiency' in metric:
            text_format = lambda val: f'{val:.1f}%'
        else:
            text_format = lambda val: f'{val:.0f}'
        
        fig.add_trace(go.Bar(
            x=agg_data['period_label'],
            y=agg_data[metric],
            name=f'Average {metric_labels.get(metric, metric)}',
            marker_color='darkslateblue',
            text=[text_format(val) for val in agg_data[metric]],
            textposition='outside'
        ))
        
        layout_config = {
            'title': f"Average {metric_labels.get(metric, metric).title()} per {period_label}",
            'xaxis_title': period_label,
            'yaxis_title': f"Average {metric_labels.get(metric, metric)}",
            'height': 400,
            'xaxis': {'tickangle': 45}
        }
        
        # Custom y-axis formatting for time metrics
        if metric in ['bed_time_hours', 'wake_time_hours']:
            def format_time_tick(val):
                if metric == 'bed_time_hours' and val >= 24:
                    val = val - 24
                hour = int(val)
                minute = int((val - hour) * 60)
                return f'{hour:02d}:{minute:02d}'
            
            # Create custom tick values and labels
            y_min, y_max = agg_data[metric].min(), agg_data[metric].max()
            
            if metric == 'bed_time_hours':
                # For bed time, show times from evening to early morning
                tick_vals = list(range(int(y_min), int(y_max) + 2))
                tick_text = [format_time_tick(val) for val in tick_vals]
            else:
                # For wake time, show normal morning times
                tick_vals = list(range(int(y_min), int(y_max) + 2))
                tick_text = [format_time_tick(val) for val in tick_vals]
            
            layout_config['yaxis'] = {
                'tickvals': tick_vals,
                'ticktext': tick_text
            }
        
        fig.update_layout(**layout_config)
    
    return fig

def aggregate_heart_rate_daily(df):
    """Aggregate heart rate data by day."""
    if df.empty:
        return pd.DataFrame()
    
    # Convert date to pandas datetime for grouping
    df['date_dt'] = pd.to_datetime(df['date'])
    
    # Aggregate by date
    daily_hr = df.groupby('date_dt').agg({
        'heart_rate': ['mean', 'min', 'max', 'std'],
        'resting_hr': 'mean',
        'max_hr': 'mean',
        'data_source': 'first'
    }).reset_index()
    
    # Flatten column names
    daily_hr.columns = ['date', 'avg_hr', 'min_hr', 'max_hr', 'hr_std', 'avg_resting_hr', 'avg_max_hr', 'data_source']
    
    return daily_hr

def create_heart_rate_chart(df, metric, date_range, chart_type='line'):
    """Create heart rate metric chart with moving averages or bar plots."""
    if df.empty:
        return None
    
    # Aggregate to daily data first
    daily_df = aggregate_heart_rate_daily(df)
    
    if daily_df.empty:
        return None
    
    # Filter data by date range
    mask = (daily_df['date'] >= date_range[0]) & (daily_df['date'] <= date_range[1])
    filtered_df = daily_df[mask].copy()
    
    if filtered_df.empty:
        return None
    
    metric_labels = {
        'avg_hr': 'Average Heart Rate (bpm)',
        'min_hr': 'Minimum Heart Rate (bpm)',
        'max_hr': 'Maximum Heart Rate (bpm)',
        'hr_std': 'Heart Rate Variability (std)',
        'avg_resting_hr': 'Average Resting HR (bpm)',
        'avg_max_hr': 'Average Max HR (bpm)'
    }
    
    if chart_type == 'line':
        # Calculate moving averages
        filtered_df = calculate_moving_averages(filtered_df, metric)
        
        # Create line chart
        fig = go.Figure()
        
        # Daily values (lighter)
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[metric],
            mode='lines',
            name='Daily',
            line=dict(color='lightcoral', width=1),
            opacity=0.6
        ))
        
        # 7-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma7'],
            mode='lines',
            name='7-day MA',
            line=dict(color='orange', width=2)
        ))
        
        # 30-day moving average
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[f'{metric}_ma30'],
            mode='lines',
            name='30-day MA',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f"{metric_labels.get(metric, metric).title()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric_labels.get(metric, metric),
            hovermode='x unified',
            height=400
        )
        
    else:  # bar chart
        # Create aggregated data based on chart_type
        if chart_type == 'week':
            filtered_df['period'] = filtered_df['date'].dt.to_period('W-MON')  # Week starting Monday
            period_label = "Week"
            date_format = lambda x: f"Week of {x.start_time.strftime('%Y-%m-%d')}"
        elif chart_type == 'month':
            filtered_df['period'] = filtered_df['date'].dt.to_period('M')
            period_label = "Month"
            date_format = lambda x: x.strftime('%Y-%m')
        elif chart_type == 'quarter':
            filtered_df['period'] = filtered_df['date'].dt.to_period('Q')
            period_label = "Quarter"
            date_format = lambda x: f"Q{x.quarter} {x.year}"
        
        # Calculate averages per period
        agg_data = filtered_df.groupby('period')[metric].mean().reset_index()
        agg_data['period_label'] = agg_data['period'].apply(date_format)
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=agg_data['period_label'],
            y=agg_data[metric],
            name=f'Average {metric_labels.get(metric, metric)}',
            marker_color='crimson',
            text=[f'{val:.0f}' for val in agg_data[metric]],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Average {metric_labels.get(metric, metric).title()} per {period_label}",
            xaxis_title=period_label,
            yaxis_title=f"Average {metric_labels.get(metric, metric)}",
            height=400,
            xaxis={'tickangle': 45}
        )
    
    return fig

def analyze_sport_data_by_period(df, period='weekly'):
    """Analyze sport data by time period showing activity counts and total time."""
    if df.empty:
        return pd.DataFrame()
    
    # Convert start_time to datetime if needed
    df['start_time'] = pd.to_datetime(df['start_time'])
    
    if period == 'weekly':
        df['period'] = df['start_time'].dt.to_period('W-MON')
        period_label = "Week"
    elif period == 'monthly':
        df['period'] = df['start_time'].dt.to_period('M')
        period_label = "Month"
    else:
        raise ValueError("Period must be 'weekly' or 'monthly'")
    
    # Group by period and sport type
    analysis = df.groupby(['period', 'sport_name']).agg({
        'start_time': 'count',  # Number of activities
        'duration_minutes': 'sum',  # Total time
        'distance_km': 'sum',  # Total distance
        'calories': 'sum'  # Total calories
    }).reset_index()
    
    # Rename columns for clarity
    analysis.columns = ['period', 'sport_name', 'activity_count', 'total_time_minutes', 'total_distance_km', 'total_calories']
    
    # Convert time to hours for better readability
    analysis['total_time_hours'] = analysis['total_time_minutes'] / 60
    
    # Format period labels
    if period == 'weekly':
        analysis['period_label'] = analysis['period'].apply(lambda x: f"Week of {x.start_time.strftime('%Y-%m-%d')}")
    else:
        analysis['period_label'] = analysis['period'].apply(lambda x: x.strftime('%Y-%m'))
    
    return analysis

def create_sport_activity_chart(df, metric='activity_count', period='weekly'):
    """Create sport activity chart showing counts or time by sport type."""
    if df.empty:
        return None
    
    analysis = analyze_sport_data_by_period(df, period)
    
    if analysis.empty:
        return None
    
    period_label = "Weekly" if period == 'weekly' else "Monthly"
    
    if metric == 'activity_count':
        title = f"{period_label} Activity Count by Sport Type"
        y_title = "Number of Activities"
        value_col = 'activity_count'
        text_format = lambda x: f'{int(x)}'
    else:  # total_time_hours
        title = f"{period_label} Total Time by Sport Type"
        y_title = "Total Time (hours)"
        value_col = 'total_time_hours'
        text_format = lambda x: f'{x:.1f}h'
    
    # Create stacked bar chart
    fig = go.Figure()
    
    # Get unique periods and sport types
    periods = analysis['period_label'].unique()
    sport_types = analysis['sport_name'].unique()
    
    # Create a bar for each sport type
    colors = px.colors.qualitative.Set3
    for i, sport in enumerate(sport_types):
        sport_data = analysis[analysis['sport_name'] == sport]
        
        # Create full period series with zeros for missing periods
        full_data = []
        full_periods = []
        for period in periods:
            period_value = sport_data[sport_data['period_label'] == period][value_col]
            if len(period_value) > 0:
                full_data.append(period_value.iloc[0])
            else:
                full_data.append(0)
            full_periods.append(period)
        
        fig.add_trace(go.Bar(
            name=sport,
            x=full_periods,
            y=full_data,
            text=[text_format(val) if val > 0 else '' for val in full_data],
            textposition='inside',
            marker_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=f"{period_label.split()[0]} Period",
        yaxis_title=y_title,
        barmode='stack',
        height=500,
        xaxis={'tickangle': 45},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def main():
    """Main dashboard application."""
    st.title("📊 Health Data Analytics Dashboard")
    st.markdown("Interactive visualization of your health data with daily values and moving averages")
    
    # Load data
    with st.spinner("Loading data..."):
        activity_df = load_activity_data()
        sleep_df = load_sleep_data()
        heart_rate_df = load_heart_rate_data()
        sport_df = load_sport_data()
    
    # Debug information
    st.sidebar.header("🔍 Data Debug Info")
    st.sidebar.write(f"Activity records: {len(activity_df)}")
    st.sidebar.write(f"Sleep records: {len(sleep_df)}")
    st.sidebar.write(f"Heart rate records: {len(heart_rate_df)}")
    st.sidebar.write(f"Sport records: {len(sport_df)}")
    
    if not activity_df.empty:
        st.sidebar.write(f"Activity date range: {activity_df['date'].min().date()} to {activity_df['date'].max().date()}")
    if not sleep_df.empty:
        st.sidebar.write(f"Sleep date range: {sleep_df['date'].min().date()} to {sleep_df['date'].max().date()}")
    if not heart_rate_df.empty:
        st.sidebar.write(f"Heart rate date range: {heart_rate_df['date'].min()} to {heart_rate_df['date'].max()}")
    if not sport_df.empty:
        st.sidebar.write(f"Sport date range: {sport_df['date'].min()} to {sport_df['date'].max()}")
    
    if activity_df.empty and sleep_df.empty and heart_rate_df.empty and sport_df.empty:
        st.error("No data found. Please ensure your database contains data.")
        st.info("Run the import scripts to populate your database with health data.")
        
        # Show more debug info
        with st.expander("🔧 Debug Information"):
            st.write("Database file exists:", Path("data/health_data.db").exists())
            try:
                from src.database.connection import DatabaseConnection
                db = DatabaseConnection("data/health_data.db")
                tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                st.write("Available tables:", [dict(t)['name'] for t in tables])
            except Exception as e:
                st.write("Database error:", str(e))
        return
    
    # Sidebar controls
    st.sidebar.header("📅 Date Range Selection")
    
    # Determine available date range
    all_dates = []
    if not activity_df.empty:
        all_dates.extend(activity_df['date'].tolist())
    if not sleep_df.empty:
        all_dates.extend(sleep_df['date'].tolist())
    if not heart_rate_df.empty:
        all_dates.extend(pd.to_datetime(heart_rate_df['date']).tolist())
    if not sport_df.empty:
        all_dates.extend(pd.to_datetime(sport_df['date']).tolist())
    
    if not all_dates:
        st.error("No valid dates found in the data.")
        return
    
    min_date = min(all_dates).date()
    max_date = max(all_dates).date()
    
    # Date range picker
    default_start = max(min_date, (datetime.now() - timedelta(days=365)).date())
    
    date_range = st.sidebar.date_input(
        "Select date range",
        value=[default_start, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) != 2:
        st.warning("Please select both start and end dates.")
        return
    
    # Convert to datetime for filtering
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])
    
    # Data source filter
    st.sidebar.header("📱 Data Source")
    all_sources = set()
    if not activity_df.empty:
        all_sources.update(activity_df['data_source'].unique())
    if not sleep_df.empty:
        all_sources.update(sleep_df['data_source'].unique())
    if not heart_rate_df.empty:
        all_sources.update(heart_rate_df['data_source'].unique())
    if not sport_df.empty:
        all_sources.update(sport_df['data_source'].unique())
    
    selected_sources = st.sidebar.multiselect(
        "Filter by data source",
        options=list(all_sources),
        default=list(all_sources)
    )
    
    # Chart type selection
    st.sidebar.header("📊 Chart Options")
    chart_type = st.sidebar.selectbox(
        "Chart Type",
        options=['line', 'week', 'month', 'quarter'],
        format_func=lambda x: {
            'line': '📈 Line Chart (Daily + Moving Averages)',
            'week': '📊 Bar Chart (Weekly Averages)',
            'month': '📊 Bar Chart (Monthly Averages)', 
            'quarter': '📊 Bar Chart (Quarterly Averages)'
        }[x],
        index=1
    )
    
    # Filter data by source
    if selected_sources:
        if not activity_df.empty:
            activity_df = activity_df[activity_df['data_source'].isin(selected_sources)]
        if not sleep_df.empty:
            sleep_df = sleep_df[sleep_df['data_source'].isin(selected_sources)]
        if not heart_rate_df.empty:
            heart_rate_df = heart_rate_df[heart_rate_df['data_source'].isin(selected_sources)]
        if not sport_df.empty:
            sport_df = sport_df[sport_df['data_source'].isin(selected_sources)]
    
    # Summary statistics
    st.header("📈 Summary Statistics")
    
    # Filter data for summary
    if not activity_df.empty:
        activity_summary = activity_df[
            (activity_df['date'] >= start_date) & 
            (activity_df['date'] <= end_date)
        ]
    else:
        activity_summary = pd.DataFrame()
    
    if not sleep_df.empty:
        sleep_summary = sleep_df[
            (sleep_df['date'] >= start_date) & 
            (sleep_df['date'] <= end_date)
        ]
    else:
        sleep_summary = pd.DataFrame()
    
    if not heart_rate_df.empty:
        # Aggregate heart rate to daily for summary
        hr_daily = aggregate_heart_rate_daily(heart_rate_df)
        if not hr_daily.empty:
            hr_summary = hr_daily[
                (hr_daily['date'] >= start_date) & 
                (hr_daily['date'] <= end_date)
            ]
        else:
            hr_summary = pd.DataFrame()
    else:
        hr_summary = pd.DataFrame()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not activity_summary.empty:
            avg_steps = activity_summary['steps'].mean()
            st.metric("Avg Daily Steps", f"{avg_steps:,.0f}")
        else:
            st.metric("Avg Daily Steps", "No data")
    
    with col2:
        if not activity_summary.empty:
            avg_calories = activity_summary['calories'].mean()
            st.metric("Avg Daily Calories", f"{avg_calories:,.0f}")
        else:
            st.metric("Avg Daily Calories", "No data")
    
    with col3:
        if not sleep_summary.empty:
            avg_sleep = sleep_summary['total_sleep_minutes'].mean() / 60
            st.metric("Avg Sleep Hours", f"{avg_sleep:.1f}h")
        else:
            st.metric("Avg Sleep Hours", "No data")
    
    with col4:
        if not hr_summary.empty:
            avg_hr = hr_summary['avg_hr'].mean()
            st.metric("Avg Heart Rate", f"{avg_hr:.0f} bpm")
        else:
            st.metric("Avg Heart Rate", "No data")
    
    # Additional heart rate metrics if available
    if not hr_summary.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_resting = hr_summary['avg_resting_hr'].mean()
            if not pd.isna(avg_resting):
                st.metric("Avg Resting HR", f"{avg_resting:.0f} bpm")
            else:
                st.metric("Avg Resting HR", "No data")
        
        with col2:
            avg_max = hr_summary['avg_max_hr'].mean()
            if not pd.isna(avg_max):
                st.metric("Avg Max HR", f"{avg_max:.0f} bpm")
            else:
                st.metric("Avg Max HR", "No data")
        
        with col3:
            if not sleep_summary.empty:
                avg_efficiency = sleep_summary['sleep_efficiency'].mean()
                st.metric("Avg Sleep Efficiency", f"{avg_efficiency:.1f}%")
            else:
                st.metric("Avg Sleep Efficiency", "No data")
        
        with col4:
            avg_variability = hr_summary['hr_std'].mean()
            if not pd.isna(avg_variability):
                st.metric("HR Variability", f"{avg_variability:.1f}")
            else:
                st.metric("HR Variability", "No data")
    else:
        # Show sleep efficiency in original location if no HR data
        if not sleep_summary.empty:
            st.columns(3)  # spacer
            col4 = st.columns(1)[0]
            with col4:
                avg_efficiency = sleep_summary['sleep_efficiency'].mean()
                st.metric("Avg Sleep Efficiency", f"{avg_efficiency:.1f}%")
    
    # Chart type description
    if chart_type == 'line':
        st.info("📈 **Line Chart Mode**: Shows daily values with 7-day and 30-day moving averages to identify trends.")
    else:
        period_names = {'week': 'Weekly', 'month': 'Monthly', 'quarter': 'Quarterly'}
        st.info(f"📊 **Bar Chart Mode**: Shows average values per {chart_type} for easy comparison of {period_names[chart_type].lower()} performance.")
    
    # Activity Data Visualization
    if not activity_df.empty:
        st.header("🚶 Activity Data")
        
        activity_tabs = st.tabs(["Steps", "Calories", "Distance", "Run Distance", "Active Minutes"])
        
        activity_metrics = ['steps', 'calories', 'distance', 'run_distance', 'active_minutes']
        
        for tab, metric in zip(activity_tabs, activity_metrics):
            with tab:
                fig = create_activity_chart(activity_df, metric, (start_date, end_date), chart_type)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected date range.")
    
    # Sleep Data Visualization
    if not sleep_df.empty:
        st.header("😴 Sleep Data")
        
        sleep_tabs = st.tabs(["Total Sleep", "Deep Sleep", "Light Sleep", "REM Sleep", "Sleep Efficiency", "Bed Time", "Wake Time"])
        
        sleep_metrics = ['total_sleep_hours', 'deep_sleep_hours', 'light_sleep_hours', 'rem_sleep_hours', 'sleep_efficiency', 'bed_time_hours', 'wake_time_hours']
        
        for tab, metric in zip(sleep_tabs, sleep_metrics):
            with tab:
                fig = create_sleep_chart(sleep_df, metric, (start_date, end_date), chart_type)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected date range.")
    
    # Heart Rate Data Visualization
    if not heart_rate_df.empty:
        st.header("❤️ Heart Rate Data")
        
        heart_rate_tabs = st.tabs(["Average HR", "Min HR", "Max HR", "HR Variability", "Resting HR", "Max HR Daily"])
        
        heart_rate_metrics = ['avg_hr', 'min_hr', 'max_hr', 'hr_std', 'avg_resting_hr', 'avg_max_hr']
        
        for tab, metric in zip(heart_rate_tabs, heart_rate_metrics):
            with tab:
                fig = create_heart_rate_chart(heart_rate_df, metric, (start_date, end_date), chart_type)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected date range.")
    
    # Sport Data Visualization
    if not sport_df.empty:
        st.header("🏃 Sport Data Analysis")
        
        # Filter sport data by date range
        sport_filtered = sport_df[
            (sport_df['date'] >= start_date.date()) & 
            (sport_df['date'] <= end_date.date())
        ]
        
        if not sport_filtered.empty:
            # Sport analysis controls
            col1, col2 = st.columns(2)
            
            with col1:
                sport_period = st.selectbox(
                    "Analysis Period",
                    options=['weekly', 'monthly'],
                    format_func=lambda x: f"{'📅 Weekly' if x == 'weekly' else '📊 Monthly'} Analysis",
                    index=0,
                    key="sport_period"
                )
            
            with col2:
                sport_metric = st.selectbox(
                    "Metric",
                    options=['activity_count', 'total_time_hours'],
                    format_func=lambda x: f"{'🔢 Activity Count' if x == 'activity_count' else '⏱️ Total Time'} per Sport",
                    index=0,
                    key="sport_metric"
                )
            
            # Create sport activity chart
            sport_fig = create_sport_activity_chart(sport_filtered, sport_metric, sport_period)
            if sport_fig:
                st.plotly_chart(sport_fig, use_container_width=True)
                
                # Sport summary statistics
                sport_analysis = analyze_sport_data_by_period(sport_filtered, sport_period)
                if not sport_analysis.empty:
                    st.subheader(f"📊 {sport_period.capitalize()} Sport Summary")
                    
                    # Overall stats
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_activities = sport_analysis['activity_count'].sum()
                        st.metric("Total Activities", f"{total_activities:,}")
                    
                    with col2:
                        total_time = sport_analysis['total_time_hours'].sum()
                        st.metric("Total Time", f"{total_time:.1f}h")
                    
                    with col3:
                        unique_sports = sport_analysis['sport_name'].nunique()
                        st.metric("Sport Types", f"{unique_sports}")
                    
                    with col4:
                        avg_duration = sport_filtered['duration_minutes'].mean()
                        st.metric("Avg Activity Duration", f"{avg_duration:.0f} min")
                    
                    # Top sports by activity count and time
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🏆 Most Frequent Sports")
                        sport_counts = sport_analysis.groupby('sport_name')['activity_count'].sum().sort_values(ascending=False).head(5)
                        for sport, count in sport_counts.items():
                            st.write(f"**{sport}:** {count} activities")
                    
                    with col2:
                        st.subheader("⏱️ Most Time Spent")
                        sport_time = sport_analysis.groupby('sport_name')['total_time_hours'].sum().sort_values(ascending=False).head(5)
                        for sport, time in sport_time.items():
                            st.write(f"**{sport}:** {time:.1f} hours")
            else:
                st.info("No sport data available for the selected date range.")
        else:
            st.info("No sport data available for the selected date range and filters.")
    
    # Correlation Analysis
    if not activity_df.empty and not sleep_df.empty:
        st.header("🔗 Correlation Analysis")
        
        # Merge activity and sleep data by date
        merged_df = pd.merge(
            activity_df[['date', 'steps', 'calories', 'distance', 'active_minutes']],
            sleep_df[['date', 'total_sleep_hours', 'sleep_efficiency', 'deep_sleep_hours']],
            on='date',
            how='inner'
        )
        
        # Add heart rate data if available
        if not heart_rate_df.empty:
            hr_daily = aggregate_heart_rate_daily(heart_rate_df)
            if not hr_daily.empty:
                merged_df = pd.merge(
                    merged_df,
                    hr_daily[['date', 'avg_hr', 'avg_resting_hr', 'hr_std']],
                    on='date',
                    how='left'
                )
        
        # Filter by date range and remove invalid sleep data
        merged_df = merged_df[
            (merged_df['date'] >= start_date) & 
            (merged_df['date'] <= end_date) &
            (merged_df['total_sleep_hours'] > 0)  # Exclude days with no sleep data
        ]
        
        if not merged_df.empty and len(merged_df) > 1:
            st.info(f"📊 **Correlation Analysis**: Analyzing {len(merged_df)} days with both activity and sleep data.")
            
            # Analysis options
            col1, col2 = st.columns(2)
            
            with col1:
                corr_aggregation = st.selectbox(
                    "Aggregation Level",
                    options=['daily', 'weekly', 'monthly'],
                    format_func=lambda x: {
                        'daily': '📅 Daily Analysis',
                        'weekly': '📊 Weekly Analysis', 
                        'monthly': '📈 Monthly Analysis'
                    }[x],
                    index=0,
                    key="correlation_agg"
                )
            
            with col2:
                include_outliers = st.checkbox(
                    "Include outliers",
                    value=True,
                    help="Outliers are data points that fall outside 1.5 * IQR from Q1/Q3"
                )
            
            # Prepare data based on aggregation level
            if corr_aggregation == 'daily':
                agg_df = merged_df.copy()
                period_label = "Daily"
                date_col = 'date'
            elif corr_aggregation == 'weekly':
                # Group by week
                merged_df['week'] = merged_df['date'].dt.to_period('W-MON')
                agg_df = merged_df.groupby('week').agg({
                    'steps': 'mean',  # Average steps per week
                    'total_sleep_hours': 'mean',  # Average sleep hours per week
                    'sleep_efficiency': 'mean',
                    'deep_sleep_hours': 'mean',
                    'calories': 'mean',
                    'active_minutes': 'mean'
                }).reset_index()
                agg_df['period_label'] = agg_df['week'].apply(lambda x: f"Week of {x.start_time.strftime('%Y-%m-%d')}")
                period_label = "Weekly"
                date_col = 'period_label'
            else:  # monthly
                # Group by month
                merged_df['month'] = merged_df['date'].dt.to_period('M')
                agg_df = merged_df.groupby('month').agg({
                    'steps': 'mean',  # Average steps per month
                    'total_sleep_hours': 'mean',  # Average sleep hours per month
                    'sleep_efficiency': 'mean',
                    'deep_sleep_hours': 'mean',
                    'calories': 'mean',
                    'active_minutes': 'mean'
                }).reset_index()
                agg_df['period_label'] = agg_df['month'].apply(lambda x: x.strftime('%Y-%m'))
                period_label = "Monthly"
                date_col = 'period_label'
            
            if len(agg_df) > 1:
                # Detect outliers using IQR method
                def detect_outliers(data, column):
                    Q1 = data[column].quantile(0.25)
                    Q3 = data[column].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    return (data[column] < lower_bound) | (data[column] > upper_bound)
                
                # Identify outliers for both steps and sleep hours
                steps_outliers = detect_outliers(agg_df, 'steps')
                sleep_outliers = detect_outliers(agg_df, 'total_sleep_hours')
                agg_df['is_outlier'] = steps_outliers | sleep_outliers
                
                # Create filtered dataset if outliers should be excluded
                if include_outliers:
                    corr_df = agg_df.copy()
                    outlier_info = f"Including {agg_df['is_outlier'].sum()} outliers"
                else:
                    corr_df = agg_df[~agg_df['is_outlier']].copy()
                    outlier_info = f"Excluding {agg_df['is_outlier'].sum()} outliers"
                
                if len(corr_df) > 1:
                    st.info(f"📊 **Analysis**: {len(corr_df)} periods used for correlation. {outlier_info}.")
                    
                    # Calculate correlations using filtered data
                    correlations = {
                        'Steps vs Avg Sleep': corr_df['steps'].corr(corr_df['total_sleep_hours']),
                        'Steps vs Sleep Efficiency': corr_df['steps'].corr(corr_df['sleep_efficiency']),
                        'Steps vs Avg Deep Sleep': corr_df['steps'].corr(corr_df['deep_sleep_hours']),
                        'Active Minutes vs Avg Sleep': corr_df['active_minutes'].corr(corr_df['total_sleep_hours']),
                        'Calories vs Avg Sleep': corr_df['calories'].corr(corr_df['total_sleep_hours'])
                    }
                    
                    # Add heart rate correlations if available
                    if 'avg_hr' in corr_df.columns:
                        hr_correlations = {
                            'Steps vs Avg HR': corr_df['steps'].corr(corr_df['avg_hr']),
                            'Sleep vs Avg HR': corr_df['total_sleep_hours'].corr(corr_df['avg_hr']),
                            'Sleep vs Resting HR': corr_df['total_sleep_hours'].corr(corr_df['avg_resting_hr']) if 'avg_resting_hr' in corr_df.columns else None,
                            'Steps vs HR Variability': corr_df['steps'].corr(corr_df['hr_std']) if 'hr_std' in corr_df.columns else None
                        }
                        correlations.update({k: v for k, v in hr_correlations.items() if v is not None and not pd.isna(v)})
                else:
                    st.warning("Not enough data points after outlier filtering.")
                    return
                
                # Display correlation metrics
                num_cols = min(4, len([k for k, v in correlations.items() if not pd.isna(v)]))
                if num_cols == 0:
                    st.warning("No valid correlations could be calculated.")
                    return
                
                # Create dynamic columns based on available correlations
                cols = st.columns(num_cols)
                col_idx = 0
                
                # Primary correlations
                with cols[col_idx]:
                    steps_sleep_corr = correlations['Steps vs Avg Sleep']
                    if not pd.isna(steps_sleep_corr):
                        sleep_label = "Avg Sleep Hours" if corr_aggregation != 'daily' else "Sleep Hours"
                        st.metric(
                            f"Steps ↔ {sleep_label}", 
                            f"{steps_sleep_corr:.3f}",
                            help="Correlation coefficient (-1 to 1). Values closer to ±1 indicate stronger relationships."
                        )
                        col_idx += 1
                
                if col_idx < num_cols:
                    with cols[col_idx]:
                        steps_efficiency_corr = correlations['Steps vs Sleep Efficiency']
                        if not pd.isna(steps_efficiency_corr):
                            st.metric("Steps ↔ Sleep Efficiency", f"{steps_efficiency_corr:.3f}")
                            col_idx += 1
                
                if col_idx < num_cols:
                    with cols[col_idx]:
                        active_sleep_corr = correlations['Active Minutes vs Avg Sleep']
                        if not pd.isna(active_sleep_corr):
                            sleep_label = "Avg Sleep Hours" if corr_aggregation != 'daily' else "Sleep Hours"
                            st.metric(f"Active Minutes ↔ {sleep_label}", f"{active_sleep_corr:.3f}")
                            col_idx += 1
                
                # Heart rate correlations if available
                if col_idx < num_cols and 'Steps vs Avg HR' in correlations:
                    with cols[col_idx]:
                        steps_hr_corr = correlations['Steps vs Avg HR']
                        if not pd.isna(steps_hr_corr):
                            st.metric("Steps ↔ Avg HR", f"{steps_hr_corr:.3f}")
                            col_idx += 1
                
                # Additional heart rate correlations in a new row if needed
                hr_corrs = {k: v for k, v in correlations.items() if 'HR' in k and k != 'Steps vs Avg HR' and not pd.isna(v)}
                if hr_corrs:
                    st.subheader("❤️ Heart Rate Correlations")
                    hr_cols = st.columns(min(3, len(hr_corrs)))
                    for idx, (name, corr) in enumerate(hr_corrs.items()):
                        if idx < len(hr_cols):
                            with hr_cols[idx]:
                                display_name = name.replace('vs', '↔')
                                st.metric(display_name, f"{corr:.3f}")
                
                # Scatter plot for steps vs sleep
                sleep_unit = "hours" if corr_aggregation != 'daily' else "hours"
                sleep_desc = "Average Sleep" if corr_aggregation != 'daily' else "Sleep"
                st.subheader(f"📈 {period_label} Steps vs {sleep_desc} Relationship")
                
                fig_scatter = go.Figure()
                
                # Prepare hover template and labels
                if corr_aggregation == 'daily':
                    hover_template = '<b>%{text}</b><br>Steps: %{x:,}<br>Sleep: %{y:.1f}h<extra></extra>'
                    text_data = agg_df['date'].dt.strftime('%Y-%m-%d')
                    x_title = f"{period_label} Steps"
                    y_title = f"Sleep Hours"
                else:
                    hover_template = '<b>%{text}</b><br>Avg Steps: %{x:,}<br>Avg Sleep: %{y:.1f}h<extra></extra>'
                    text_data = agg_df[date_col]
                    x_title = f"{period_label} Average Steps"
                    y_title = f"Average Sleep Hours"
                
                # Add normal data points
                normal_data = agg_df[~agg_df['is_outlier']]
                if len(normal_data) > 0:
                    fig_scatter.add_trace(go.Scatter(
                        x=normal_data['steps'],
                        y=normal_data['total_sleep_hours'],
                        mode='markers',
                        name=f'{period_label} Data',
                        marker=dict(
                            size=10 if corr_aggregation != 'daily' else 8,
                            color='steelblue',
                            opacity=0.7
                        ),
                        text=normal_data[date_col] if corr_aggregation != 'daily' else normal_data['date'].dt.strftime('%Y-%m-%d'),
                        hovertemplate=hover_template
                    ))
                
                # Add outliers in red
                outlier_data = agg_df[agg_df['is_outlier']]
                if len(outlier_data) > 0:
                    fig_scatter.add_trace(go.Scatter(
                        x=outlier_data['steps'],
                        y=outlier_data['total_sleep_hours'],
                        mode='markers',
                        name='Outliers',
                        marker=dict(
                            size=12 if corr_aggregation != 'daily' else 10,
                            color='red',
                            opacity=0.8,
                            symbol='diamond'
                        ),
                        text=outlier_data[date_col] if corr_aggregation != 'daily' else outlier_data['date'].dt.strftime('%Y-%m-%d'),
                        hovertemplate=hover_template.replace('<extra></extra>', ' (Outlier)<extra></extra>')
                    ))
                
                # Add trend line if correlation exists (using filtered data for calculation)
                if not pd.isna(steps_sleep_corr) and abs(steps_sleep_corr) > 0.1:
                    import numpy as np
                    z = np.polyfit(corr_df['steps'], corr_df['total_sleep_hours'], 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(agg_df['steps'].min(), agg_df['steps'].max(), 100)
                    y_trend = p(x_trend)
                    
                    trend_color = 'darkred' if not include_outliers else 'red'
                    trend_name = f'Trend Line (r={steps_sleep_corr:.3f})'
                    if not include_outliers:
                        trend_name += ' - No Outliers'
                    
                    fig_scatter.add_trace(go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name=trend_name,
                        line=dict(color=trend_color, width=2, dash='dash')
                    ))
                
                fig_scatter.update_layout(
                    title=f"{period_label} Steps vs {sleep_desc} Hours",
                    xaxis_title=x_title,
                    yaxis_title=y_title,
                    height=400,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Interpretation
                if not pd.isna(steps_sleep_corr):
                    st.subheader("🔍 Correlation Interpretation")
                    if abs(steps_sleep_corr) >= 0.7:
                        strength = "Strong"
                    elif abs(steps_sleep_corr) >= 0.3:
                        strength = "Moderate"
                    elif abs(steps_sleep_corr) >= 0.1:
                        strength = "Weak"
                    else:
                        strength = "Very weak"
                    
                    direction = "positive" if steps_sleep_corr > 0 else "negative"
                    
                    time_context = {
                        'daily': 'daily steps and sleep hours',
                        'weekly': 'weekly average steps and average sleep hours',
                        'monthly': 'monthly average steps and average sleep hours'
                    }
                    
                    st.write(f"**{strength} {direction} correlation** between {time_context[corr_aggregation]}.")
                    
                    if steps_sleep_corr > 0.3:
                        activity_context = {
                            'daily': 'Higher daily activity levels are associated with longer sleep duration',
                            'weekly': 'Weeks with higher average activity show better average sleep',
                            'monthly': 'Months with higher average activity show better average sleep'
                        }
                        st.success(f"✅ {activity_context[corr_aggregation]}.")
                    elif steps_sleep_corr < -0.3:
                        activity_context = {
                            'daily': 'Higher daily activity levels are associated with shorter sleep duration',
                            'weekly': 'Weeks with higher average activity show worse average sleep',
                            'monthly': 'Months with higher average activity show worse average sleep'
                        }
                        st.warning(f"⚠️ {activity_context[corr_aggregation]}.")
                    else:
                        st.info(f"ℹ️ No strong relationship detected between {corr_aggregation} activity and sleep.")
                
                # Summary stats for aggregated data
                if corr_aggregation != 'daily':
                    st.subheader(f"📊 {period_label} Summary Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_steps = agg_df['steps'].mean()
                        st.metric(f"Avg {period_label} Steps", f"{avg_steps:,.0f}")
                    
                    with col2:
                        avg_sleep = agg_df['total_sleep_hours'].mean()
                        st.metric(f"Avg Sleep/Day", f"{avg_sleep:.1f}h")
                    
                    with col3:
                        periods_count = len(agg_df)
                        outlier_count = agg_df['is_outlier'].sum()
                        st.metric(f"{period_label.capitalize()} periods", f"{periods_count} ({outlier_count} outliers)")
                    
                    with col4:
                        date_range_text = f"{len(merged_df)} days"
                        st.metric("Days analyzed", date_range_text)
            
            else:
                st.warning(f"Not enough {corr_aggregation} periods for correlation analysis.")
        
        else:
            st.warning("Not enough overlapping data for correlation analysis.")
    
    # Data Export
    st.header("📥 Data Export")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not activity_df.empty:
            activity_csv = activity_df.to_csv(index=False)
            st.download_button(
                label="Download Activity Data (CSV)",
                data=activity_csv,
                file_name=f"activity_data_{date_range[0]}_{date_range[1]}.csv",
                mime="text/csv"
            )
    
    with col2:
        if not sleep_df.empty:
            sleep_csv = sleep_df.to_csv(index=False)
            st.download_button(
                label="Download Sleep Data (CSV)",
                data=sleep_csv,
                file_name=f"sleep_data_{date_range[0]}_{date_range[1]}.csv",
                mime="text/csv"
            )
    
    with col3:
        if not heart_rate_df.empty:
            hr_csv = heart_rate_df.to_csv(index=False)
            st.download_button(
                label="Download Heart Rate Data (CSV)",
                data=hr_csv,
                file_name=f"heart_rate_data_{date_range[0]}_{date_range[1]}.csv",
                mime="text/csv"
            )
    
    with col4:
        if not sport_df.empty:
            sport_csv = sport_df.to_csv(index=False)
            st.download_button(
                label="Download Sport Data (CSV)",
                data=sport_csv,
                file_name=f"sport_data_{date_range[0]}_{date_range[1]}.csv",
                mime="text/csv"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit and Plotly for interactive health data analytics*")

if __name__ == "__main__":
    main()