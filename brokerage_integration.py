"""
Brokerage Integration Module for Automatic Trade Recording
Supports Canadian brokerages: Questrade, Wealthica, SnapTrade, Webull

Note on Wealthsimple:
- Wealthsimple doesn't have a direct public API
- BUT it's supported through:
  * SnapTrade (connects to Wealthsimple accounts)
  * Wealthica (connects to Wealthsimple accounts)
- Users can connect Wealthsimple via these third-party services
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

class BrokerageAdapter(ABC):
    """Base class for brokerage integrations"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with brokerage API"""
        pass
    
    @abstractmethod
    def fetch_trades(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch trades from brokerage"""
        pass
    
    @abstractmethod
    def normalize_trade(self, raw_trade: Dict) -> Dict:
        """Convert brokerage-specific trade format to standard format"""
        pass


class QuestradeAdapter(BrokerageAdapter):
    """Questrade API Integration"""
    
    def __init__(self):
        self.api_base = "https://api01.iq.questrade.com"
        self.access_token = None
        self.refresh_token = None
        self.api_server = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with Questrade API
        Requires: refresh_token (from Questrade developer portal)
        """
        try:
            refresh_token = credentials.get('refresh_token')
            if not refresh_token:
                return False
            
            # Get access token
            response = requests.get(
                f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={refresh_token}"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
                self.api_server = data['api_server']
                return True
            return False
        except Exception as e:
            print(f"Questrade authentication error: {e}")
            return False
    
    def fetch_trades(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch trades from Questrade"""
        if not self.access_token or not self.api_server:
            return []
        
        try:
            # Get accounts
            accounts_response = requests.get(
                f"{self.api_server}/v1/accounts",
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            
            if accounts_response.status_code != 200:
                return []
            
            accounts = accounts_response.json().get('accounts', [])
            all_trades = []
            
            # Fetch trades from each account
            for account in accounts:
                account_number = account['number']
                
                # Build query params
                params = {}
                if start_date:
                    params['startTime'] = start_date.isoformat()
                if end_date:
                    params['endTime'] = end_date.isoformat()
                
                trades_response = requests.get(
                    f"{self.api_server}/v1/accounts/{account_number}/executions",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    params=params
                )
                
                if trades_response.status_code == 200:
                    executions = trades_response.json().get('executions', [])
                    for execution in executions:
                        normalized = self.normalize_trade(execution)
                        if normalized:
                            all_trades.append(normalized)
            
            return all_trades
        except Exception as e:
            print(f"Error fetching Questrade trades: {e}")
            return []
    
    def normalize_trade(self, raw_trade: Dict) -> Dict:
        """Convert Questrade execution to standard trade format"""
        try:
            # Questrade execution format
            symbol = raw_trade.get('symbol', '')
            quantity = raw_trade.get('quantity', 0)
            price = raw_trade.get('price', 0)
            side = raw_trade.get('side', '').upper()
            execution_time = raw_trade.get('executionTime', '')
            
            # Determine action
            action = 'BUY' if side == 'Buy' else 'SELL'
            
            # Parse symbol to detect options
            trade_type = 'STOCK'
            option_type = None
            strike = None
            expiration = None
            
            # Questrade options format: SYMBOL YYMMDD C/P STRIKE
            # Example: AAPL 241220 C 150
            if ' ' in symbol and len(symbol.split()) >= 4:
                parts = symbol.split()
                if len(parts) == 4:
                    base_symbol = parts[0]
                    exp_date = parts[1]  # YYMMDD
                    opt_type = parts[2]  # C or P
                    strike_price = float(parts[3])
                    
                    trade_type = 'OPTION'
                    option_type = 'CALL' if opt_type.upper() == 'C' else 'PUT'
                    strike = strike_price
                    # Convert YYMMDD to expiration date
                    year = 2000 + int(exp_date[:2])
                    month = int(exp_date[2:4])
                    day = int(exp_date[4:6])
                    expiration = f"{year}-{month:02d}-{day:02d}"
                    symbol = base_symbol
            
            return {
                'symbol': symbol,
                'action': action,
                'quantity': abs(quantity),
                'price': price,
                'date': execution_time,
                'trade_type': trade_type,
                'option_type': option_type,
                'strike': strike,
                'expiration': expiration,
                'transaction_fee': raw_trade.get('commission', 0),
                'brokerage': 'Questrade',
                'brokerage_trade_id': raw_trade.get('executionId', '')
            }
        except Exception as e:
            print(f"Error normalizing Questrade trade: {e}")
            return None


class WealthicaAdapter(BrokerageAdapter):
    """Wealthica API Integration - Connects to 150+ Canadian institutions"""
    
    def __init__(self):
        self.api_base = "https://api.wealthica.com"
        self.access_token = None
        self.api_key = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with Wealthica API
        Requires: api_key and api_secret (from Wealthica developer portal)
        """
        try:
            self.api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            
            if not self.api_key or not api_secret:
                return False
            
            # Wealthica uses OAuth2 - would need full OAuth flow
            # For now, storing API key for future implementation
            return True
        except Exception as e:
            print(f"Wealthica authentication error: {e}")
            return False
    
    def fetch_trades(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch trades from Wealthica-connected accounts"""
        # Implementation would use Wealthica API
        # This requires OAuth flow and account connection
        return []
    
    def normalize_trade(self, raw_trade: Dict) -> Dict:
        """Convert Wealthica transaction to standard format"""
        # Implementation depends on Wealthica API response format
        return {}


class SnapTradeAdapter(BrokerageAdapter):
    """SnapTrade API Integration - Universal brokerage connector"""
    
    def __init__(self):
        self.api_base = "https://api.snaptrade.com/api/v1"
        self.client_id = None
        self.client_secret = None
        self.access_token = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with SnapTrade API
        Requires: client_id and client_secret (from SnapTrade developer portal)
        """
        try:
            self.client_id = credentials.get('client_id')
            self.client_secret = credentials.get('client_secret')
            
            if not self.client_id or not self.client_secret:
                return False
            
            # Get access token
            response = requests.post(
                f"{self.api_base}/auth/token",
                auth=(self.client_id, self.client_secret),
                json={'grant_type': 'client_credentials'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                return True
            return False
        except Exception as e:
            print(f"SnapTrade authentication error: {e}")
            return False
    
    def fetch_trades(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch trades from SnapTrade-connected account"""
        if not self.access_token:
            return []
        
        try:
            # Get transactions for user
            response = requests.get(
                f"{self.api_base}/transactions",
                headers={'Authorization': f'Bearer {self.access_token}'},
                params={'userId': user_id}
            )
            
            if response.status_code == 200:
                transactions = response.json().get('transactions', [])
                return [self.normalize_trade(t) for t in transactions if self.normalize_trade(t)]
            return []
        except Exception as e:
            print(f"Error fetching SnapTrade trades: {e}")
            return []
    
    def normalize_trade(self, raw_trade: Dict) -> Dict:
        """Convert SnapTrade transaction to standard format"""
        try:
            return {
                'symbol': raw_trade.get('symbol', ''),
                'action': raw_trade.get('transactionType', '').upper(),
                'quantity': abs(float(raw_trade.get('quantity', 0))),
                'price': float(raw_trade.get('price', 0)),
                'date': raw_trade.get('date', ''),
                'trade_type': 'OPTION' if raw_trade.get('optionType') else 'STOCK',
                'option_type': raw_trade.get('optionType', '').upper(),
                'strike': raw_trade.get('strikePrice'),
                'expiration': raw_trade.get('expirationDate'),
                'transaction_fee': raw_trade.get('commission', 0),
                'brokerage': 'SnapTrade',
                'brokerage_trade_id': raw_trade.get('id', '')
            }
        except Exception as e:
            print(f"Error normalizing SnapTrade trade: {e}")
            return None


class WebullAdapter(BrokerageAdapter):
    """Webull API Integration"""
    
    def __init__(self):
        self.api_base = "https://api.webull.com/api"
        self.access_token = None
        self.refresh_token = None
        self.account_id = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with Webull API
        Requires: api_key, api_secret, account_id
        Note: Webull API requires account with $5,000+ and application approval
        """
        try:
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            self.account_id = credentials.get('account_id')
            
            if not api_key or not api_secret or not self.account_id:
                return False
            
            # Webull uses OAuth2 - get access token
            # This is a simplified version - actual implementation would need full OAuth flow
            response = requests.post(
                f"{self.api_base}/passport/login/v3/account",
                json={
                    'account': api_key,
                    'pwd': api_secret,
                    'regionId': 6  # Canada region
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')
                self.refresh_token = data.get('refreshToken')
                return True
            return False
        except Exception as e:
            print(f"Webull authentication error: {e}")
            return False
    
    def fetch_trades(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch trades from Webull"""
        if not self.access_token or not self.account_id:
            return []
        
        try:
            # Get account orders/executions
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'ticker': 'webull'
            }
            
            params = {
                'secAccountId': self.account_id,
                'startTime': int(start_date.timestamp() * 1000) if start_date else None,
                'endTime': int(end_date.timestamp() * 1000) if end_date else None
            }
            
            response = requests.get(
                f"{self.api_base}/v2/option/list",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                orders = response.json().get('data', [])
                all_trades = []
                
                for order in orders:
                    # Webull returns orders, need to get executions
                    executions = self._get_order_executions(order.get('orderId'))
                    for execution in executions:
                        normalized = self.normalize_trade(execution)
                        if normalized:
                            all_trades.append(normalized)
                
                return all_trades
            return []
        except Exception as e:
            print(f"Error fetching Webull trades: {e}")
            return []
    
    def _get_order_executions(self, order_id: str) -> List[Dict]:
        """Get executions for a specific order"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'ticker': 'webull'
            }
            
            response = requests.get(
                f"{self.api_base}/v2/option/execution/list",
                headers=headers,
                params={'orderId': order_id}
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            print(f"Error fetching Webull executions: {e}")
            return []
    
    def normalize_trade(self, raw_trade: Dict) -> Dict:
        """Convert Webull execution to standard trade format"""
        try:
            symbol = raw_trade.get('symbol', '')
            quantity = raw_trade.get('filledQuantity', 0)
            price = raw_trade.get('avgFilledPrice', 0)
            side = raw_trade.get('side', '').upper()
            execution_time = raw_trade.get('createTime', '')
            
            # Determine action
            action = 'BUY' if side == 'BUY' else 'SELL'
            
            # Parse symbol to detect options
            trade_type = 'STOCK'
            option_type = None
            strike = None
            expiration = None
            
            # Webull options format: SYMBOL YYMMDD C/P STRIKE
            # Example: AAPL 241220C150
            if len(symbol) > 6 and symbol[-1] in ['C', 'P']:
                # Try to parse option symbol
                base_symbol = symbol.split()[0] if ' ' in symbol else symbol[:-15]
                # Webull option format is complex, would need specific parsing
                trade_type = 'OPTION'
                # Would need to extract strike and expiration from symbol
            
            return {
                'symbol': symbol.split()[0] if ' ' in symbol else symbol,
                'action': action,
                'quantity': abs(quantity),
                'price': price,
                'date': execution_time,
                'trade_type': trade_type,
                'option_type': option_type,
                'strike': strike,
                'expiration': expiration,
                'transaction_fee': raw_trade.get('commission', 0),
                'brokerage': 'Webull',
                'brokerage_trade_id': raw_trade.get('execId', '')
            }
        except Exception as e:
            print(f"Error normalizing Webull trade: {e}")
            return None


class BrokerageManager:
    """Manages multiple brokerage connections"""
    
    def __init__(self):
        self.connections_file = 'brokerage_connections.json'
        self.connections = self.load_connections()
    
    def load_connections(self) -> Dict:
        """Load saved brokerage connections"""
        if os.path.exists(self.connections_file):
            try:
                with open(self.connections_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading connections: {e}")
        return {}
    
    def save_connections(self):
        """Save brokerage connections"""
        with open(self.connections_file, 'w') as f:
            json.dump(self.connections, f, indent=2)
    
    def add_connection(self, user_id: str, brokerage_type: str, credentials: Dict) -> bool:
        """Add a brokerage connection for a user"""
        if user_id not in self.connections:
            self.connections[user_id] = []
        
        # Create adapter and test connection
        adapter = self._create_adapter(brokerage_type)
        if adapter and adapter.authenticate(credentials):
            connection = {
                'id': f"{brokerage_type}_{datetime.now().timestamp()}",
                'type': brokerage_type,
                'credentials': credentials,
                'connected_at': datetime.now().isoformat(),
                'last_sync': None,
                'enabled': True
            }
            self.connections[user_id].append(connection)
            self.save_connections()
            return True
        return False
    
    def _create_adapter(self, brokerage_type: str) -> Optional[BrokerageAdapter]:
        """Create appropriate adapter based on brokerage type"""
        if brokerage_type == 'questrade':
            return QuestradeAdapter()
        elif brokerage_type == 'wealthica':
            return WealthicaAdapter()
        elif brokerage_type == 'snaptrade':
            return SnapTradeAdapter()
        elif brokerage_type == 'webull':
            return WebullAdapter()
        return None
    
    def sync_trades(self, user_id: str) -> List[Dict]:
        """Sync trades from all connected brokerages for a user"""
        if user_id not in self.connections:
            return []
        
        all_trades = []
        for connection in self.connections[user_id]:
            if not connection.get('enabled', True):
                continue
            
            adapter = self._create_adapter(connection['type'])
            if adapter and adapter.authenticate(connection['credentials']):
                # Fetch trades since last sync
                last_sync = connection.get('last_sync')
                start_date = datetime.fromisoformat(last_sync) if last_sync else None
                
                trades = adapter.fetch_trades(start_date=start_date)
                all_trades.extend(trades)
                
                # Update last sync time
                connection['last_sync'] = datetime.now().isoformat()
        
        self.save_connections()
        return all_trades

