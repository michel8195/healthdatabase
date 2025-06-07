#!/usr/bin/env python3
"""
Quick launcher for the Health Data Analytics Dashboard.

This script launches the Streamlit dashboard with proper configuration.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit dashboard."""
    app_path = Path(__file__).parent / "app.py"
    
    print("🚀 Starting Health Data Analytics Dashboard...")
    print("📊 The dashboard will open in your default browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Thank you for using Health Data Analytics!")

if __name__ == "__main__":
    main()