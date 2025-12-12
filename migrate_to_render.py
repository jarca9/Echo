#!/usr/bin/env python3
"""
One-time migration script to copy data from local SQLite to Render PostgreSQL
Run this locally with DATABASE_URL pointing to Render's database
"""
import os
import sys
from database import get_db, close_db, User, Trade, PortfolioHistory, PortfolioAdjustment
from auth import AuthManager
from trade_tracker import TradeTracker
from datetime import datetime

def export_from_local():
    """Export data from local SQLite database"""
    # Temporarily use local SQLite
    original_url = os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL'] = 'sqlite:///quantify.db'
    
    # Reload database module to use SQLite
    import importlib
    import database
    importlib.reload(database)
    
    from database import get_db, close_db, User, Trade, PortfolioHistory, PortfolioAdjustment
    
    db = get_db()
    try:
        # Export users
        users = db.query(User).all()
        users_data = []
        for u in users:
            users_data.append({
                'id': u.id,
                'email': u.email,
                'name': u.name,
                'password_hash': u.password_hash,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'last_login': u.last_login.isoformat() if u.last_login else None
            })
        
        # Export trades
        trades = db.query(Trade).all()
        trades_data = []
        for t in trades:
            trades_data.append({
                'id': t.id,
                'user_id': t.user_id,
                'symbol': t.symbol,
                'action': t.action,
                'quantity': float(t.quantity),
                'price': float(t.price),
                'date': t.date.isoformat() if isinstance(t.date, datetime) else str(t.date),
                'transaction_fee': float(t.transaction_fee),
                'sold_amount': float(t.sold_amount),
                'notes': t.notes or '',
                'option_type': t.option_type or '',
                'strike': float(t.strike) if t.strike else None,
                'expiration': t.expiration or '',
                'trade_type': t.trade_type or 'OPTION',
                'created_at': t.created_at.isoformat() if t.created_at else None
            })
        
        # Export portfolio history
        portfolio = db.query(PortfolioHistory).all()
        portfolio_data = []
        for p in portfolio:
            portfolio_data.append({
                'id': p.id,
                'user_id': p.user_id,
                'date': p.date.isoformat() if isinstance(p.date, datetime) else str(p.date),
                'total_value': float(p.total_value),
                'notes': p.notes or '',
                'created_at': p.created_at.isoformat() if p.created_at else None
            })
        
        # Export portfolio adjustments
        adjustments = db.query(PortfolioAdjustment).all()
        adjustments_data = []
        for a in adjustments:
            adjustments_data.append({
                'id': a.id,
                'user_id': a.user_id,
                'date': a.date.isoformat() if isinstance(a.date, datetime) else str(a.date),
                'amount': float(a.amount),
                'description': a.description or '',
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
        
        return {
            'users': users_data,
            'trades': trades_data,
            'portfolio': portfolio_data,
            'adjustments': adjustments_data
        }
    finally:
        close_db(db)
        if original_url:
            os.environ['DATABASE_URL'] = original_url

def import_to_render(data):
    """Import data to Render PostgreSQL database"""
    # DATABASE_URL should be set to Render's database
    db = get_db()
    try:
        # Import users
        users_imported = 0
        for user_data in data['users']:
            existing = db.query(User).filter(User.id == user_data['id']).first()
            if not existing:
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    name=user_data['name'],
                    password_hash=user_data['password_hash'],
                    created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow(),
                    last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
                )
                db.add(user)
                users_imported += 1
        
        # Import trades
        trades_imported = 0
        for trade_data in data['trades']:
            existing = db.query(Trade).filter(Trade.id == trade_data['id']).first()
            if not existing:
                trade = Trade(
                    id=trade_data['id'],
                    user_id=trade_data['user_id'],
                    symbol=trade_data['symbol'],
                    action=trade_data['action'],
                    quantity=trade_data['quantity'],
                    price=trade_data['price'],
                    date=datetime.fromisoformat(trade_data['date'].replace('Z', '+00:00').split('+')[0]) if 'T' in trade_data['date'] else datetime.fromisoformat(trade_data['date']),
                    transaction_fee=trade_data['transaction_fee'],
                    sold_amount=trade_data['sold_amount'],
                    notes=trade_data['notes'],
                    option_type=trade_data['option_type'],
                    strike=trade_data['strike'],
                    expiration=trade_data['expiration'],
                    trade_type=trade_data['trade_type'],
                    created_at=datetime.fromisoformat(trade_data['created_at']) if trade_data.get('created_at') else datetime.utcnow()
                )
                db.add(trade)
                trades_imported += 1
        
        # Import portfolio
        portfolio_imported = 0
        for p_data in data['portfolio']:
            existing = db.query(PortfolioHistory).filter(PortfolioHistory.id == p_data['id']).first()
            if not existing:
                portfolio = PortfolioHistory(
                    id=p_data['id'],
                    user_id=p_data['user_id'],
                    date=datetime.fromisoformat(p_data['date'].replace('Z', '+00:00').split('+')[0]) if 'T' in p_data['date'] else datetime.fromisoformat(p_data['date']),
                    total_value=p_data['total_value'],
                    notes=p_data['notes'],
                    created_at=datetime.fromisoformat(p_data['created_at']) if p_data.get('created_at') else datetime.utcnow()
                )
                db.add(portfolio)
                portfolio_imported += 1
        
        # Import adjustments
        adjustments_imported = 0
        for a_data in data['adjustments']:
            existing = db.query(PortfolioAdjustment).filter(PortfolioAdjustment.id == a_data['id']).first()
            if not existing:
                adjustment = PortfolioAdjustment(
                    id=a_data['id'],
                    user_id=a_data['user_id'],
                    date=datetime.fromisoformat(a_data['date'].replace('Z', '+00:00').split('+')[0]) if 'T' in a_data['date'] else datetime.fromisoformat(a_data['date']),
                    amount=a_data['amount'],
                    description=a_data['description'],
                    created_at=datetime.fromisoformat(a_data['created_at']) if a_data.get('created_at') else datetime.utcnow()
                )
                db.add(adjustment)
                adjustments_imported += 1
        
        db.commit()
        print(f"✅ Imported to Render:")
        print(f"   Users: {users_imported}")
        print(f"   Trades: {trades_imported}")
        print(f"   Portfolio entries: {portfolio_imported}")
        print(f"   Adjustments: {adjustments_imported}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error importing: {e}")
        raise
    finally:
        close_db(db)

if __name__ == '__main__':
    print("🔄 Migrating data from local SQLite to Render PostgreSQL...")
    print("")
    print("⚠️  Make sure DATABASE_URL is set to Render's database URL")
    print("   Get it from: Render Dashboard → Your Database → Internal Database URL")
    print("")
    
    render_url = os.environ.get('DATABASE_URL')
    if not render_url or 'sqlite' in render_url:
        print("❌ DATABASE_URL not set or pointing to SQLite")
        print("   Set it like: export DATABASE_URL='postgresql://...'")
        print("   Or pass it as argument: python migrate_to_render.py 'postgresql://...'")
        if len(sys.argv) > 1:
            render_url = sys.argv[1]
            os.environ['DATABASE_URL'] = render_url
        else:
            sys.exit(1)
    
    print(f"📤 Exporting from local database...")
    data = export_from_local()
    print(f"   Found {len(data['users'])} users, {len(data['trades'])} trades")
    print("")
    
    print(f"📥 Importing to Render database...")
    import_to_render(data)
    print("")
    print("✅ Migration complete! You can now log in on Render.")

