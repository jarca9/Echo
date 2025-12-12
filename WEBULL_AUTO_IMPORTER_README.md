# Webull Automatic Trade Importer

This script automatically monitors your Webull Desktop app's log files and imports new trades into your Echo journal. It also automatically refreshes the Webull order history page so you don't have to manually refresh.

## Features

- ✅ **Automatic Monitoring**: Watches Webull log files for new trades
- ✅ **Auto-Refresh**: Automatically refreshes Webull order history every 5 minutes
- ✅ **Duplicate Prevention**: Tracks processed trades to avoid importing twice
- ✅ **Real-time Import**: Imports trades as soon as they appear in logs
- ✅ **Background Operation**: Runs continuously in the background

## Setup

1. **Make sure your Echo journal server is running:**
   ```bash
   python3 app.py 5001
   ```

2. **Start the importer:**
   ```bash
   ./start_webull_importer.sh
   ```

   Or run directly:
   ```bash
   python3 webull_auto_importer.py
   ```

## How It Works

1. **Monitoring**: The script watches the Webull log directory for changes
2. **Auto-Refresh**: Every 5 minutes, it automatically refreshes the Webull order history page (using AppleScript)
3. **Detection**: When new trades appear in the logs, it parses them
4. **Import**: New trades are automatically imported to your Echo journal via the API
5. **Tracking**: Processed trades are saved to avoid duplicates

## Configuration

You can modify these settings in `webull_auto_importer.py`:

- `CHECK_INTERVAL`: How often to check for new trades (default: 60 seconds)
- `WEBULL_REFRESH_INTERVAL`: How often to refresh Webull (default: 300 seconds / 5 minutes)
- `API_BASE_URL`: Your Echo journal API URL (default: http://localhost:5001/api)

## Requirements

- Python 3.7+
- Webull Desktop app installed and logged in
- Echo journal server running
- Required Python packages (installed automatically):
  - `watchdog` - File monitoring
  - `requests` - API calls

## Troubleshooting

### Trades not being imported

1. **Check if Webull is open**: The app needs to be running for logs to be created
2. **Check if server is running**: Make sure `python3 app.py 5001` is running
3. **Manually refresh orders**: Open the Orders/History page in Webull to trigger a log update
4. **Check logs**: The script prints status messages - look for errors

### Auto-refresh not working

The AppleScript automation tries multiple methods to refresh Webull:
- Keyboard shortcut (Cmd+R)
- Clicking refresh buttons
- Navigating to Orders tab

If it's not working, you can:
- Manually refresh the Orders page in Webull occasionally
- The script will still detect trades when you manually refresh

### Permission Issues

If you get permission errors:
```bash
chmod +x webull_auto_importer.py
chmod +x start_webull_importer.sh
```

On macOS, you may need to grant Terminal/your terminal app permission to control Webull:
- System Preferences → Security & Privacy → Privacy → Accessibility
- Add your terminal app

## Running in Background

To run the importer in the background:

```bash
nohup python3 webull_auto_importer.py > webull_importer.log 2>&1 &
```

To stop it:
```bash
pkill -f webull_auto_importer.py
```

## What Gets Imported

For each filled trade, the script imports:
- Symbol
- Action (BUY/SELL)
- Quantity
- Price per contract
- Date & Time
- Transaction fee
- Option details (if applicable): type, strike, expiration

## Notes

- The script only imports **filled** trades (not pending or cancelled orders)
- Trades are tracked by a unique ID to prevent duplicates
- The script needs Webull Desktop to be running
- Log files are created when Webull fetches order data (usually when you open Orders/History)


