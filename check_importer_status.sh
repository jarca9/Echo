#!/bin/bash
# Quick status check for Webull importer

echo "=== Webull Auto Importer Status ==="
echo ""

# Check if server is running
if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
    echo "✓ Echo Journal Server: RUNNING"
else
    echo "✗ Echo Journal Server: NOT RUNNING"
    echo "  Start with: python3 app.py 5001"
fi

# Check if importer is running
if ps aux | grep -q "[w]ebull_auto_importer.py"; then
    echo "✓ Webull Importer: RUNNING"
    IMPORTER_PID=$(ps aux | grep "[w]ebull_auto_importer.py" | awk '{print $2}' | head -1)
    echo "  PID: $IMPORTER_PID"
else
    echo "✗ Webull Importer: NOT RUNNING"
    echo "  Start with: python3 webull_auto_importer.py"
fi

echo ""
echo "=== Configuration ==="
echo "• Importing trades from: December 10, 2025 onwards"
echo "• Auto-refresh Webull: Every 5 minutes"
echo "• Check for trades: Every 60 seconds"
echo "• Duplicate prevention: Enabled"
echo ""

# Check processed trades
if [ -f "webull_processed_trades.json" ]; then
    PROCESSED_COUNT=$(python3 -c "import json; f=open('webull_processed_trades.json'); d=json.load(f); print(len(d.get('trade_ids', [])))" 2>/dev/null || echo "0")
    echo "Processed trades tracked: $PROCESSED_COUNT"
else
    echo "Processed trades tracked: 0 (will be created on first import)"
fi

echo ""
echo "=== Recent Log ==="
if [ -f "webull_importer.log" ]; then
    tail -10 webull_importer.log 2>/dev/null || echo "No log entries yet"
else
    echo "No log file yet (importer will create it)"
fi


