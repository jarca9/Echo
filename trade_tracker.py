"""
Options Trade tracking and PnL calculation system (No API Required)
Now using PostgreSQL database
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from database import get_db, close_db, Trade, PortfolioHistory, PortfolioAdjustment

class TradeTracker:
    """Tracks options trades and calculates PnL metrics - uses PostgreSQL"""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize TradeTracker for a specific user.
        If user_id is None, uses 'default' for backward compatibility.
        """
        self.user_id = user_id or 'default'
    
    def load_trades(self) -> List[Dict]:
        """Load trades from database"""
        db = get_db()
        try:
            trades = db.query(Trade).filter(Trade.user_id == self.user_id).order_by(Trade.date.desc()).all()
            result = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'action': trade.action,
                    'quantity': float(trade.quantity),
                    'price': float(trade.price),
                    'date': trade.date.isoformat() if isinstance(trade.date, datetime) else trade.date,
                    'transaction_fee': float(trade.transaction_fee),
                    'sold_amount': float(trade.sold_amount),
                    'notes': trade.notes or '',
                    'option_type': trade.option_type or '',
                    'strike': float(trade.strike) if trade.strike else 0,
                    'expiration': trade.expiration or '',
                    'trade_type': trade.trade_type or 'OPTION',
                    'created_at': trade.created_at.isoformat() if trade.created_at else datetime.now().isoformat()
                }
                result.append(trade_dict)
            return result
        except Exception as e:
            print(f"Error loading trades: {e}")
            return []
        finally:
            close_db(db)
    
    def save_trades(self):
        """Save trades to database (no-op, trades are saved individually)"""
        pass  # Trades are saved individually via add_trade/update_trade
    
    def load_portfolio_history(self) -> List[Dict]:
        """Load daily portfolio snapshots from database"""
        db = get_db()
        try:
            entries = db.query(PortfolioHistory).filter(
                PortfolioHistory.user_id == self.user_id
            ).order_by(PortfolioHistory.date.asc()).all()
            
            result = []
            for entry in entries:
                result.append({
                    'id': entry.id,
                    'date': entry.date.strftime('%Y-%m-%d') if isinstance(entry.date, datetime) else entry.date,
                    'amount': float(entry.total_value),
                    'notes': entry.notes or '',
                    'created_at': entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat()
                })
            return result
        except Exception as e:
            print(f"Error loading portfolio history: {e}")
            return []
        finally:
            close_db(db)
    
    def save_portfolio_history(self):
        """Save portfolio history to database (no-op, entries are saved individually)"""
        pass  # Portfolio entries are saved individually via record_portfolio_value
    
    def load_portfolio_adjustments(self) -> List[Dict]:
        """Load manual portfolio adjustments from database"""
        db = get_db()
        try:
            adjustments = db.query(PortfolioAdjustment).filter(
                PortfolioAdjustment.user_id == self.user_id
            ).order_by(PortfolioAdjustment.date.asc()).all()
            
            result = []
            for adj in adjustments:
                result.append({
                    'id': adj.id,
                    'date': adj.date.strftime('%Y-%m-%d') if isinstance(adj.date, datetime) else adj.date,
                    'amount': float(adj.amount),
                    'label': adj.description or '',
                    'created_at': adj.created_at.isoformat() if adj.created_at else datetime.now().isoformat(),
                    'apply_to': 'since_start'  # Default for compatibility
                })
            return result
        except Exception as e:
            print(f"Error loading portfolio adjustments: {e}")
            return []
        finally:
            close_db(db)
    
    @property
    def trades(self) -> List[Dict]:
        """Get trades (property for backward compatibility)"""
        return self.load_trades()
    
    @property
    def portfolio_history(self) -> List[Dict]:
        """Get portfolio history (property for backward compatibility)"""
        return self.load_portfolio_history()
    
    @property
    def portfolio_adjustments(self) -> List[Dict]:
        """Get portfolio adjustments (property for backward compatibility)"""
        return self.load_portfolio_adjustments()
    
    def add_trade(self, trade_data: Dict) -> Dict:
        """Add a new options trade"""
        db = get_db()
        try:
            # Parse date
            date_str = trade_data.get('date', datetime.now().isoformat())
            trade_date = self._parse_date(date_str)
            
            trade_id = str(uuid.uuid4())
            new_trade = Trade(
                id=trade_id,
                user_id=self.user_id,
                symbol=trade_data.get('symbol', '').upper(),
                action=trade_data.get('action', 'SELL').upper(),
                quantity=float(trade_data.get('quantity', 0)),
                price=float(trade_data.get('price', 0)),
                date=trade_date,
                transaction_fee=float(trade_data.get('transaction_fee', 0)),
                sold_amount=float(trade_data.get('sold_amount', 0)),
                notes=trade_data.get('notes', ''),
                option_type=trade_data.get('option_type', 'CALL').upper() if trade_data.get('trade_type', '').upper() == 'OPTION' else '',
                strike=float(trade_data.get('strike', 0)) if trade_data.get('trade_type', '').upper() == 'OPTION' else None,
                expiration=trade_data.get('expiration', ''),
                trade_type=trade_data.get('trade_type', 'OPTION').upper(),
                created_at=datetime.utcnow()
            )
            
            db.add(new_trade)
            db.commit()
            
            # Return as dict for compatibility
            return {
                'id': trade_id,
                'symbol': new_trade.symbol,
                'action': new_trade.action,
                'quantity': float(new_trade.quantity),
                'price': float(new_trade.price),
                'date': trade_date.isoformat(),
                'transaction_fee': float(new_trade.transaction_fee),
                'sold_amount': float(new_trade.sold_amount),
                'notes': new_trade.notes or '',
                'option_type': new_trade.option_type or '',
                'strike': float(new_trade.strike) if new_trade.strike else 0,
                'expiration': new_trade.expiration or '',
                'trade_type': new_trade.trade_type or 'OPTION',
                'created_at': new_trade.created_at.isoformat()
            }
        except Exception as e:
            db.rollback()
            print(f"Error adding trade: {e}")
            raise
        finally:
            close_db(db)
    
    def update_trade(self, trade_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing trade"""
        db = get_db()
        try:
            trade = db.query(Trade).filter(
                Trade.id == trade_id,
                Trade.user_id == self.user_id
            ).first()
            
            if not trade:
                return None
            
            # Update fields
            for key, value in updates.items():
                if key == 'quantity':
                    trade.quantity = float(value)
                elif key == 'price':
                    trade.price = float(value)
                elif key == 'strike':
                    trade.strike = float(value) if value else None
                elif key == 'transaction_fee':
                    trade.transaction_fee = float(value)
                elif key == 'sold_amount':
                    trade.sold_amount = float(value)
                elif key == 'symbol':
                    trade.symbol = str(value).upper()
                elif key == 'date':
                    trade.date = self._parse_date(value)
                elif key == 'action':
                    trade.action = str(value).upper()
                elif key == 'option_type':
                    trade.option_type = str(value).upper() if value else ''
                elif key == 'expiration':
                    trade.expiration = str(value) if value else ''
                elif key == 'trade_type':
                    trade.trade_type = str(value).upper()
                elif key == 'notes':
                    trade.notes = str(value) if value else ''
            
            db.commit()
            
            # Return as dict
            return {
                'id': trade.id,
                'symbol': trade.symbol,
                'action': trade.action,
                'quantity': float(trade.quantity),
                'price': float(trade.price),
                'date': trade.date.isoformat() if isinstance(trade.date, datetime) else trade.date,
                'transaction_fee': float(trade.transaction_fee),
                'sold_amount': float(trade.sold_amount),
                'notes': trade.notes or '',
                'option_type': trade.option_type or '',
                'strike': float(trade.strike) if trade.strike else 0,
                'expiration': trade.expiration or '',
                'trade_type': trade.trade_type or 'OPTION',
                'created_at': trade.created_at.isoformat() if trade.created_at else datetime.now().isoformat()
            }
        except Exception as e:
            db.rollback()
            print(f"Error updating trade: {e}")
            return None
        finally:
            close_db(db)
    
    def delete_trade(self, trade_id: str) -> bool:
        """Delete a trade"""
        db = get_db()
        try:
            trade = db.query(Trade).filter(
                Trade.id == trade_id,
                Trade.user_id == self.user_id
            ).first()
            
            if trade:
                db.delete(trade)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error deleting trade: {e}")
            return False
        finally:
            close_db(db)

    def record_portfolio_value(self, amount: float, date_str: Optional[str] = None, notes: str = '') -> Dict:
        """Record or update total portfolio value for a given day"""
        db = get_db()
        try:
            if date_str:
                date_obj = self._parse_date(date_str)
            else:
                date_obj = datetime.now()
            
            # Normalize to date only (no time)
            date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            normalized_amount = round(float(amount), 2)
            
            # Check if entry already exists for date
            existing = db.query(PortfolioHistory).filter(
                PortfolioHistory.user_id == self.user_id,
                PortfolioHistory.date == date_obj
            ).first()
            
            if existing:
                existing.total_value = normalized_amount
                existing.notes = notes
                db.commit()
                return {
                    'id': existing.id,
                    'date': date_obj.strftime('%Y-%m-%d'),
                    'amount': normalized_amount,
                    'notes': notes,
                    'created_at': existing.created_at.isoformat() if existing.created_at else datetime.now().isoformat()
                }
            
            # Create new entry
            entry_id = str(uuid.uuid4())
            new_entry = PortfolioHistory(
                id=entry_id,
                user_id=self.user_id,
                date=date_obj,
                total_value=normalized_amount,
                notes=notes,
                created_at=datetime.utcnow()
            )
            
            db.add(new_entry)
            db.commit()
            
            return {
                'id': entry_id,
                'date': date_obj.strftime('%Y-%m-%d'),
                'amount': normalized_amount,
                'notes': notes,
                'created_at': new_entry.created_at.isoformat()
            }
        except Exception as e:
            db.rollback()
            print(f"Error recording portfolio value: {e}")
            raise
        finally:
            close_db(db)
    
    def get_portfolio_history(self, limit: int = 30) -> List[Dict]:
        """Return recent portfolio totals (default last 30 days)"""
        daily_balances = self.get_portfolio_daily_balances()
        if not daily_balances:
            return []
        
        sorted_dates = sorted(daily_balances.keys(), reverse=True)
        return [
            {
                'date': date_str,
                'amount': daily_balances[date_str]
            }
            for date_str in sorted_dates[:limit]
        ]
    
    def get_portfolio_daily_balances(self) -> Dict[str, float]:
        """Compute cumulative portfolio balances from first recorded amount"""
        portfolio_history = self.load_portfolio_history()
        if not portfolio_history:
            return {}
        
        # Find earliest recorded amount as base
        base_entry = min(
            portfolio_history,
            key=lambda e: self._parse_date(e.get('date'))
        )
        base_date = self._parse_date(base_entry.get('date'))
        base_amount = float(base_entry.get('amount', 0))
        
        # Aggregate realized PnL by day starting from base date
        pnl_by_day = defaultdict(float)
        last_trade_date = base_date
        trades = self.load_trades()
        
        for trade in trades:
            action = trade.get('action', '').upper()
            if action in ['SELL', 'CLOSE']:
                trade_date = self._parse_date(trade.get('date'))
                if trade_date >= base_date:
                    date_key = trade_date.strftime('%Y-%m-%d')
                    pnl_by_day[date_key] += self.calculate_trade_pnl(trade)
                    if trade_date > last_trade_date:
                        last_trade_date = trade_date
        
        # Determine end date (latest of last trade or today)
        today = datetime.now()
        end_date = max(last_trade_date, today)
        
        daily_balances = {}
        cumulative_pnl = 0.0
        current_date = base_date
        
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            if date_key in pnl_by_day:
                cumulative_pnl += pnl_by_day[date_key]
            daily_balances[date_key] = round(base_amount + cumulative_pnl, 2)
            current_date += timedelta(days=1)
        
        return daily_balances
    
    def get_portfolio_by_date(self, year: int, month: int) -> Dict:
        """Get portfolio balances grouped by date for calendar view"""
        portfolio_by_date = {}
        daily_balances = self.get_portfolio_daily_balances()
        
        for date_str, amount in daily_balances.items():
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj.year == year and date_obj.month == month:
                portfolio_by_date[date_str] = {
                    'amount': amount
                }
        
        return portfolio_by_date
    
    def get_trades_by_date(self, year: int, month: int) -> Dict:
        """Get trades grouped by date for calendar view"""
        trades_by_date = defaultdict(list)
        trades = self.load_trades()
        
        for trade in trades:
            trade_date = self._parse_date(trade.get('date'))
            if trade_date.year == year and trade_date.month == month:
                date_key = trade_date.strftime('%Y-%m-%d')
                trades_by_date[date_key].append(trade)
        
        # Calculate daily PnL (includes transaction fees) and per-trade PnL / % return
        result = {}
        for date_str, day_trades in trades_by_date.items():
            day_pnl = 0.0

            for t in day_trades:
                action = t.get('action', '').upper()
                if action in ['SELL', 'CLOSE']:
                    trade_pnl = self.calculate_trade_pnl(t)
                    day_pnl += trade_pnl

                    # Attach per-trade PnL (after fees)
                    t['pnl'] = round(trade_pnl, 2)

                    # Compute % return relative to capital in the trade, if we have sold_amount
                    sold_amount = float(t.get('sold_amount', 0) or 0)
                    if sold_amount > 0:
                        cost_basis = sold_amount - trade_pnl  # works for both wins and losses
                        if cost_basis > 0:
                            t['pnl_pct'] = round(trade_pnl / cost_basis * 100.0, 2)

            result[date_str] = {
                'trades': day_trades,
                'pnl': round(day_pnl, 2),
                'count': len(day_trades)
            }
        
        return result
    
    def calculate_trade_pnl(self, trade: Dict) -> float:
        """Calculate PnL for a single trade using FIFO matching (includes transaction fee if provided)"""
        try:
            # Get transaction fee from trade data, default to 0 if not provided
            transaction_fee = float(trade.get('transaction_fee', 0))
            
            action = trade.get('action', '').upper()
            
            # For SELL/CLOSE trades, use FIFO to find matching BUY trade
            if action in ['SELL', 'CLOSE']:
                sold_amount = float(trade.get('sold_amount', 0))
                if sold_amount > 0:
                    # Use FIFO to find matching BUY trade(s)
                    quantity = float(trade.get('quantity', 0))
                    trade_date = self._parse_date(trade.get('date'))
                    trades = self.load_trades()
                    
                    # Find matching BUY trades using FIFO
                    if trade.get('trade_type', '').upper() == 'OPTION':
                        symbol_key = f"{trade.get('symbol')}_{trade.get('strike')}_{trade.get('option_type')}"
                    else:
                        symbol_key = trade.get('symbol', '')
                    
                    buy_trades = [
                        t for t in trades
                        if t.get('action', '').upper() in ['BUY', 'OPEN']
                        and self._get_symbol_key(t) == symbol_key
                        and self._parse_date(t.get('date')) < trade_date
                    ]
                    buy_trades.sort(key=lambda x: self._parse_date(x.get('date')))
                    
                    # Calculate total cost using FIFO matching
                    remaining_qty = quantity
                    total_cost = 0.0
                    total_buy_fees = 0.0  # Track fees from matched BUY trades
                    
                    for buy_trade in buy_trades:
                        if remaining_qty <= 0:
                            break
                        buy_qty = float(buy_trade.get('quantity', 0))
                        buy_price = float(buy_trade.get('price', 0))
                        buy_fee = float(buy_trade.get('transaction_fee', 0))
                        matched_qty = min(remaining_qty, buy_qty)
                        total_cost += matched_qty * buy_price * 100  # Options are per 100 shares
                        # Proportionally allocate BUY trade fee based on matched quantity
                        total_buy_fees += (matched_qty / buy_qty) * buy_fee if buy_qty > 0 else 0
                        remaining_qty -= matched_qty
                    
                    # If we couldn't match all quantity, use the SELL price as fallback (shouldn't happen in normal cases)
                    if remaining_qty > 0:
                        sell_price = float(trade.get('price', 0))
                        total_cost += remaining_qty * sell_price * 100
                    
                    # Total fees = SELL trade fee + matched BUY trade fees
                    total_fees = transaction_fee + total_buy_fees
                    pnl = sold_amount - total_cost - total_fees
                    return pnl
            
            # Fallback to old method if sold_amount not available
            if trade.get('trade_type', '').upper() == 'OPTION':
                symbol_key = f"{trade.get('symbol')}_{trade.get('strike')}_{trade.get('option_type')}"
            else:
                symbol_key = trade.get('symbol', '')
            
            action = trade.get('action', '').upper()
            quantity = float(trade.get('quantity', 0))
            price = float(trade.get('price', 0))
            trades = self.load_trades()
            
            # For SELL/CLOSE trades, find matching BUY trades
            if action in ['SELL', 'CLOSE']:
                trade_date = self._parse_date(trade.get('date'))
                buy_trades = [
                    t for t in trades
                    if self._get_symbol_key(t) == symbol_key
                    and t.get('action', '').upper() in ['BUY', 'OPEN']
                    and self._parse_date(t.get('date')) < trade_date
                ]
                
                if buy_trades:
                    total_cost = sum(float(t.get('quantity', 0)) * float(t.get('price', 0)) * 100 for t in buy_trades)
                    total_quantity = sum(float(t.get('quantity', 0)) for t in buy_trades)
                    
                    if total_quantity > 0:
                        avg_buy_price = total_cost / total_quantity
                        transaction_fee = float(trade.get('transaction_fee', 0))
                        pnl = (price * 100 - avg_buy_price) * quantity - transaction_fee  # Subtract transaction fee
                        return pnl
            
            return 0.0
        except Exception as e:
            print(f"Error calculating PnL: {e}")
        return 0.0
    
    def _get_symbol_key(self, trade: Dict) -> str:
        """Get unique identifier for trade matching"""
        if trade.get('trade_type', '').upper() == 'OPTION':
            return f"{trade.get('symbol')}_{trade.get('strike')}_{trade.get('option_type')}"
        return trade.get('symbol', '')
    
    def _parse_date(self, date_str) -> datetime:
        """Parse date string to datetime"""
        if not date_str:
            return datetime.now()
        
        if isinstance(date_str, datetime):
            return date_str
        
        if isinstance(date_str, str):
            try:
                if 'T' in date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
                else:
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except:
                            continue
            except:
                pass
        
        return datetime.now()
    
    def get_pnl_metrics(self) -> Dict:
        """Calculate PnL metrics for different time periods"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)
        
        day_pnl = 0.0
        week_pnl = 0.0
        month_pnl = 0.0
        all_time_pnl = 0.0
        
        trades = self.load_trades()
        
        # Calculate PnL for each trade (fees already included in calculate_trade_pnl)
        for trade in trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                trade_pnl = self.calculate_trade_pnl(trade)
                trade_date = self._parse_date(trade.get('date'))
                
                if trade_date >= today_start:
                    day_pnl += trade_pnl
                if trade_date >= week_start:
                    week_pnl += trade_pnl
                if trade_date >= month_start:
                    month_pnl += trade_pnl
                all_time_pnl += trade_pnl
        
        # Calculate win rate
        total_trades = 0
        winning_trades = 0
        for trade in trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                trade_pnl = self.calculate_trade_pnl(trade)
                total_trades += 1
                if trade_pnl > 0:
                    winning_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate advanced metrics
        winning_pnl = 0
        losing_pnl = 0
        all_pnls = []
        
        for trade in trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                trade_pnl = self.calculate_trade_pnl(trade)
                all_pnls.append(trade_pnl)
                if trade_pnl > 0:
                    winning_pnl += trade_pnl
                else:
                    losing_pnl += abs(trade_pnl)
        
        profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else (winning_pnl if winning_pnl > 0 else 0)
        
        # Calculate average win/loss in dollars
        wins = [p for p in all_pnls if p > 0]
        losses = [abs(p) for p in all_pnls if p < 0]
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # Calculate average % loss per losing trade (based on capital in the trade)
        loss_percents = []
        for trade in trades:
            if trade.get('action', '').upper() not in ['SELL', 'CLOSE']:
                continue
            trade_pnl = self.calculate_trade_pnl(trade)
            if trade_pnl >= 0:
                continue  # only losing trades

            sold_amount = float(trade.get('sold_amount', 0) or 0)
            if sold_amount <= 0:
                continue

            # Effective capital in the trade ≈ sold_amount - pnl (since pnl is negative for losers)
            cost_basis = sold_amount - trade_pnl
            if cost_basis <= 0:
                continue

            loss_pct = abs(trade_pnl) / cost_basis * 100.0
            loss_percents.append(loss_pct)

        avg_loss_pct = sum(loss_percents) / len(loss_percents) if loss_percents else 0
        
        # Calculate expectancy
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss) if total_trades > 0 else 0
        
        return {
            'day_pnl': round(day_pnl, 2),
            'week_pnl': round(week_pnl, 2),
            'month_pnl': round(month_pnl, 2),
            'all_time_pnl': round(all_time_pnl, 2),
            'win_rate': round(win_rate, 1),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'avg_loss_pct': round(avg_loss_pct, 2),
            'expectancy': round(expectancy, 2),
            'largest_win': round(max(wins), 2) if wins else 0,
            'largest_loss': round(max(losses), 2) if losses else 0,
            'last_updated': now.isoformat()
        }
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        trades = self.load_trades()
        sorted_trades = sorted(
            trades,
            key=lambda x: self._parse_date(x.get('date')),
            reverse=True
        )
        return sorted_trades[:limit]
    
    def get_open_positions(self) -> List[Dict]:
        """Get current open positions"""
        symbol_positions = defaultdict(lambda: {
            'quantity': 0,
            'total_cost': 0,
            'trades': [],
            'symbol': '',
            'strike': 0,
            'option_type': '',
            'expiration': ''
        })
        
        trades = self.load_trades()
        for trade in trades:
            symbol_key = self._get_symbol_key(trade)
            action = trade.get('action', '').upper()
            quantity = float(trade.get('quantity', 0))
            
            if symbol_key not in symbol_positions:
                symbol_positions[symbol_key]['symbol'] = trade.get('symbol', '')
                symbol_positions[symbol_key]['strike'] = trade.get('strike', 0)
                symbol_positions[symbol_key]['option_type'] = trade.get('option_type', '')
                symbol_positions[symbol_key]['expiration'] = trade.get('expiration', '')
            
            if action in ['BUY', 'OPEN']:
                symbol_positions[symbol_key]['quantity'] += quantity
                symbol_positions[symbol_key]['total_cost'] += quantity * float(trade.get('price', 0))
                symbol_positions[symbol_key]['trades'].append(trade)
            elif action in ['SELL', 'CLOSE']:
                symbol_positions[symbol_key]['quantity'] -= quantity
        
        # Filter to only open positions
        open_positions = []
        for symbol_key, pos in symbol_positions.items():
            if pos['quantity'] > 0:
                avg_price = pos['total_cost'] / sum(float(t.get('quantity', 0)) for t in pos['trades']) if pos['trades'] else 0
                open_positions.append({
                    'symbol': pos['symbol'],
                    'strike': pos['strike'],
                    'option_type': pos['option_type'],
                    'expiration': pos['expiration'],
                    'quantity': round(pos['quantity'], 4),
                    'avg_price': round(avg_price, 2),
                    'total_cost': round(pos['total_cost'], 2)
                })
        
        return open_positions
