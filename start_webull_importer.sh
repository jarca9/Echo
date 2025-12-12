#!/bin/bash
# Start the Webull automatic trade importer

cd "$(dirname "$0")"

echo "Starting Webull Automatic Trade Importer..."
echo "This will monitor Webull log files and automatically import trades."
echo "Press Ctrl+C to stop."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q watchdog requests

# Run the importer
python3 webull_auto_importer.py


