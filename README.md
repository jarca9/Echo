# Quantify - Options Trading Journal

A powerful options trading journal that works **without any API keys**. Track your trades manually or import from CSV files exported from Webull.

## Features

- ✅ **No API Key Required**: Works completely offline with manual entry
- ✅ **Manual Trade Entry**: Add trades easily through a beautiful web interface
- ✅ **CSV Import**: Import trades from Webull CSV exports
- ✅ **Comprehensive P&L Metrics**:
  - Daily P&L
  - Weekly P&L
  - Monthly P&L
  - All-Time P&L
- ✅ **Daily Portfolio Log**: Record total portfolio value each day and see day-over-day changes
- ✅ **Modern Dashboard**: Beautiful, responsive web interface
- ✅ **Trade History**: View all your trades with edit/delete options
- ✅ **Open Positions**: Automatically calculates open positions from your trades
- ✅ **FIFO P&L Calculation**: Accurate profit/loss using First-In-First-Out method

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./start.sh
```

This script will:
- Check for `.env` file and run setup if needed
- Create a virtual environment
- Install all dependencies
- Start the server

### Option 2: Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Run the Application

**That's it! No API keys or credentials needed!**

Start the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5001` (or the port you specify)

#### 4. Open the Dashboard

Open your browser and navigate to:
```
http://localhost:5001
```

**Note**: If port 5001 is also busy, you can specify a different port:
```bash
python app.py 8080
```
Then access it at `http://localhost:8080`

The dashboard will automatically refresh every 10 seconds to show the latest data.

## How It Works

1. **Manual Entry**: Add trades through the web interface or import from CSV
2. **Trade Storage**: All trades are stored locally in `trades_history.json`
3. **PnL Calculation**: The system uses FIFO (First-In-First-Out) method to calculate realized P&L
4. **Auto-Refresh**: The dashboard refreshes every 10 seconds to show the latest data

## Adding Trades

### Method 1: Manual Entry
1. Click the "Add Trade" button on the dashboard
2. Fill in the trade details:
   - Symbol (e.g., AAPL)
   - Action (BUY, SELL, OPEN, CLOSE)
   - Quantity
   - Price per share
   - Date & Time (defaults to now)
   - Optional notes
3. Click "Add Trade"

### Method 2: CSV Import
1. Export your trade history from Webull as CSV
2. Click "Import CSV" on the dashboard
3. Select your CSV file
4. The system will automatically parse and import your trades

**CSV Format**: The importer supports common Webull CSV formats. Required columns:
- Symbol/Ticker
- Action/Side
- Quantity/Qty
- Price/Fill Price
- Date/Time

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/pnl` - Get P&L metrics
- `GET /api/portfolio?limit=30` - Fetch recent daily portfolio totals
- `POST /api/portfolio` - Record/update a day's total portfolio value
- `GET /api/trades?limit=50` - Get recent trades
- `POST /api/trades` - Add a new trade
- `PUT /api/trades/<id>` - Update a trade
- `DELETE /api/trades/<id>` - Delete a trade
- `GET /api/positions` - Get open positions
- `POST /api/import` - Import trades from CSV file

## Troubleshooting

### No Trades Showing

- Click the "Add Trade" button to manually add your first trade
- Or use "Import CSV" to import trades from Webull exports
- Make sure the server is running (check the port number in the terminal output)

### CSV Import Not Working

- Ensure your CSV file has the required columns (Symbol, Action, Quantity, Price, Date)
- Check the browser console for error messages
- Try exporting a fresh CSV from Webull

### P&L Not Calculating Correctly

- Make sure you've entered both BUY and SELL trades for closed positions
- The system uses FIFO (First-In-First-Out) method
- Open positions won't show unrealized P&L (would need current market prices)

## Security Notes

- All data is stored locally in `trades_history.json`
- No data is sent to external servers
- Your trades remain private on your machine

## Future Enhancements

- [ ] Advanced charting and visualization
- [ ] Trade performance analytics
- [ ] Export trade history to CSV
- [ ] Real-time price updates for open positions (unrealized P&L)
- [ ] Trade tags and categories
- [ ] Performance metrics and statistics
- [ ] Multi-account support

## License

This project is for personal use. Free to use and modify as needed.

