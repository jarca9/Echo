#!/usr/bin/env python3
"""Launch Quantify server"""
import subprocess
import sys
import os
import time

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("🛑 Stopping any existing servers...")
try:
    subprocess.run(['pkill', '-f', 'python.*app.py'], 
                   stderr=subprocess.DEVNULL)
    time.sleep(1)
except:
    pass

print("🚀 Starting Quantify server...")
print("📊 Open: http://localhost:5001")
print("=" * 60)

# Start server
subprocess.run([sys.executable, 'app.py', '5001'])

