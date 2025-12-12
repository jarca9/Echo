"""
AI-Powered Personal Trading Coach
Analyzes trade patterns and provides personalized insights
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class AITradingCoach:
    """Analyzes trading patterns and provides personalized recommendations"""
    
    def __init__(self, trades: List[Dict]):
        self.trades = trades
    
    def analyze_patterns(self) -> Dict:
        """Analyze all trading patterns and return insights"""
        if not self.trades:
            return {'error': 'No trades to analyze'}
        
        insights = {
            'best_symbols': self._find_best_symbols(),
            'best_days': self._find_best_days(),
            'best_strategies': self._find_best_strategies(),
            'time_patterns': self._analyze_time_patterns(),
            'risk_analysis': self._analyze_risk(),
            'mistakes': self._identify_mistakes(),
            'recommendations': [],
            'performance_breakdown': self._performance_breakdown()
        }
        
        # Generate personalized recommendations
        insights['recommendations'] = self._generate_recommendations(insights)
        
        return insights
    
    def _find_best_symbols(self) -> List[Dict]:
        """Find symbols with highest win rates and profits"""
        symbol_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'trades': []})
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                symbol = trade.get('symbol', '')
                pnl = self._calculate_trade_pnl(trade)
                
                symbol_stats[symbol]['trades'].append(trade)
                symbol_stats[symbol]['pnl'] += pnl
                if pnl > 0:
                    symbol_stats[symbol]['wins'] += 1
                else:
                    symbol_stats[symbol]['losses'] += 1
        
        results = []
        for symbol, stats in symbol_stats.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                win_rate = (stats['wins'] / total) * 100
                avg_pnl = stats['pnl'] / total if total > 0 else 0
                results.append({
                    'symbol': symbol,
                    'win_rate': round(win_rate, 1),
                    'total_trades': total,
                    'total_pnl': round(stats['pnl'], 2),
                    'avg_pnl': round(avg_pnl, 2)
                })
        
        return sorted(results, key=lambda x: x['total_pnl'], reverse=True)[:5]
    
    def _find_best_days(self) -> List[Dict]:
        """Find days of week with best performance"""
        day_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'count': 0})
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                try:
                    trade_date = self._parse_date(trade.get('date'))
                    day_name = day_names[trade_date.weekday()]
                    pnl = self._calculate_trade_pnl(trade)
                    
                    day_stats[day_name]['count'] += 1
                    day_stats[day_name]['pnl'] += pnl
                    if pnl > 0:
                        day_stats[day_name]['wins'] += 1
                    else:
                        day_stats[day_name]['losses'] += 1
                except:
                    continue
        
        results = []
        for day, stats in day_stats.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                win_rate = (stats['wins'] / total) * 100
                results.append({
                    'day': day,
                    'win_rate': round(win_rate, 1),
                    'total_trades': total,
                    'total_pnl': round(stats['pnl'], 2),
                    'avg_pnl': round(stats['pnl'] / total, 2) if total > 0 else 0
                })
        
        return sorted(results, key=lambda x: x['total_pnl'], reverse=True)
    
    def _find_best_strategies(self) -> List[Dict]:
        """Find strategies with best performance"""
        strategy_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'count': 0})
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                strategy = trade.get('strategy', 'No Strategy')
                if not strategy:
                    strategy = 'No Strategy'
                
                pnl = self._calculate_trade_pnl(trade)
                strategy_stats[strategy]['count'] += 1
                strategy_stats[strategy]['pnl'] += pnl
                if pnl > 0:
                    strategy_stats[strategy]['wins'] += 1
                else:
                    strategy_stats[strategy]['losses'] += 1
        
        results = []
        for strategy, stats in strategy_stats.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                win_rate = (stats['wins'] / total) * 100
                results.append({
                    'strategy': strategy,
                    'win_rate': round(win_rate, 1),
                    'total_trades': total,
                    'total_pnl': round(stats['pnl'], 2),
                    'avg_pnl': round(stats['pnl'] / total, 2) if total > 0 else 0
                })
        
        return sorted(results, key=lambda x: x['total_pnl'], reverse=True)
    
    def _analyze_time_patterns(self) -> Dict:
        """Analyze time of day patterns"""
        hour_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'count': 0})
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                try:
                    trade_date = self._parse_date(trade.get('date'))
                    hour = trade_date.hour
                    pnl = self._calculate_trade_pnl(trade)
                    
                    hour_stats[hour]['count'] += 1
                    hour_stats[hour]['pnl'] += pnl
                    if pnl > 0:
                        hour_stats[hour]['wins'] += 1
                    else:
                        hour_stats[hour]['losses'] += 1
                except:
                    continue
        
        best_hour = max(hour_stats.items(), key=lambda x: x[1]['pnl']) if hour_stats else None
        
        return {
            'best_hour': best_hour[0] if best_hour else None,
            'best_hour_pnl': round(best_hour[1]['pnl'], 2) if best_hour else 0,
            'best_hour_win_rate': round((best_hour[1]['wins'] / (best_hour[1]['wins'] + best_hour[1]['losses']) * 100), 1) if best_hour and (best_hour[1]['wins'] + best_hour[1]['losses']) > 0 else 0
        }
    
    def _analyze_risk(self) -> Dict:
        """Analyze risk patterns"""
        winning_trades = []
        losing_trades = []
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                pnl = self._calculate_trade_pnl(trade)
                if pnl > 0:
                    winning_trades.append(pnl)
                else:
                    losing_trades.append(abs(pnl))
        
        avg_win = statistics.mean(winning_trades) if winning_trades else 0
        avg_loss = statistics.mean(losing_trades) if losing_trades else 0
        risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'largest_win': round(max(winning_trades), 2) if winning_trades else 0,
            'largest_loss': round(max(losing_trades), 2) if losing_trades else 0,
            'win_count': len(winning_trades),
            'loss_count': len(losing_trades)
        }
    
    def _identify_mistakes(self) -> List[Dict]:
        """Identify common mistakes"""
        mistakes = []
        
        # Check for large losses
        large_losses = []
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                pnl = self._calculate_trade_pnl(trade)
                if pnl < -100:  # Loss greater than $100
                    large_losses.append({
                        'symbol': trade.get('symbol'),
                        'loss': round(pnl, 2),
                        'date': trade.get('date')
                    })
        
        if large_losses:
            mistakes.append({
                'type': 'Large Losses',
                'severity': 'high',
                'message': f"You have {len(large_losses)} trades with losses over $100. Consider tighter stop-losses.",
                'count': len(large_losses)
            })
        
        # Check risk/reward ratio
        risk_analysis = self._analyze_risk()
        if risk_analysis['risk_reward_ratio'] < 1.5 and risk_analysis['risk_reward_ratio'] > 0:
            mistakes.append({
                'type': 'Poor Risk/Reward',
                'severity': 'medium',
                'message': f"Your average win (${risk_analysis['avg_win']}) is less than 1.5x your average loss (${risk_analysis['avg_loss']}). Aim for at least 2:1 ratio.",
                'ratio': risk_analysis['risk_reward_ratio']
            })
        
        # Check for overtrading
        if len(self.trades) > 50:
            recent_trades = [t for t in self.trades if self._parse_date(t.get('date')) > datetime.now() - timedelta(days=30)]
            if len(recent_trades) > 20:
                mistakes.append({
                    'type': 'Overtrading',
                    'severity': 'medium',
                    'message': f"You've made {len(recent_trades)} trades in the last 30 days. Quality over quantity - focus on high-probability setups.",
                    'count': len(recent_trades)
                })
        
        return mistakes
    
    def _performance_breakdown(self) -> Dict:
        """Break down performance by various metrics"""
        option_type_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})
        
        for trade in self.trades:
            if trade.get('action', '').upper() in ['SELL', 'CLOSE']:
                option_type = trade.get('option_type', 'STOCK')
                if not option_type:
                    option_type = 'STOCK'
                
                pnl = self._calculate_trade_pnl(trade)
                option_type_stats[option_type]['pnl'] += pnl
                if pnl > 0:
                    option_type_stats[option_type]['wins'] += 1
                else:
                    option_type_stats[option_type]['losses'] += 1
        
        breakdown = {}
        for opt_type, stats in option_type_stats.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                breakdown[opt_type] = {
                    'win_rate': round((stats['wins'] / total) * 100, 1),
                    'total_pnl': round(stats['pnl'], 2),
                    'total_trades': total
                }
        
        return breakdown
    
    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """Generate personalized recommendations based on insights"""
        recommendations = []
        
        # Best symbols recommendation
        if insights['best_symbols']:
            top_symbol = insights['best_symbols'][0]
            if top_symbol['win_rate'] > 60:
                recommendations.append(
                    f"🎯 Focus on {top_symbol['symbol']} - You have a {top_symbol['win_rate']}% win rate with ${top_symbol['total_pnl']} profit"
                )
        
        # Best days recommendation
        if insights['best_days']:
            best_day = insights['best_days'][0]
            if best_day['total_pnl'] > 0:
                recommendations.append(
                    f"📅 {best_day['day']} is your best trading day - {best_day['win_rate']}% win rate, ${best_day['total_pnl']} profit"
                )
        
        # Risk management recommendation
        risk = insights['risk_analysis']
        if risk['risk_reward_ratio'] < 1.5 and risk['risk_reward_ratio'] > 0:
            recommendations.append(
                f"⚠️ Improve risk/reward: Your wins average ${risk['avg_win']} but losses average ${risk['avg_loss']}. Target 2:1 minimum."
            )
        
        # Strategy recommendation
        if insights['best_strategies']:
            best_strategy = insights['best_strategies'][0]
            if best_strategy['strategy'] != 'No Strategy' and best_strategy['total_pnl'] > 0:
                recommendations.append(
                    f"💡 Your '{best_strategy['strategy']}' strategy works well - {best_strategy['win_rate']}% win rate"
                )
        
        # Time pattern recommendation
        time_patterns = insights['time_patterns']
        if time_patterns['best_hour'] is not None:
            recommendations.append(
                f"⏰ Best trading hour: {time_patterns['best_hour']}:00 - {time_patterns['best_hour_win_rate']}% win rate"
            )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _calculate_trade_pnl(self, trade: Dict) -> float:
        """Calculate PnL for a trade (same logic as TradeTracker)"""
        try:
            sold_amount = float(trade.get('sold_amount', 0))
            if sold_amount > 0:
                quantity = float(trade.get('quantity', 0))
                buy_price = float(trade.get('price', 0))
                total_cost = quantity * buy_price * 100
                pnl = sold_amount - total_cost - 2.00  # Transaction fee
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







