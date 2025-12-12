#!/usr/bin/env python3
"""Start the Quantify server"""
import subprocess
import sys
import os
import time
import signal

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Kill any existing servers
print("🛑 Stopping any existing servers...")
try:
    subprocess.run(['pkill', '-f', 'python.*app.py'], 
                   stderr=subprocess.DEVNULL, 
                   stdout=subprocess.DEVNULL)
    time.sleep(2)
except:
    pass

# Start the server
print("🚀 Starting Quantify server on port 5001...")
print("📊 Dashboard: http://localhost:5001")
print("Press Ctrl+C to stop the server\n")

try:
    # Start the Flask app
    subprocess.run([sys.executable, 'app.py', '5001'])
except KeyboardInterrupt:
    print("\n\n🛑 Server stopped.")
    sys.exit(0)

