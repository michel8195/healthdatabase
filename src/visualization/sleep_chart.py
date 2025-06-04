"""
Sleep Regularity Chart Generator

This module provides functionality to create sleep regularity charts
similar to health app visualizations, showing sleep patterns across days.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple, Optional, Dict
import numpy as np


class SleepRegularityChart:
    """
    A class to generate sleep regularity charts showing sleep patterns across days.

    The chart displays sleep duration bars for each day, with bedtime at the
    bottom and wake time at the top, similar to health app sleep visualizations.
    """

    def __init__(self, figsize: Tuple[float, float] = (12, 8)):
        """
        Initialize the sleep regularity chart.

        Args:
            figsize: Tuple of (width, height) for the figure size in inches
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None
        self.sleep_color = '#4A90E2'  # Blue color similar to the image
        self.background_color = '#F8F9FA'
        self.text_color = '#2C3E50'

    def _time_to_hours(self, time_str: str) -> float:
        """
        Convert time string (HH:MM) to hours as float.

        Args:
            time_str: Time in format "HH:MM"

        Returns:
            Time as hours (e.g., "14:30" -> 14.5)
        """
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours + minutes / 60.0
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM format.")

    def _calculate_sleep_duration(self, bedtime: str, wake_time: str) -> float:
        """
        Calculate sleep duration in hours, handling overnight sleep.

        Args:
            bedtime: Bedtime in "HH:MM" format
            wake_time: Wake time in "HH:MM" format

        Returns:
            Sleep duration in hours
        """
        bed_hours = self._time_to_hours(bedtime)
        wake_hours = self._time_to_hours(wake_time)

        # Handle overnight sleep (bedtime after wake time)
        if bed_hours > wake_hours:
            return (24 - bed_hours) + wake_hours
        else:
            return wake_hours - bed_hours

    def _setup_chart(self, title: str = "SLEEP REGULARITY"):
        """Setup the chart with proper styling and layout."""
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.fig.patch.set_facecolor(self.background_color)
        self.ax.set_facecolor(self.background_color)

        # Remove spines
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        # Set title
        self.ax.text(0.02, 0.95, title, transform=self.ax.transAxes,
                    fontsize=16, fontweight='bold', color=self.text_color,
                    verticalalignment='top')

        # Add sleep icon placeholder (you can replace with actual icon)
        self.ax.text(0.01, 0.95, '🌙', transform=self.ax.transAxes,
                    fontsize=16, verticalalignment='top')

    def _draw_time_axis(self, y_positions: List[float]):
        """Draw the time axis on the left side."""
        time_labels = ['20:00', '03:30', '11:00']

        for i, (time_label, y_pos) in enumerate(zip(time_labels, y_positions)):
            self.ax.text(-0.1, y_pos, time_label, transform=self.ax.transData,
                        fontsize=10, color=self.text_color, ha='right', va='center')

    def plot_sleep_data(self, sleep_data: List[Dict[str, str]],
                       title: str = "SLEEP REGULARITY") -> None:
        """
        Plot sleep regularity data.

        Args:
            sleep_data: List of dictionaries with keys: 'day', 'bedtime', 'wake_time'
                       Example: [{'day': 'T', 'bedtime': '22:39', 'wake_time': '07:47'}, ...]
            title: Chart title
        """
        self._setup_chart(title)

        if not sleep_data:
            raise ValueError("Sleep data cannot be empty")

        # Calculate positions
        n_days = len(sleep_data)
        x_positions = np.linspace(0.15, 0.85, n_days)
        bar_width = 0.6 / n_days

        # Time axis setup (24-hour scale mapped to 0-1)
        y_bottom = 0.15  # 20:00
        y_middle = 0.4   # 03:30 (midnight area)
        y_top = 0.85     # 11:00

        # Draw time axis
        self._draw_time_axis([y_bottom, y_middle, y_top])

        # Plot sleep bars for each day
        for i, data in enumerate(sleep_data):
            day = data['day']
            bedtime = data['bedtime']
            wake_time = data['wake_time']

            # Convert times to y-coordinates (normalized 0-1 scale)
            bed_hours = self._time_to_hours(bedtime)
            wake_hours = self._time_to_hours(wake_time)

            # Map hours to y-coordinates (20:00 to 11:00 next day)
            # 20:00 (20) -> 0.15, 03:30 (3.5) -> 0.4, 11:00 (11) -> 0.85
            def hours_to_y(hours):
                if hours >= 20:  # Evening (20:00-24:00)
                    return 0.15 + (hours - 20) / 4 * 0.08  # 20:00-24:00 maps to 0.15-0.23
                elif hours <= 11:  # Morning (00:00-11:00)
                    return 0.23 + hours / 11 * 0.62  # 00:00-11:00 maps to 0.23-0.85
                else:  # Afternoon (11:00-20:00) - unusual sleep times
                    return 0.85 + (hours - 11) / 9 * 0.1  # 11:00-20:00 maps to 0.85-0.95

            bed_y = hours_to_y(bed_hours)
            wake_y = hours_to_y(wake_hours)

            # Handle overnight sleep
            if bed_hours > wake_hours:
                # Sleep spans midnight
                bar_height = (0.23 - bed_y) + (wake_y - 0.23)
                bar_bottom = bed_y
            else:
                # Same day sleep
                bar_height = wake_y - bed_y
                bar_bottom = bed_y

            # Draw sleep bar
            bar = patches.Rectangle((x_positions[i] - bar_width/2, bar_bottom),
                                  bar_width, bar_height,
                                  facecolor=self.sleep_color,
                                  edgecolor='none',
                                  alpha=0.8)
            self.ax.add_patch(bar)

            # Add time labels
            self.ax.text(x_positions[i], wake_y + 0.03, wake_time,
                        ha='center', va='bottom', fontsize=9,
                        color=self.sleep_color, fontweight='bold')

            self.ax.text(x_positions[i], bed_y - 0.03, bedtime,
                        ha='center', va='top', fontsize=9,
                        color=self.sleep_color, fontweight='bold')

            # Add day label
            self.ax.text(x_positions[i], 0.05, day,
                        ha='center', va='center', fontsize=11,
                        color='#95A5A6', fontweight='bold')

        # Set axis limits and remove ticks
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        plt.tight_layout()

    def save_chart(self, filename: str, dpi: int = 300, bbox_inches: str = 'tight'):
        """
        Save the chart to file.

        Args:
            filename: Output filename
            dpi: Dots per inch for image quality
            bbox_inches: Bounding box mode
        """
        if self.fig is None:
            raise ValueError("No chart to save. Call plot_sleep_data() first.")

        self.fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches,
                        facecolor=self.background_color, edgecolor='none')

    def show(self):
        """Display the chart."""
        if self.fig is None:
            raise ValueError("No chart to show. Call plot_sleep_data() first.")
        plt.show()

    def close(self):
        """Close the chart figure."""
        if self.fig is not None:
            plt.close(self.fig)


def create_sleep_chart(sleep_data: List[Dict[str, str]],
                      title: str = "SLEEP REGULARITY",
                      figsize: Tuple[float, float] = (12, 8),
                      save_path: Optional[str] = None) -> SleepRegularityChart:
    """
    Convenience function to create a sleep regularity chart.

    Args:
        sleep_data: List of sleep data dictionaries
        title: Chart title
        figsize: Figure size tuple
        save_path: Optional path to save the chart

    Returns:
        SleepRegularityChart instance

    Example:
        >>> sleep_data = [
        ...     {'day': 'T', 'bedtime': '22:39', 'wake_time': '07:47'},
        ...     {'day': 'F', 'bedtime': '21:31', 'wake_time': '09:04'},
        ...     {'day': 'S', 'bedtime': '22:17', 'wake_time': '08:32'},
        ...     {'day': 'S', 'bedtime': '22:18', 'wake_time': '08:24'},
        ...     {'day': 'M', 'bedtime': '00:06', 'wake_time': '07:01'},
        ...     {'day': 'T', 'bedtime': '21:49', 'wake_time': '08:04'},
        ...     {'day': 'W', 'bedtime': '22:10', 'wake_time': '07:05'}
        ... ]
        >>> chart = create_sleep_chart(sleep_data)
        >>> chart.show()
    """
    chart = SleepRegularityChart(figsize=figsize)
    chart.plot_sleep_data(sleep_data, title)

    if save_path:
        chart.save_chart(save_path)

    return chart