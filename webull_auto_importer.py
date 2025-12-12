#!/usr/bin/env python3
"""
Webull Automatic Trade Importer
Monitors Webull log files and automatically imports new trades to Echo journal.
Also automates refreshing the Webull order history page.
"""

import json
import re
import time
import requests
import subprocess
import os
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import glob
import pytz

# Configuration
WEBULL_LOG_DIR = os.path.expanduser(
    "~/Library/Application Support/Webull Desktop/Webull Desktop/log/"
)
API_BASE_URL = "http://localhost:5001/api"
CHECK_INTERVAL = 60  # Check for new trades every 60 seconds
# Note: Auto-refresh disabled to avoid opening/activating Webull
# The script will monitor log files when you manually refresh Webull
WEBULL_REFRESH_INTERVAL = 300  # Refresh every 5 minutes (only if Webull is already running)
REFRESH_START_HOUR = 6  # Start refreshing at 6:30 AM PST
REFRESH_START_MINUTE = 30
REFRESH_END_HOUR = 12  # Stop refreshing at 12:00 PM PST
REFRESH_END_MINUTE = 0

# Track processed trades to avoid duplicates
processed_trades_file = "webull_processed_trades.json"
processed_trades = set()


def load_processed_trades():
    """Load list of already processed trade IDs"""
    global processed_trades
    if os.path.exists(processed_trades_file):
        try:
            with open(processed_trades_file, 'r') as f:
                data = json.load(f)
                processed_trades = set(data.get('trade_ids', []))
        except:
            processed_trades = set()


def save_processed_trade(trade_id):
    """Save a trade ID to mark it as processed"""
    global processed_trades
    processed_trades.add(trade_id)
    data = {'trade_ids': list(processed_trades)}
    with open(processed_trades_file, 'w') as f:
        json.dump(data, f, indent=2)


def is_refresh_time():
    """Check if current PST time is within auto-refresh hours (6:30 AM - 12:00 PM PST)"""
    try:
        # Get current time in PST
        pst = pytz.timezone('America/Los_Angeles')
        now_pst = datetime.now(pst)
        current_hour = now_pst.hour
        current_minute = now_pst.minute
        
        # Convert to minutes since midnight for easier comparison
        current_time_minutes = current_hour * 60 + current_minute
        start_time_minutes = REFRESH_START_HOUR * 60 + REFRESH_START_MINUTE  # 6:30 AM = 390 minutes
        end_time_minutes = REFRESH_END_HOUR * 60 + REFRESH_END_MINUTE  # 12:00 PM = 720 minutes
        
        # Check if current time is within refresh window
        return start_time_minutes <= current_time_minutes < end_time_minutes
    except Exception:
        # If timezone conversion fails, default to allowing refresh
        return True

def refresh_webull_orders():
    """
    Attempt to refresh Webull orders WITHOUT activating/opening the app.
    Only works if Webull is already running in the background.
    """
    try:
        # Check if Webull is running first
        result = subprocess.run([
            'pgrep', '-f', 'Webull Desktop'
        ], capture_output=True, timeout=3)
        
        if result.returncode != 0:
            # Webull is not running - skip refresh (won't open it)
            return False
        
        # Webull is running - try to send refresh command WITHOUT activating
        # Note: macOS security may prevent this from working if app isn't frontmost
        # But we try anyway - if it fails, file monitoring will still catch manual refreshes
        script = '''
        tell application "System Events"
            if (name of processes) contains "Webull Desktop" then
                tell process "Webull Desktop"
                    -- Try to send Cmd+R without activating the app
                    -- This attempts to refresh in the background
                    try
                        -- Use key code 15 (R key) with command modifier
                        -- Note: This may silently fail if macOS security blocks it
                        key code 15 using {command down}
                        return "success"
                    on error errMsg
                        return "failed: " & errMsg
                    end try
                end tell
            else
                return "not_running"
            end if
        end tell
        '''
        
        # Run the script - capture output to check result
        result = subprocess.run([
            'osascript', '-e', script
        ], timeout=5, capture_output=True, text=True)
        
        # Check if it succeeded
        output = result.stdout.strip()
        success = "success" in output.lower()
        
        # Only log if successful (keep it quiet)
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Background refresh sent to Webull")
        
        return success
        
    except Exception as e:
        # Silently fail - don't interrupt user
        return False


def parse_webull_trade(item, min_date=None):
    """
    Parse a Webull trade item into Echo journal format.
    
    CRITICAL IMPLEMENTATION NOTES (for auto-import):
    ================================================
    1. BUY and SELL are SEPARATE trades - import BOTH:
       - BUY trade: price = buy price per contract from logs (e.g., $1.49)
       - SELL trade: price = sell price per contract from logs (e.g., $1.35)
       - Each trade stores its own price - DO NOT confuse them
    
    2. sold_amount calculation for SELL trades:
       - For options: sold_amount = quantity * price * 100
       - Example: SELL 2 contracts @ $1.35 → sold_amount = 2 * 1.35 * 100 = $270
       - For stocks: sold_amount = quantity * price
    
    3. P&L calculation (handled by TradeTracker):
       - Uses FIFO matching to find matching BUY trade(s)
       - Uses BUY trade's price for cost calculation (NOT SELL price)
       - Includes both BUY and SELL transaction fees
       - Example: Revenue ($270) - Cost ($298 from BUY @ $1.49) - Fees ($4.02) = -$32.02
    
    4. Always import both BUY and SELL trades when they appear in logs
    """
    try:
        filled_time = item.get('filledTime') or item.get('createTime', '')
        symbol = item.get('ticker', {}).get('symbol', 'N/A')
        action = item.get('action', '').upper()
        quantity = float(item.get('filledQuantity', 0) or 0)
        price = float(item.get('avgFilledPrice', 0) or 0)  # This is the price for THIS trade (BUY or SELL)
        amount = float(item.get('filledAmount', 0) or 0)
        fee = float(item.get('fee', 0) or 0)
        
        # Check if trade is before minimum date (only import from Dec 10 onwards)
        if min_date:
            try:
                if '/' in filled_time:
                    parts = filled_time.split(' ')
                    date_part = parts[0]
                    month, day, year = date_part.split('/')
                    trade_date = datetime(int(year), int(month), int(day))
                    if trade_date < min_date:
                        return None, None  # Skip trades before min_date
            except:
                pass
        
        # Get option details
        option_type = None
        strike = None
        expiration = None
        if 'legs' in item and len(item['legs']) > 0:
            leg = item['legs'][0]
            option_type = leg.get('optionType')
            strike = leg.get('optionExercisePrice')
            expiration = leg.get('optionExpireDate')
        
        # Convert action to standard format
        if action in ['BUY', 'OPEN']:
            action = 'BUY'
        elif action in ['SELL', 'CLOSE']:
            action = 'SELL'
        
        # Parse date/time
        # Format: "12/09/2025 09:31:29 EST"
        try:
            if '/' in filled_time:
                # Parse "MM/DD/YYYY HH:MM:SS EST"
                parts = filled_time.split(' ')
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else "00:00:00"
                month, day, year = date_part.split('/')
                hour, minute, second = time_part.split(':')
                # Convert to ISO format (keep as EST for now, will convert in frontend)
                dt = datetime(int(year), int(month), int(day), 
                             int(hour), int(minute), int(second))
                date_str = dt.isoformat()
            else:
                date_str = filled_time
        except Exception as e:
            print(f"Warning: Could not parse date '{filled_time}': {e}")
            date_str = datetime.now().isoformat()
        
        # Create trade ID from order details
        trade_id = f"webull_{item.get('id', '')}_{filled_time}_{symbol}_{action}_{quantity}_{price}"
        
        # Calculate sold_amount for SELL trades (must match manual entry calculation)
        # CRITICAL: This uses the SELL trade's price, NOT the BUY price
        # Manual entry calculates: sold_amount = quantity * price * 100 (for options)
        # For options: sold_amount = quantity * price * 100 (same as manual entry)
        # For stocks: sold_amount = quantity * price
        # Example: SELL 2 contracts @ $1.35 → sold_amount = 2 * 1.35 * 100 = $270
        if action == 'SELL':
            if option_type and strike:
                # Options: quantity * price * 100 (matches manual entry)
                # price here is the SELL price per contract from logs
                sold_amount = quantity * price * 100
            else:
                # Stocks: quantity * price
                sold_amount = quantity * price
        else:
            # BUY trades have no sold_amount
            sold_amount = 0
        
        trade_data = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'date': date_str,
            'transaction_fee': fee,
            'sold_amount': sold_amount,
        }
        
        # Add option fields if it's an option trade
        if option_type and strike and expiration:
            trade_data['option_type'] = option_type
            trade_data['strike'] = float(strike)
            trade_data['expiration'] = expiration
            trade_data['trade_type'] = 'OPTION'
        else:
            trade_data['trade_type'] = 'STOCK'
            trade_data['option_type'] = ''
            trade_data['strike'] = 0
            trade_data['expiration'] = ''
        
        return trade_data, trade_id
    except Exception as e:
        print(f"Error parsing trade: {e}")
        return None, None


def scan_log_files(min_date=None):
    """Scan all Webull log files for new trades"""
    log_files = glob.glob(os.path.join(WEBULL_LOG_DIR, "Trade_*.log"))
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    new_trades = []
    
    # Check the most recent log files
    for log_file in log_files[:3]:  # Check last 3 log files
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                if 'loadOrderList' in line and 'true' in line:
                    match = re.search(r'loadOrderList true "(\[.*\])"', line)
                    if match:
                        json_str_escaped = match.group(1)
                        json_str = json_str_escaped.replace('\\"', '"').replace('\\\\', '\\')
                        try:
                            orders = json.loads(json_str)
                            for order in orders:
                                if isinstance(order, dict) and 'items' in order:
                                    for item in order.get('items', []):
                                        status = item.get('statusCode', '')
                                        filled_qty = float(item.get('filledQuantity', 0) or 0)
                                        
                                        if status == 'Filled' and filled_qty > 0:
                                            trade_data, trade_id = parse_webull_trade(item, min_date)
                                            if trade_data and trade_id and trade_id not in processed_trades:
                                                new_trades.append((trade_data, trade_id))
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    return new_trades


def import_trade_to_echo(trade_data, session_token=None):
    """Import a trade to Echo journal via API"""
    try:
        headers = {'Content-Type': 'application/json'}
        if session_token:
            headers['X-Session-Token'] = session_token
        
        response = requests.post(
            f"{API_BASE_URL}/trades",
            json=trade_data,
            headers=headers,
            timeout=10
        )
        # Check for success (200 or 201 status codes, or success in response)
        if response.status_code in [200, 201]:
            result = response.json()
            # Also check if response has success field
            if isinstance(result, dict) and result.get('success', True):
                return True, result
            return True, result
        else:
            return False, response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)


class LogFileHandler(FileSystemEventHandler):
    """Handler for log file changes"""
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.log') and 'Trade_' in event.src_path:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Log file changed: {os.path.basename(event.src_path)}")
            time.sleep(2)  # Wait for file to finish writing
            process_new_trades()


def process_new_trades():
    """
    Process any new trades found in log files.
    
    REMEMBER FOR AUTO-IMPORT:
    ========================
    - Import BOTH BUY and SELL trades separately (they are different trades)
    - BUY trades: price = buy price from logs (e.g., $1.49)
    - SELL trades: price = sell price from logs (e.g., $1.35)
    - sold_amount = quantity * SELL_price * 100 (for options)
    - P&L is calculated by TradeTracker using FIFO matching with BUY price
    """
    # Only import trades from Dec 10, 2025 onwards
    min_date = datetime(2025, 12, 10)
    new_trades = scan_log_files(min_date=min_date)
    
    if new_trades:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(new_trades)} new trade(s)")
        
        for trade_data, trade_id in new_trades:
            success, result = import_trade_to_echo(trade_data)
            if success:
                trade_info = result.get('trade', {}) if isinstance(result, dict) else {}
                trade_id_echo = trade_info.get('id', trade_id)
                print(f"  ✓ Imported: {trade_data['action']} {trade_data['quantity']} {trade_data['symbol']} @ ${trade_data['price']} (ID: {trade_id_echo[:8]}...)")
                save_processed_trade(trade_id)
            else:
                print(f"  ✗ Failed to import {trade_data['symbol']}: {result}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No new trades found")


def main():
    """Main monitoring loop"""
    print("=" * 60)
    print("Webull Automatic Trade Importer")
    print("=" * 60)
    print(f"Monitoring: {WEBULL_LOG_DIR}")
    print(f"API: {API_BASE_URL}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print(f"Auto-refresh: DISABLED (stopped until user says so)")
    print(f"Auto-read: DISABLED (stopped until user says so)")
    print(f"Refresh hours: {REFRESH_START_HOUR:02d}:{REFRESH_START_MINUTE:02d} AM - {REFRESH_END_HOUR:02d}:{REFRESH_END_MINUTE:02d} PM PST")
    print(f"Importing trades from: December 10, 2025 onwards")
    print(f"Note: Auto-refresh and auto-read are currently DISABLED")
    print("=" * 60)
    print()
    
    # Load processed trades
    load_processed_trades()
    print(f"Loaded {len(processed_trades)} previously processed trades")
    print()
    
    # Initial scan
    print("Performing initial scan...")
    process_new_trades()
    print()
    
    # Set up file watcher
    # DISABLED: Auto read stopped until user says so
    # event_handler = LogFileHandler()
    # observer = Observer()
    # observer.schedule(event_handler, WEBULL_LOG_DIR, recursive=False)
    # observer.start()
    # print("File watcher started")
    print("File watcher DISABLED (auto read stopped)")
    print()
    
    # last_refresh = time.time()
    
    try:
        while True:
            # DISABLED: Auto refresh stopped until user says so
            # Periodically attempt to refresh Webull (only if already running and within market hours)
            # This won't open/activate the app - it only works if Webull is already open
            # current_time = time.time()
            # if current_time - last_refresh >= WEBULL_REFRESH_INTERVAL:
            #     # Check if we're within refresh hours (6:30 AM - 12:00 PM PST)
            #     if is_refresh_time():
            #         # Attempt background refresh (won't open app)
            #         success = refresh_webull_orders()
            #         last_refresh = current_time
            #         if success:
            #             pst = pytz.timezone('America/Los_Angeles')
            #             now_pst = datetime.now(pst)
            #             print(f"[{now_pst.strftime('%H:%M:%S')} PST] Background refresh sent to Webull")
            #             # Wait a bit for trades to appear in logs
            #             time.sleep(5)
            #             process_new_trades()
            #         # If refresh failed (app not running or not accessible), just continue monitoring
            #     else:
            #         # Outside refresh hours - skip refresh but update last_refresh to avoid constant checking
            #         last_refresh = current_time
            
            # DISABLED: Periodic check for new trades stopped until user says so
            # Periodic check for new trades
            time.sleep(CHECK_INTERVAL)
            # process_new_trades()
            
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        # observer.stop()
    # observer.join()
    print("Monitor stopped.")


if __name__ == "__main__":
    main()

