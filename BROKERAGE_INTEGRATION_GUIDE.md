# Brokerage Integration Guide

## Overview

This guide explains how to implement automatic trade recording from Canadian brokerages. The system supports multiple integration methods:

1. **Questrade API** - Direct integration with Questrade (most popular Canadian discount broker)
2. **Wealthica API** - Aggregator connecting to 150+ Canadian financial institutions
3. **SnapTrade API** - Universal connector for major retail brokerages globally
4. **Webull API** - Direct integration with Webull (requires $5,000+ account and API approval)

## Supported Brokerages

### Direct API Support:
- ✅ **Questrade** - Free API, most popular Canadian broker
- ✅ **Webull** - Requires $5,000+ account and API application

### Via Third-Party Services:

**Through SnapTrade:**
- ✅ **Wealthsimple** - No direct API, but available via SnapTrade
- ✅ **TD Direct Investing**
- ✅ **RBC Direct Investing**
- ✅ **BMO InvestorLine**
- ✅ **CIBC Investor's Edge**
- ✅ **Scotia iTrade**
- ✅ And 100+ other brokerages globally

**Through Wealthica:**
- ✅ **Wealthsimple** - Also available via Wealthica
- ✅ **TD Direct Investing**
- ✅ **RBC Direct Investing**
- ✅ **BMO InvestorLine**
- ✅ **CIBC Investor's Edge**
- ✅ **Scotia iTrade**
- ✅ **Questrade** (also has direct API)
- ✅ And 150+ Canadian financial institutions

## Implementation Strategy

### Phase 1: Questrade Integration (Recommended First)

**Why Questrade?**
- Most popular Canadian discount broker
- Free REST API (no API fees)
- Good documentation
- Supports both stocks and options

**Setup Steps:**

1. **Get Questrade API Credentials:**
   - Register at: https://www.questrade.com/api/home
   - Create a developer account
   - Get your `refresh_token` from the developer portal

2. **OAuth Flow:**
   - User clicks "Connect Questrade" in settings
   - Redirect to Questrade OAuth page
   - User authorizes access
   - Receive `refresh_token`
   - Store securely (encrypted in database)

3. **Automatic Sync:**
   - Background job runs every hour
   - Fetches new trades since last sync
   - Normalizes to standard trade format
   - Adds to trade history

### Phase 2: Wealthica Integration (For Multiple Banks)

**Why Wealthica?**
- Connects to 150+ Canadian institutions:
  - TD Direct Investing
  - RBC Direct Investing
  - BMO InvestorLine
  - CIBC Investor's Edge
  - Scotia iTrade
  - And many more...

**Setup Steps:**

1. **Get Wealthica API Credentials:**
   - Register at: https://wealthica.com/investment-api/
   - Get `api_key` and `api_secret`

2. **OAuth Flow:**
   - User selects their bank/brokerage
   - Redirect to Wealthica OAuth
   - User connects their account
   - Store connection token

3. **Sync Process:**
   - Wealthica handles the bank connection
   - Your app fetches transactions via Wealthica API
   - Normalize and import trades

### Phase 3: SnapTrade Integration (Universal)

**Why SnapTrade?**
- Works with major brokerages globally
- Handles OAuth for you
- Good for international users too

**Setup Steps:**

1. **Get SnapTrade Credentials:**
   - Register at: https://snaptrade.com/
   - Get `client_id` and `client_secret`

2. **User Connection:**
   - User selects their brokerage
   - SnapTrade handles OAuth flow
   - Returns connection token

3. **Sync:**
   - Fetch transactions via SnapTrade API
   - Normalize and import

## Security Considerations

### 1. Credential Storage
- **Never store credentials in plain text**
- Use encryption (AES-256) for stored tokens
- Store in secure database, not JSON files
- Use environment variables for API keys

### 2. OAuth Best Practices
- Use HTTPS only
- Implement token refresh automatically
- Store refresh tokens securely
- Implement token expiration handling

### 3. User Privacy
- Clear consent flow
- Show what data is accessed
- Allow users to disconnect
- Comply with Canadian privacy laws (PIPEDA)

## Database Schema

```sql
-- Brokerage connections table
CREATE TABLE brokerage_connections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    brokerage_type VARCHAR(50) NOT NULL, -- 'questrade', 'wealthica', 'snaptrade'
    encrypted_credentials TEXT NOT NULL, -- Encrypted JSON
    connected_at TIMESTAMP NOT NULL,
    last_sync TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sync history table
CREATE TABLE sync_history (
    id UUID PRIMARY KEY,
    connection_id UUID NOT NULL,
    sync_started_at TIMESTAMP NOT NULL,
    sync_completed_at TIMESTAMP,
    trades_found INT DEFAULT 0,
    trades_imported INT DEFAULT 0,
    status VARCHAR(20), -- 'success', 'failed', 'partial'
    error_message TEXT,
    FOREIGN KEY (connection_id) REFERENCES brokerage_connections(id)
);
```

## API Endpoints to Add

```python
# Connect brokerage
POST /api/brokerage/connect
{
    "brokerage_type": "questrade",
    "credentials": {...}
}

# List connections
GET /api/brokerage/connections

# Sync trades manually
POST /api/brokerage/sync/{connection_id}

# Disconnect
DELETE /api/brokerage/connections/{connection_id}

# Get sync status
GET /api/brokerage/sync/status
```

## Background Job (Celery/APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler

def sync_all_brokerages():
    """Run every hour to sync all enabled connections"""
    manager = BrokerageManager()
    for user_id, connections in manager.connections.items():
        trades = manager.sync_trades(user_id)
        # Import trades into TradeTracker
        for trade in trades:
            tracker.add_trade(trade)

scheduler = BackgroundScheduler()
scheduler.add_job(sync_all_brokerages, 'interval', hours=1)
scheduler.start()
```

## UI Components Needed

1. **Settings > Brokerage Connections**
   - List of connected brokerages
   - "Connect New" button
   - Status indicators (connected, syncing, error)
   - Last sync time
   - Enable/disable toggle

2. **Connection Modal**
   - Select brokerage type
   - OAuth redirect button
   - Instructions for each brokerage
   - Status feedback

3. **Sync Status**
   - Show in header or sidebar
   - "Last synced: 2 hours ago"
   - Manual sync button
   - Sync progress indicator

## Cost Considerations

- **Questrade API**: Free (no API fees, only trading commissions)
- **Wealthica API**: Free tier available, paid plans for higher volume
- **SnapTrade API**: Free tier available, paid for production

## Next Steps

1. **Start with Questrade** (easiest, most popular)
2. **Add database** (PostgreSQL recommended)
3. **Implement OAuth flow** in frontend
4. **Add background sync job**
5. **Test with real accounts**
6. **Add Wealthica** for bank connections
7. **Add SnapTrade** for broader coverage

## Testing

- Use Questrade sandbox/test environment
- Test with small accounts first
- Verify trade normalization
- Test error handling (expired tokens, API failures)
- Test duplicate detection (don't import same trade twice)

## Support

For each brokerage:
- Questrade: https://www.questrade.com/api/documentation
- Wealthica: https://docs.wealthica.com/
- SnapTrade: https://docs.snaptrade.com/

