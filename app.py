"""
Flask API server for Quantify - Options Trading Journal
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from trade_tracker import TradeTracker
from backtester import StrategyBacktester
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from auth import AuthManager
from typing import Optional
import shutil
import json
from database import init_db

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global tracker instance - will be replaced with user-specific instances
tracker = None
auth_manager = AuthManager()

def get_user_tracker(user_id: Optional[str] = None) -> TradeTracker:
    """Get a TradeTracker instance for a specific user"""
    if user_id:
        return TradeTracker(user_id=user_id)
    else:
        # Default tracker for backward compatibility
        return TradeTracker(user_id='default')

def get_current_user_id() -> Optional[str]:
    """Get the current user ID from the session token in the request"""
    # Try X-Session-Token header first
    session_token = request.headers.get('X-Session-Token', '')
    if not session_token:
        # Try Authorization header (for compatibility)
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            session_token = auth_header
    
    if session_token:
        user = auth_manager.verify_session(session_token)
        if user:
            return user.get('id')
    return None

def migrate_existing_data_to_user(user_id: str):
    """Migrate existing data files to user-specific storage (legacy - now using database)"""
    # This function is no longer needed - data is stored in database
    # Migration from JSON files should be done using migrate_trades.py script
    pass

# Brokerage integration (optional - only import if module exists)
try:
    from brokerage_integration import BrokerageManager
    brokerage_manager = BrokerageManager()
except ImportError:
    brokerage_manager = None
brokerage_manager = BrokerageManager()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory('static', 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/pnl', methods=['GET'])
def get_pnl():
    """Get PnL metrics for the current user"""
    try:
        user_id = get_current_user_id()
        # Migrate existing data if this is first access
        if user_id:
            migrate_existing_data_to_user(user_id)
        user_tracker = get_user_tracker(user_id)
        metrics = user_tracker.get_pnl_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get recent trades for the current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            # No user ID - return empty (user not authenticated)
            return jsonify({'trades': [], 'count': 0})
        
        # Migrate existing data if this is first access (legacy support)
        # Note: This function is for migrating old JSON files, not needed for database
        # migrate_existing_data_to_user(user_id)
        
        user_tracker = get_user_tracker(user_id)
        limit = request.args.get('limit', 50, type=int)
        trades = user_tracker.get_recent_trades(limit)
        return jsonify({'trades': trades, 'count': len(trades)})
    except Exception as e:
        print(f"Error in get_trades: {e}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['POST'])
def add_trade():
    """Add a new trade for the current user"""
    try:
        user_id = get_current_user_id()
        # Migrate existing data if this is first access
        if user_id:
            migrate_existing_data_to_user(user_id)
        user_tracker = get_user_tracker(user_id)
        data = request.json
        required_fields = ['symbol', 'action', 'quantity', 'price']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        trade = user_tracker.add_trade(data)
        return jsonify({'success': True, 'trade': trade}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<trade_id>', methods=['PUT'])
def update_trade(trade_id):
    """Update an existing trade for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        data = request.json
        trade = user_tracker.update_trade(trade_id, data)
        if trade:
            return jsonify({'success': True, 'trade': trade})
        return jsonify({'error': 'Trade not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['GET', 'POST'])
def portfolio_tracker():
    """Record and retrieve daily total portfolio values for the current user"""
    try:
        user_id = get_current_user_id()
        # Migrate existing data if this is first access
        if user_id:
            migrate_existing_data_to_user(user_id)
        user_tracker = get_user_tracker(user_id)
        
        if request.method == 'GET':
            limit = request.args.get('limit', 30, type=int)
            daily_balances = user_tracker.get_portfolio_daily_balances()
            
            if not daily_balances:
                return jsonify({
                    'entries': [],
                    'latest': None,
                    'previous': None,
                    'start': None,
                    'change': 0.0,
                    'since_start_change': 0.0,
                    'since_start_percent': 0.0
                })
            
            sorted_dates = sorted(daily_balances.keys())
            start_date = sorted_dates[0]
            latest_date = sorted_dates[-1]
            previous_date = sorted_dates[-2] if len(sorted_dates) > 1 else None
            
            latest_amount = daily_balances[latest_date]
            previous_amount = daily_balances[previous_date] if previous_date else None
            start_amount = daily_balances[start_date]
            
            adjustments = getattr(user_tracker, 'portfolio_adjustments', [])
            since_start_adjustments = 0.0
            latest_adjustments = 0.0
            
            for adj in adjustments:
                try:
                    amount = float(adj.get('amount', 0))
                except (TypeError, ValueError):
                    continue
                
                apply_to = str(adj.get('apply_to', 'since_start')).lower()
                if apply_to in ['since_start', 'both']:
                    since_start_adjustments += amount
                if apply_to in ['latest', 'both']:
                    # Only apply latest adjustments if they are on or after the start date
                    adj_date = adj.get('date')
                    if not adj_date or adj_date >= start_date:
                        latest_adjustments += amount
            
            adjusted_latest_amount = round(latest_amount + latest_adjustments, 2)
            day_change = round(latest_amount - previous_amount, 2) if previous_amount is not None else 0.0
            
            since_start_change = round((latest_amount - start_amount) + since_start_adjustments, 2)
            since_start_percent = round((since_start_change / start_amount * 100), 2) if start_amount else 0.0
            
            history = []
            for date_str in sorted(sorted_dates, reverse=True):
                amount = daily_balances[date_str]
                if date_str == latest_date:
                    amount = adjusted_latest_amount
                history.append({'date': date_str, 'amount': amount})
                if len(history) >= limit:
                    break
            
            return jsonify({
                'entries': history,
                'latest': {'date': latest_date, 'amount': adjusted_latest_amount},
                'previous': {'date': previous_date, 'amount': previous_amount} if previous_date else None,
                'start': {'date': start_date, 'amount': start_amount},
                'change': day_change,
                'since_start_change': since_start_change,
                'since_start_percent': since_start_percent
            })
        
        data = request.json or {}
        amount = data.get('amount')
        if amount is None:
            return jsonify({'error': 'Amount is required'}), 400
        
        date_str = data.get('date')
        notes = data.get('notes', '')
        entry = user_tracker.record_portfolio_value(amount, date_str, notes)
        return jsonify({'success': True, 'entry': entry}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    """Delete a trade for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        if user_tracker.delete_trade(trade_id):
            return jsonify({'success': True})
        return jsonify({'error': 'Trade not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get open positions for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        positions = user_tracker.get_open_positions()
        return jsonify({'positions': positions, 'count': len(positions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    """Get trades for calendar view for the current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            # Return empty calendar data if not authenticated (calendar will still show)
            return jsonify({})
        
        user_tracker = get_user_tracker(user_id)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        trades_by_date = user_tracker.get_trades_by_date(year, month)
        # Always return a dict, even if empty - this ensures calendar always renders
        return jsonify(trades_by_date if trades_by_date else {})
    except Exception as e:
        # Return empty dict on error so calendar still shows
        print(f"Error in get_calendar: {e}")
        return jsonify({})

@app.route('/api/portfolio/calendar', methods=['GET'])
def get_portfolio_calendar():
    """Get portfolio balances for calendar view for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        portfolio_by_date = user_tracker.get_portfolio_by_date(year, month)
        return jsonify(portfolio_by_date)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import', methods=['POST'])
def import_csv():
    """Import trades from CSV file for the current user"""
    try:
        user_id = get_current_user_id()
        # Migrate existing data if this is first access
        if user_id:
            migrate_existing_data_to_user(user_id)
        user_tracker = get_user_tracker(user_id)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Try enhanced Webull parser first, fallback to standard parser
            try:
                from webull_automation import create_webull_csv_parser
                parser = create_webull_csv_parser()
                webull_trades = parser(filepath)
                
                if webull_trades:
                    # Import Webull trades
                    imported = 0
                    errors = []
                    for trade in webull_trades:
                        try:
                            user_tracker.add_trade(trade)
                            imported += 1
                        except Exception as e:
                            errors.append(str(e))
                    
                    # Clean up
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    
                    return jsonify({
                        'success': True,
                        'imported': imported,
                        'errors': errors,
                        'source': 'webull'
                    })
            except ImportError:
                pass  # Fallback to standard parser
            
            # Standard CSV import
            result = user_tracker.import_csv(filepath)
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except:
                pass
            
            return jsonify({
                'success': True,
                'imported': result['imported'],
                'errors': result['errors']
            })
        
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run strategy backtest for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        data = request.json
        filters = data.get('filters', {})
        
        trades = user_tracker.get_recent_trades(limit=1000)
        backtester = StrategyBacktester(trades)
        results = backtester.backtest(filters)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/compare', methods=['POST'])
def compare_backtests():
    """Compare multiple backtest scenarios for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        data = request.json
        scenarios = data.get('scenarios', [])
        
        trades = user_tracker.get_recent_trades(limit=1000)
        backtester = StrategyBacktester(trades)
        results = backtester.compare_scenarios(scenarios)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/filter', methods=['POST'])
def filter_trades():
    """Filter trades by various criteria for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        data = request.json
        filters = data.get('filters', {})
        
        all_trades = user_tracker.get_recent_trades(limit=1000)
        filtered = []
        
        for trade in all_trades:
            # Symbol filter
            if filters.get('symbols'):
                if trade.get('symbol') not in filters['symbols']:
                    continue
            
            # Date range filter
            if filters.get('start_date') or filters.get('end_date'):
                trade_date = user_tracker._parse_date(trade.get('date'))
                if filters.get('start_date'):
                    start = datetime.fromisoformat(filters['start_date'])
                    if trade_date < start:
                        continue
                if filters.get('end_date'):
                    end = datetime.fromisoformat(filters['end_date'])
                    if trade_date > end:
                        continue
            
            # Tag filter
            if filters.get('tags'):
                trade_tags = trade.get('tags', [])
                if not any(tag in trade_tags for tag in filters['tags']):
                    continue
            
            # Strategy filter
            if filters.get('strategies'):
                if trade.get('strategy') not in filters['strategies']:
                    continue
            
            filtered.append(trade)
        
        return jsonify({'trades': filtered, 'count': len(filtered)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/performance', methods=['GET'])
def get_performance_analytics():
    """Get detailed performance analytics for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        trades = user_tracker.get_recent_trades(limit=1000)
        
        # Monthly performance
        monthly_performance = {}
        for trade in trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                trade_date = user_tracker._parse_date(trade.get('date'))
                month_key = trade_date.strftime('%Y-%m')
                if month_key not in monthly_performance:
                    monthly_performance[month_key] = {'pnl': 0, 'trades': 0, 'wins': 0}
                
                pnl = user_tracker.calculate_trade_pnl(trade)
                monthly_performance[month_key]['pnl'] += pnl
                monthly_performance[month_key]['trades'] += 1
                if pnl > 0:
                    monthly_performance[month_key]['wins'] += 1
        
        # Convert to list format
        monthly_data = []
        for month, data in sorted(monthly_performance.items()):
            monthly_data.append({
                'month': month,
                'pnl': round(data['pnl'], 2),
                'trades': data['trades'],
                'win_rate': round((data['wins'] / data['trades'] * 100), 1) if data['trades'] > 0 else 0
            })
        
        return jsonify({
            'monthly_performance': monthly_data,
            'total_months': len(monthly_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_trades():
    """Export trades to CSV for the current user"""
    try:
        user_id = get_current_user_id()
        user_tracker = get_user_tracker(user_id)
        data = request.json
        filters = data.get('filters', {})
        
        if filters:
            # Use filter endpoint logic
            all_trades = user_tracker.get_recent_trades(limit=1000)
            trades = []
            for trade in all_trades:
                if filters.get('symbols') and trade.get('symbol') not in filters['symbols']:
                    continue
                trades.append(trade)
        else:
            trades = user_tracker.get_recent_trades(limit=1000)
        
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Date', 'Symbol', 'Type', 'Option Type', 'Strike', 'Action', 'Quantity', 'Buy Price', 'Sold Amount', 'P&L', 'Strategy', 'Tags', 'Notes'])
        
        # Rows
        for trade in trades:
            pnl = tracker.calculate_trade_pnl(trade)
            writer.writerow([
                trade.get('date', ''),
                trade.get('symbol', ''),
                trade.get('trade_type', ''),
                trade.get('option_type', ''),
                trade.get('strike', ''),
                trade.get('action', ''),
                trade.get('quantity', ''),
                trade.get('price', ''),
                trade.get('sold_amount', ''),
                round(pnl, 2),
                trade.get('strategy', ''),
                ', '.join(trade.get('tags', [])),
                trade.get('notes', '')
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=trades_export.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Brokerage Integration Endpoints (only if module is available)
if brokerage_manager:
    @app.route('/api/brokerage/connect', methods=['POST'])
    def connect_brokerage():
        """Connect a brokerage account"""
        try:
            data = request.json
            user_id = data.get('user_id', 'default')  # TODO: Get from session/auth
            brokerage_type = data.get('brokerage_type')
            credentials = data.get('credentials', {})
            
            if not brokerage_type:
                return jsonify({'error': 'brokerage_type required'}), 400
            
            success = brokerage_manager.add_connection(user_id, brokerage_type, credentials)
            if success:
                return jsonify({'success': True, 'message': 'Brokerage connected successfully'}), 201
            return jsonify({'error': 'Failed to connect brokerage'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/brokerage/connections', methods=['GET'])
    def get_connections():
        """Get all brokerage connections for user"""
        try:
            user_id = request.args.get('user_id', 'default')  # TODO: Get from session/auth
            connections = brokerage_manager.connections.get(user_id, [])
            # Don't return full credentials for security
            safe_connections = [
                {
                    'id': c['id'],
                    'type': c['type'],
                    'connected_at': c['connected_at'],
                    'last_sync': c.get('last_sync'),
                    'enabled': c.get('enabled', True)
                }
                for c in connections
            ]
            return jsonify({'connections': safe_connections})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/brokerage/sync', methods=['POST'])
    def sync_brokerage():
        """Manually sync trades from connected brokerages"""
        try:
            user_id = request.json.get('user_id', 'default')  # TODO: Get from session/auth
            trades = brokerage_manager.sync_trades(user_id)
            
            # Import trades into tracker
            imported = []
            for trade in trades:
                # Check if trade already exists (by brokerage_trade_id)
                existing = [t for t in tracker.trades if t.get('brokerage_trade_id') == trade.get('brokerage_trade_id')]
                if not existing:
                    added_trade = tracker.add_trade(trade)
                    imported.append(added_trade)
            
            return jsonify({
                'success': True,
                'trades_found': len(trades),
                'trades_imported': len(imported),
                'trades': imported
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create a new user account"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'success': False, 'error': 'Email, password, and name are required'}), 400
        
        result = auth_manager.create_user(email, password, name)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """Sign in a user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        result = auth_manager.sign_in(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/signout', methods=['POST'])
def signout():
    """Sign out a user"""
    try:
        data = request.json
        session_token = data.get('session_token', '')
        
        auth_manager.sign_out(session_token)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/session', methods=['GET'])
def verify_session():
    """Verify a session token"""
    try:
        session_token = request.headers.get('X-Session-Token', '')
        
        if not session_token:
            return jsonify({'authenticated': False}), 401
        
        user = auth_manager.verify_session(session_token)
        
        if user:
            return jsonify({'authenticated': True, 'user': user}), 200
        else:
            return jsonify({'authenticated': False}), 401
    except Exception as e:
        return jsonify({'authenticated': False, 'error': str(e)}), 500

@app.route('/api/auth/update-name', methods=['POST'])
def update_user_name():
    """Update user's name"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.json
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        result = auth_manager.update_user_name(user_id, new_name)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    import sys
    
    # Initialize database on startup
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("  This is required for the app to work. Please check:")
        print("  1. DATABASE_URL environment variable is set")
        print("  2. Database is accessible")
        print("  3. Database credentials are correct")
        # Don't exit - let it fail on first request so user can see the error
        # import sys
        # sys.exit(1)
    
    # Try to use port 5001 if 5000 is busy, or use command line argument
    port = 5001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    # For Render, use PORT environment variable
    port = int(os.environ.get('PORT', port))
    
    print("=" * 60)
    print("🚀 Quantify - Options Trading Journal")
    print("=" * 60)
    print(f"📊 Dashboard: http://localhost:{port}")
    print("📝 Add trades manually or import from CSV")
    print("=" * 60)
    
    # For production (Render), use 0.0.0.0 instead of 127.0.0.1
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    app.run(debug=not os.environ.get('RENDER'), host=host, port=port)
