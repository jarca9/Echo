"""
Strategy Backtesting Engine
Test "what if" scenarios on historical trade data
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from collections import defaultdict

class StrategyBacktester:
    """Backtest trading strategies on historical data"""
    
    TRANSACTION_FEE = 2.00
    
    def __init__(self, trades: List[Dict]):
        self.original_trades = trades
        self.trades = trades.copy()
    
    def backtest(self, filters: Dict) -> Dict:
        """
        Backtest with various filters/rules
        
        filters can include:
        - day_of_week: ['Monday', 'Tuesday', etc.] or None
        - symbols: ['AAPL', 'TSLA'] or None (only trade these)
        - exclude_symbols: ['XYZ'] or None (exclude these)
        - min_win_rate: float (only trade symbols with this win rate)
        - strategies: ['Covered Call'] or None
        - time_range: {'start': date, 'end': date} or None
        - stop_loss: float (exit if loss exceeds this %)
        - take_profit: float (exit if profit exceeds this %)
        """
        filtered_trades = self._apply_filters(filters)
        
        if not filtered_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'max_win': 0,
                'max_loss': 0,
                'original_trades': len(self.original_trades),
                'filtered_trades': 0
            }
        
        results = self._calculate_results(filtered_trades)
        results['original_trades'] = len(self.original_trades)
        results['filtered_trades'] = len(filtered_trades)
        results['trades_removed'] = len(self.original_trades) - len(filtered_trades)
        
        return results
    
    def _apply_filters(self, filters: Dict) -> List[Dict]:
        """Apply filters to trades"""
        filtered = []
        
        for trade in self.original_trades:
            if trade.get('action', '').upper() not in ['SELL', 'CLOSE']:
                continue
            
            # Day of week filter
            if filters.get('day_of_week'):
                try:
                    trade_date = self._parse_date(trade.get('date'))
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_name = day_names[trade_date.weekday()]
                    if day_name not in filters['day_of_week']:
                        continue
                except:
                    continue
            
            # Symbol filter
            if filters.get('symbols'):
                if trade.get('symbol') not in filters['symbols']:
                    continue
            
            # Exclude symbols
            if filters.get('exclude_symbols'):
                if trade.get('symbol') in filters['exclude_symbols']:
                    continue
            
            # Strategy filter
            if filters.get('strategies'):
                strategy = trade.get('strategy', 'No Strategy') or 'No Strategy'
                if strategy not in filters['strategies']:
                    continue
            
            # Time range filter
            if filters.get('time_range'):
                try:
                    trade_date = self._parse_date(trade.get('date'))
                    start = filters['time_range'].get('start')
                    end = filters['time_range'].get('end')
                    
                    if start and trade_date < start:
                        continue
                    if end and trade_date > end:
                        continue
                except:
                    continue
            
            filtered.append(trade)
        
        # Min win rate filter (requires calculating win rates first)
        if filters.get('min_win_rate'):
            symbol_win_rates = self._calculate_symbol_win_rates(filtered)
            filtered = [
                t for t in filtered
                if symbol_win_rates.get(t.get('symbol', ''), 0) >= filters['min_win_rate']
            ]
        
        return filtered
    
    def _calculate_symbol_win_rates(self, trades: List[Dict]) -> Dict:
        """Calculate win rate per symbol"""
        symbol_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
        
        for trade in trades:
            symbol = trade.get('symbol', '')
            pnl = self._calculate_trade_pnl(trade)
            symbol_stats[symbol]['total'] += 1
            if pnl > 0:
                symbol_stats[symbol]['wins'] += 1
        
        win_rates = {}
        for symbol, stats in symbol_stats.items():
            if stats['total'] > 0:
                win_rates[symbol] = (stats['wins'] / stats['total']) * 100
        
        return win_rates
    
    def _calculate_results(self, trades: List[Dict]) -> Dict:
        """Calculate backtest results"""
        total_trades = len(trades)
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0
        wins = []
        losses = []
        
        for trade in trades:
            pnl = self._calculate_trade_pnl(trade)
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
                wins.append(pnl)
            else:
                losing_trades += 1
                losses.append(abs(pnl))
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        max_win = max(wins) if wins else 0
        max_loss = max(losses) if losses else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 1),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(avg_pnl, 2),
            'max_win': round(max_win, 2),
            'max_loss': round(max_loss, 2),
            'avg_win': round(sum(wins) / len(wins), 2) if wins else 0,
            'avg_loss': round(sum(losses) / len(losses), 2) if losses else 0
        }
    
    def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Compare multiple backtest scenarios"""
        results = {}
        
        for i, scenario in enumerate(scenarios):
            scenario_name = scenario.get('name', f'Scenario {i+1}')
            filters = scenario.get('filters', {})
            results[scenario_name] = self.backtest(filters)
        
        return results
    
    def _calculate_trade_pnl(self, trade: Dict) -> float:
        """Calculate PnL for a trade"""
        try:
            sold_amount = float(trade.get('sold_amount', 0))
            if sold_amount > 0:
                quantity = float(trade.get('quantity', 0))
                buy_price = float(trade.get('price', 0))
                total_cost = quantity * buy_price * 100
                pnl = sold_amount - total_cost - self.TRANSACTION_FEE
                return pnl
        except:
            pass
        return 0.0
    
    def _parse_date(self, date_str) -> datetime:
        """Parse date string to datetime"""
        if not date_str:
            return datetime.now()
        
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







