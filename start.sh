#!/bin/bash

# Kill any existing servers first
echo "🛑 Stopping any existing servers..."
pkill -f "python.*app.py" 2>/dev/null
sleep 2

echo "🚀 Starting Quantify - Options Trading Journal..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting server..."
echo "📊 Dashboard: http://localhost:5001"
echo "💡 No API keys needed - just add trades manually or import CSV!"
echo "💡 If port 5001 is busy, you can specify a different port: python app.py 8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask app
python3 app.py 5001

