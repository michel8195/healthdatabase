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
def load_sleep_data():
    """Load sleep data from database."""
    try:
        db = DatabaseConnection("data/health_data.db")
        
        query = """
        SELECT 
            date,
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
        'sleep_efficiency': 'Sleep Efficiency (%)'
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
        if 'hours' in metric:
            text_format = lambda val: f'{val:.1f}h'
            value_format = 1
        elif 'efficiency' in metric:
            text_format = lambda val: f'{val:.1f}%'
            value_format = 1
        else:
            text_format = lambda val: f'{val:.0f}'
            value_format = 0
        
        fig.add_trace(go.Bar(
            x=agg_data['period_label'],
            y=agg_data[metric],
            name=f'Average {metric_labels.get(metric, metric)}',
            marker_color='darkslateblue',
            text=[text_format(val) for val in agg_data[metric]],
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

def main():
    """Main dashboard application."""
    st.title("📊 Health Data Analytics Dashboard")
    st.markdown("Interactive visualization of your health data with daily values and moving averages")
    
    # Load data
    with st.spinner("Loading data..."):
        activity_df = load_activity_data()
        sleep_df = load_sleep_data()
    
    # Debug information
    st.sidebar.header("🔍 Data Debug Info")
    st.sidebar.write(f"Activity records: {len(activity_df)}")
    st.sidebar.write(f"Sleep records: {len(sleep_df)}")
    
    if not activity_df.empty:
        st.sidebar.write(f"Activity date range: {activity_df['date'].min().date()} to {activity_df['date'].max().date()}")
    if not sleep_df.empty:
        st.sidebar.write(f"Sleep date range: {sleep_df['date'].min().date()} to {sleep_df['date'].max().date()}")
    
    if activity_df.empty and sleep_df.empty:
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
        index=0
    )
    
    # Filter data by source
    if selected_sources:
        if not activity_df.empty:
            activity_df = activity_df[activity_df['data_source'].isin(selected_sources)]
        if not sleep_df.empty:
            sleep_df = sleep_df[sleep_df['data_source'].isin(selected_sources)]
    
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
        if not sleep_summary.empty:
            avg_efficiency = sleep_summary['sleep_efficiency'].mean()
            st.metric("Avg Sleep Efficiency", f"{avg_efficiency:.1f}%")
        else:
            st.metric("Avg Sleep Efficiency", "No data")
    
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
        
        sleep_tabs = st.tabs(["Total Sleep", "Deep Sleep", "Light Sleep", "REM Sleep", "Sleep Efficiency"])
        
        sleep_metrics = ['total_sleep_hours', 'deep_sleep_hours', 'light_sleep_hours', 'rem_sleep_hours', 'sleep_efficiency']
        
        for tab, metric in zip(sleep_tabs, sleep_metrics):
            with tab:
                fig = create_sleep_chart(sleep_df, metric, (start_date, end_date), chart_type)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected date range.")
    
    # Data Export
    st.header("📥 Data Export")
    col1, col2 = st.columns(2)
    
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
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit and Plotly for interactive health data analytics*")

if __name__ == "__main__":
    main()