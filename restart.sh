#!/bin/bash

# Kill any existing servers
echo "🛑 Stopping any existing servers..."
pkill -f "python.*app.py" 2>/dev/null
sleep 2

# Navigate to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Start the server
echo "🚀 Starting Quantify server on port 5001..."
python3 app.py 5001

