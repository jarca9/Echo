#!/usr/bin/env python3
"""
Migrate trades and portfolio data from JSON files to database
"""
import json
import os
from datetime import datetime
from database import get_db, close_db, Trade, PortfolioHistory, PortfolioAdjustment

def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return datetime.utcnow()
    
    if isinstance(date_str, datetime):
        return date_str
    
    if isinstance(date_str, str):
        try:
            # Try ISO format first
            if 'T' in date_str:
                # Handle formats like "2025-11-19T07:08" or "2025-11-19T07:08:00"
                parts = date_str.split('T')
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else "00:00:00"
                
                # Pad time if needed
                time_parts = time_part.split(':')
                if len(time_parts) == 2:
                    time_part = f"{time_part}:00"
                
                return datetime.fromisoformat(f"{date_part}T{time_part}")
            else:
                # Try other formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
        except:
            pass
    
    return datetime.utcnow()

def migrate_trades(user_id: str, trades_file: str):
    """Migrate trades from JSON to database"""
    if not os.path.exists(trades_file):
        print(f"  ⏭️  No trades file found: {trades_file}")
        return 0
    
    with open(trades_file, 'r') as f:
        trades_data = json.load(f)
    
    if not trades_data:
        print(f"  ⏭️  No trades in file: {trades_file}")
        return 0
    
    db = get_db()
    migrated = 0
    skipped = 0
    
    try:
        for trade_data in trades_data:
            trade_id = trade_data.get('id')
            if not trade_id:
                print(f"  ⚠️  Skipping trade without ID: {trade_data.get('symbol', 'unknown')}")
                continue
            
            # Check if trade already exists
            existing = db.query(Trade).filter(
                Trade.id == trade_id,
                Trade.user_id == user_id
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Parse date
            trade_date = parse_date(trade_data.get('date'))
            
            # Create trade
            new_trade = Trade(
                id=trade_id,
                user_id=user_id,
                symbol=trade_data.get('symbol', '').upper(),
                action=trade_data.get('action', 'SELL').upper(),
                quantity=float(trade_data.get('quantity', 0)),
                price=float(trade_data.get('price', 0)),
                date=trade_date,
                transaction_fee=float(trade_data.get('transaction_fee', 0)),
                sold_amount=float(trade_data.get('sold_amount', 0)),
                notes=trade_data.get('notes', '') or '',
                option_type=(trade_data.get('option_type', '') or '').upper(),
                strike=float(trade_data.get('strike', 0)) if trade_data.get('strike') else None,
                expiration=trade_data.get('expiration', '') or '',
                trade_type=(trade_data.get('trade_type', 'OPTION') or 'OPTION').upper(),
                created_at=parse_date(trade_data.get('created_at')) if trade_data.get('created_at') else datetime.utcnow()
            )
            
            db.add(new_trade)
            migrated += 1
        
        db.commit()
        print(f"  ✅ Migrated {migrated} trades, skipped {skipped} (already exist)")
        return migrated
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error migrating trades: {e}")
        raise
    finally:
        close_db(db)

def migrate_portfolio_history(user_id: str, portfolio_file: str):
    """Migrate portfolio history from JSON to database"""
    if not os.path.exists(portfolio_file):
        print(f"  ⏭️  No portfolio history file found: {portfolio_file}")
        return 0
    
    with open(portfolio_file, 'r') as f:
        portfolio_data = json.load(f)
    
    if not portfolio_data:
        print(f"  ⏭️  No portfolio history in file: {portfolio_file}")
        return 0
    
    # Ensure it's a list
    if not isinstance(portfolio_data, list):
        portfolio_data = [portfolio_data]
    
    db = get_db()
    migrated = 0
    skipped = 0
    
    try:
        for entry_data in portfolio_data:
            if not isinstance(entry_data, dict) or 'date' not in entry_data:
                continue
            
            entry_id = entry_data.get('id')
            if not entry_id:
                entry_id = f"{user_id}_{entry_data.get('date')}"
            
            # Check if already exists
            existing = db.query(PortfolioHistory).filter(
                PortfolioHistory.id == entry_id,
                PortfolioHistory.user_id == user_id
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Parse date
            entry_date = parse_date(entry_data.get('date'))
            entry_date = entry_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            new_entry = PortfolioHistory(
                id=entry_id,
                user_id=user_id,
                date=entry_date,
                total_value=float(entry_data.get('amount', entry_data.get('total_value', 0))),
                notes=entry_data.get('notes', '') or '',
                created_at=parse_date(entry_data.get('created_at')) if entry_data.get('created_at') else datetime.utcnow()
            )
            
            db.add(new_entry)
            migrated += 1
        
        db.commit()
        print(f"  ✅ Migrated {migrated} portfolio entries, skipped {skipped} (already exist)")
        return migrated
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error migrating portfolio history: {e}")
        raise
    finally:
        close_db(db)

def migrate_portfolio_adjustments(user_id: str, adjustments_file: str):
    """Migrate portfolio adjustments from JSON to database"""
    if not os.path.exists(adjustments_file):
        print(f"  ⏭️  No portfolio adjustments file found: {adjustments_file}")
        return 0
    
    with open(adjustments_file, 'r') as f:
        adjustments_data = json.load(f)
    
    if not adjustments_data:
        print(f"  ⏭️  No portfolio adjustments in file: {adjustments_file}")
        return 0
    
    # Ensure it's a list
    if not isinstance(adjustments_data, list):
        adjustments_data = [adjustments_data]
    
    db = get_db()
    migrated = 0
    skipped = 0
    
    try:
        for adj_data in adjustments_data:
            if not isinstance(adj_data, dict) or 'date' not in adj_data:
                continue
            
            adj_id = adj_data.get('id')
            if not adj_id:
                adj_id = f"{user_id}_adj_{adj_data.get('date')}"
            
            # Check if already exists
            existing = db.query(PortfolioAdjustment).filter(
                PortfolioAdjustment.id == adj_id,
                PortfolioAdjustment.user_id == user_id
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Parse date
            adj_date = parse_date(adj_data.get('date'))
            adj_date = adj_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            new_adj = PortfolioAdjustment(
                id=adj_id,
                user_id=user_id,
                date=adj_date,
                amount=float(adj_data.get('amount', 0)),
                description=adj_data.get('label', adj_data.get('description', '')) or '',
                created_at=parse_date(adj_data.get('created_at')) if adj_data.get('created_at') else datetime.utcnow()
            )
            
            db.add(new_adj)
            migrated += 1
        
        db.commit()
        print(f"  ✅ Migrated {migrated} portfolio adjustments, skipped {skipped} (already exist)")
        return migrated
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error migrating portfolio adjustments: {e}")
        raise
    finally:
        close_db(db)

def migrate_user_data(user_id: str):
    """Migrate all data for a user"""
    user_data_dir = f'user_data/{user_id}'
    
    if not os.path.exists(user_data_dir):
        print(f"❌ User data directory not found: {user_data_dir}")
        return
    
    print(f"🔄 Migrating data for user: {user_id}")
    print("")
    
    # Migrate trades
    trades_file = os.path.join(user_data_dir, 'trades_history.json')
    print("📊 Migrating trades...")
    migrate_trades(user_id, trades_file)
    
    # Migrate portfolio history
    portfolio_file = os.path.join(user_data_dir, 'portfolio_history.json')
    print("📈 Migrating portfolio history...")
    migrate_portfolio_history(user_id, portfolio_file)
    
    # Migrate portfolio adjustments
    adjustments_file = os.path.join(user_data_dir, 'portfolio_adjustments.json')
    print("💰 Migrating portfolio adjustments...")
    migrate_portfolio_adjustments(user_id, adjustments_file)
    
    print("")
    print("✅ Migration complete!")

if __name__ == '__main__':
    # User ID for jaydennling@gmail.com
    user_id = 'guAVZRulVEvdI_YWQCb3xg'
    migrate_user_data(user_id)

