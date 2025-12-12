# Webull Canada Automatic Trade Tracking Guide

Since Webull Canada doesn't offer a public API and email notifications aren't available, here are practical solutions to automatically track your trades:

## Solution 1: Automated CSV Export (Recommended)

### Option A: Browser Automation (Semi-Automatic)

**How it works:**
- Uses Selenium to automate logging into Webull website
- Navigates to trade history page
- Downloads CSV export automatically
- Imports into your trading journal

**Setup:**
1. Install Selenium:
   ```bash
   pip install selenium
   ```

2. Install ChromeDriver:
   ```bash
   brew install chromedriver  # macOS
   # or download from https://chromedriver.chromium.org/
   ```

3. Run the automation script:
   ```python
   from webull_automation import WebullCSVAutomation
   
   automation = WebullCSVAutomation(
       username="your_webull_email",
       password="your_password",
       headless=True
   )
   
   csv_file = automation.login_and_download_csv()
   # Then import the CSV into your journal
   ```

**Note:** You'll need to inspect Webull's website to find the correct selectors for login and export buttons, as they may change.

### Option B: Manual CSV Export with Folder Watcher (Easiest)

**How it works:**
- You manually export CSV from Webull (takes 30 seconds)
- Drop it in a watched folder
- System automatically imports it

**Setup:**

1. **Create a watched folder:**
   ```bash
   mkdir ~/webull_exports
   ```

2. **Set up folder action (macOS):**
   - Open Automator
   - Create new "Folder Action"
   - Choose the `~/webull_exports` folder
   - Add "Run Shell Script" action:
   ```bash
   python3 /path/to/your/app/webull_auto_import.py "$1"
   ```

3. **Or use a simple Python watcher:**
   ```python
   from webull_automation import WebullCSVWatcher
   import time
   
   watcher = WebullCSVWatcher('~/webull_exports')
   
   while True:
       new_files = watcher.check_for_new_files()
       for file in new_files:
           # Import CSV
           trades = parse_webull_csv(file)
           # Add to tracker
           watcher.mark_as_processed(file)
       time.sleep(60)  # Check every minute
   ```

**Workflow:**
1. Open Webull app/website
2. Go to Trade History
3. Export to CSV (takes 30 seconds)
4. Save to `~/webull_exports` folder
5. System automatically imports

## Solution 2: Webull OpenAPI (If Available)

**Requirements:**
- Account with $5,000+ value
- Apply for API access at: https://www.webull.com/open-api
- Approval takes 1-2 business days
- May not be available for Canadian accounts

**If approved:**
- Use the `WebullAdapter` in `brokerage_integration.py`
- Set up OAuth flow
- Automatic sync every hour

## Solution 3: Browser Extension (Advanced)

**How it works:**
- Create a Chrome extension that intercepts Webull's network requests
- Captures trade data as you browse
- Sends to your journal automatically

**This requires:**
- JavaScript knowledge
- Understanding Webull's API endpoints
- Extension development

## Solution 4: Mobile App Automation (Most Complex)

**How it works:**
- Use Appium to automate the Webull mobile app
- Read order notifications from the in-app assistant
- Parse and import trades

**Setup:**
1. Install Appium
2. Connect your phone
3. Write automation script to:
   - Open Webull app
   - Navigate to order notifications
   - Extract trade data
   - Send to your journal

## Recommended Approach

**For most users: Manual CSV Export with Folder Watcher (Solution 1B)**

**Why:**
- ✅ Simple and reliable
- ✅ No complex automation
- ✅ Works 100% of the time
- ✅ Takes only 30 seconds per export
- ✅ Can export daily/weekly

**Workflow:**
1. Set up the watched folder
2. Export CSV from Webull once per day (or after trading session)
3. Drop CSV in folder
4. System auto-imports

## Enhanced CSV Parser

The system now includes an enhanced Webull CSV parser that handles:
- Various date formats
- Different column names
- Options parsing
- Commission/fee extraction
- Multiple CSV formats

## Setting Up Automated Import

Add this to your app.py:

```python
from webull_automation import WebullCSVWatcher, create_webull_csv_parser
import threading

# Start watcher in background
watcher = WebullCSVWatcher('~/webull_exports')
parser = create_webull_csv_parser()

def watch_webull_exports():
    while True:
        new_files = watcher.check_for_new_files()
        for file in new_files:
            trades = parser(file)
            for trade in trades:
                tracker.add_trade(trade)
            watcher.mark_as_processed(file)
        time.sleep(60)

# Start in background thread
threading.Thread(target=watch_webull_exports, daemon=True).start()
```

## Alternative: Scheduled CSV Export

If Webull allows scheduled exports (check settings):
1. Set up daily/weekly CSV export
2. Configure to save to watched folder
3. System auto-imports

## Tips

1. **Export frequency:** Export CSV daily or after each trading session
2. **File naming:** Use consistent naming (e.g., `webull_trades_YYYY-MM-DD.csv`)
3. **Backup:** Keep exported CSVs as backup
4. **Verification:** Check imported trades match your Webull account

## Troubleshooting

**CSV not importing:**
- Check CSV format matches expected columns
- Verify date format
- Check for encoding issues (UTF-8)

**Automation not working:**
- Webull may have changed their website structure
- Update selectors in automation script
- Consider using manual export instead

**Missing trades:**
- Ensure you're exporting all trades, not just recent
- Check date range in export settings
- Verify CSV includes all required columns


