# 🏗️ Architecture Documentation

## System Overview

The Market Data Automation Tool follows a modular, pipeline-based architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Orchestrator                        │
│                      (main.py)                               │
└────────┬──────────────────────────────────────┬─────────────┘
         │                                       │
         ▼                                       ▼
┌─────────────────┐                    ┌─────────────────────┐
│  Configuration  │                    │   Logging System    │
│   (config.py)   │                    │   (Python logging)  │
└─────────────────┘                    └─────────────────────┘
         │
         │ provides config to all modules
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Pipeline                            │
└─────────────────────────────────────────────────────────────┘
         │
         ├─► 1. FETCH (fetch_data.py)
         │   └─► API Clients (Yahoo Finance, Alpha Vantage)
         │       └─► Retry Logic
         │
         ├─► 2. TRANSFORM (transform_data.py)
         │   └─► Data Cleaning
         │   └─► Validation
         │   └─► Deduplication
         │
         ├─► 3. STORE (storage.py)
         │   ├─► SQLite Database
         │   └─► CSV Export
         │
         └─► 4. ALERT (alerts.py)
             ├─► Threshold Checking
             ├─► Console Notifications
             └─► Email Notifications (optional)
```

## Module Architecture

### 1. Configuration Layer (`config.py`)

**Purpose:** Centralized configuration management

**Design Pattern:** Singleton-like class with class methods

**Responsibilities:**
- Load environment variables from `.env`
- Parse and validate configuration
- Provide configuration to all modules
- Ensure required directories exist

**Key Features:**
- Validation on import
- Type conversion (strings → numbers, lists)
- Default values for optional settings
- Directory creation

```python
Config
├── API Configuration
│   ├── API_KEY
│   ├── API_PROVIDER
│   └── API_RETRY_ATTEMPTS
├── Symbols & Thresholds
│   ├── SYMBOLS (list)
│   └── ALERT_THRESHOLDS (dict)
├── Storage Paths
│   ├── DATABASE_PATH
│   └── CSV_EXPORT_PATH
└── Email Settings
    ├── ENABLE_EMAIL_ALERTS
    └── SMTP_* credentials
```

### 2. Data Fetching Layer (`fetch_data.py`)

**Purpose:** Retrieve market data from external APIs

**Design Pattern:** Strategy pattern (multiple API providers)

**Class Structure:**
```python
MarketDataFetcher
├── __init__(provider)
├── fetch_quote(symbol) → Dict
│   ├── Retry logic (3 attempts)
│   └── Provider-specific methods:
│       ├── _fetch_yfinance()
│       └── _fetch_alphavantage()
└── fetch_multiple(symbols) → List[Dict]
    └── Rate limiting (0.5s between calls)
```

**Data Flow:**
```
User Request
    ↓
MarketDataFetcher.fetch_quote("AAPL")
    ↓
Retry Loop (max 3 attempts)
    ↓
Provider-Specific Fetch
    ├── yfinance: ticker.info
    └── alphavantage: API call
    ↓
Standardized Output: {symbol, price, volume, timestamp, provider}
```

**Error Handling:**
- Network errors → Retry with exponential backoff
- Invalid symbols → Return None, log warning
- API errors → Return None, log error
- Rate limit exceeded → Sleep and retry

### 3. Data Transformation Layer (`transform_data.py`)

**Purpose:** Clean, validate, and standardize data

**Design Pattern:** Pipeline pattern

**Class Structure:**
```python
DataTransformer (Static Methods)
├── clean_and_standardize(raw_data) → DataFrame
│   ├── Column normalization
│   ├── Missing value handling
│   ├── Type conversion
│   ├── Timestamp normalization
│   └── Validation
├── remove_duplicates(df, existing_df) → DataFrame
└── get_summary_statistics(df) → Dict
```

**Transformation Pipeline:**
```
Raw Data List[Dict]
    ↓
1. Convert to DataFrame
    ↓
2. Standardize column names (lowercase)
    ↓
3. Handle missing values
   ├── Drop rows with NULL price
   └── Fill volume=0 if missing
    ↓
4. Type conversion
   ├── price → float64
   └── volume → int64
    ↓
5. Timestamp normalization
   └── All timestamps → UTC ISO format
    ↓
6. Add metadata
   └── processed_at timestamp
    ↓
7. Validation
   ├── Remove invalid prices (≤0)
   └── Remove duplicates
    ↓
Clean DataFrame
```

**Data Quality Checks:**
- ✅ Required fields present (symbol, price, timestamp)
- ✅ Numeric consistency (price > 0, volume ≥ 0)
- ✅ No duplicates (symbol + timestamp unique)
- ✅ Timestamps in UTC
- ✅ Type correctness

### 4. Storage Layer (`storage.py`)

**Purpose:** Persist data in SQLite and CSV formats

**Design Pattern:** Repository pattern

**Database Schema:**
```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    volume INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    provider TEXT,
    processed_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)  -- Prevent duplicates
);

-- Indexes for performance
CREATE INDEX idx_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX idx_timestamp ON market_data(timestamp);
```

**Class Structure:**
```python
DataStorage
├── __init__(db_path, csv_path)
│   └── _initialize_database()
├── save_to_database(df) → int
│   └── _save_with_ignore_duplicates()
├── load_from_database(symbol, limit) → DataFrame
├── get_latest_prices() → DataFrame
├── export_to_csv(df, append)
├── get_statistics() → dict
└── cleanup_old_data(days) → int
```

**Storage Operations:**
```
DataFrame
    ↓
save_to_database()
    ├─► Try bulk insert
    │   └─► If duplicates detected → Individual inserts
    ↓
SQLite Database
    ├─► UNIQUE constraint prevents duplicates
    └─► Indexes ensure fast queries
    ↓
export_to_csv()
    └─► CSV file (append mode)
```

**Query Patterns:**
- Get latest prices: `GROUP BY symbol, MAX(timestamp)`
- Historical data: `WHERE symbol = ? ORDER BY timestamp DESC`
- Statistics: Aggregations on symbol groups

### 5. Alert Layer (`alerts.py`)

**Purpose:** Monitor thresholds and send notifications

**Design Pattern:** Observer pattern

**Class Structure:**
```python
AlertManager
├── __init__()
│   └── Load thresholds from Config
├── check_thresholds(quote_data) → List[Alert]
│   ├── Check min threshold
│   └── Check max threshold
├── check_multiple(quotes) → List[Alert]
├── send_alerts(alerts)
│   ├── _send_console_alerts()
│   └── _send_email_alerts()
│       ├── _create_text_email_body()
│       └── _create_html_email_body()
└── get_threshold_summary() → str
```

**Alert Decision Tree:**
```
Quote Data
    ↓
Symbol has thresholds?
    ├─► No → Return []
    └─► Yes
        ↓
    Price < min_threshold?
        ├─► Yes → Create BELOW_MINIMUM alert
        └─► No → Continue
        ↓
    Price > max_threshold?
        ├─► Yes → Create ABOVE_MAXIMUM alert
        └─► No → Continue
        ↓
    Return alerts[]
        ↓
    If alerts exist:
        ├─► Console output (always)
        └─► Email (if enabled)
```

**Alert Data Structure:**
```python
{
    'symbol': 'AAPL',
    'current_price': 145.0,
    'threshold_type': 'BELOW_MINIMUM',
    'threshold_value': 150.0,
    'message': '🔴 ALERT: AAPL fell below $150.00! Current: $145.00',
    'timestamp': '2024-02-10T10:00:00',
    'severity': 'HIGH'
}
```

### 6. Orchestration Layer (`main.py`)

**Purpose:** Coordinate all modules into a complete workflow

**Design Pattern:** Facade pattern

**Class Structure:**
```python
MarketDataAutomation
├── __init__()
│   ├── Initialize storage
│   ├── Initialize alert manager
│   └── Display configuration
├── run() → bool
│   ├── Step 1: Fetch data
│   ├── Step 2: Transform data
│   ├── Step 3: Save data
│   ├── Step 4: Check alerts
│   └── Step 5: Display summary
├── _display_configuration()
├── _display_summary()
└── display_historical_data()
```

**Execution Flow:**
```
main()
    ↓
Config.validate()
    ↓
MarketDataAutomation()
    ↓
automation.run()
    ↓
┌─────────────────────────┐
│  Step 1: Fetch Data     │
│  fetch_market_data()    │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Step 2: Transform      │
│  transform_market_data()│
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Step 3: Save           │
│  save_data()            │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Step 4: Check Alerts   │
│  check_and_alert()      │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Step 5: Summary        │
│  _display_summary()     │
└─────────────────────────┘
```

## Data Models

### Quote Data Model
```python
{
    'symbol': str,          # Stock/crypto symbol
    'price': float,         # Current price
    'volume': int,          # Trading volume
    'timestamp': str,       # ISO format UTC timestamp
    'provider': str,        # Data source
    'processed_at': str     # Processing timestamp (added in transform)
}
```

### Alert Data Model
```python
{
    'symbol': str,
    'current_price': float,
    'threshold_type': str,  # 'BELOW_MINIMUM' or 'ABOVE_MAXIMUM'
    'threshold_value': float,
    'message': str,
    'timestamp': str,
    'severity': str         # 'HIGH', 'MEDIUM', 'LOW'
}
```

## Design Principles

### 1. Separation of Concerns
- Each module has a single, well-defined responsibility
- Clear interfaces between modules
- No cross-module dependencies (except config)

### 2. Dependency Injection
- Configuration injected via Config class
- Storage and alert managers can be instantiated independently
- Easy to mock for testing

### 3. Error Handling
- Graceful degradation (continue on single symbol failure)
- Comprehensive logging at all levels
- User-friendly error messages
- No silent failures

### 4. Extensibility
- Easy to add new API providers
- Easy to add new alert channels (Slack, Discord, etc.)
- Easy to add new storage backends
- Plugin-like architecture

### 5. Reliability
- Retry logic for network calls
- Database transactions
- Duplicate prevention
- Data validation

## Performance Considerations

### Database
- **Indexes** on frequently queried columns
- **UNIQUE constraint** prevents duplicate inserts
- **Batch inserts** when possible
- **Connection pooling** via context managers

### API Calls
- **Rate limiting** (0.5s between calls)
- **Retry with backoff** (2s delay)
- **Timeout** on HTTP requests (10s)
- **Concurrent calls** can be added via asyncio

### Memory
- **Streaming data** where possible
- **DataFrame operations** optimized
- **Logging rotation** to prevent log bloat
- **Database cleanup** function for old data

## Security Considerations

### Credentials
- ✅ Environment variables for secrets
- ✅ `.env` file not committed to git
- ✅ `.env.example` for documentation
- ❌ No hardcoded credentials

### Data
- ✅ Local storage (no cloud by default)
- ✅ No PII collected
- ✅ Email sent via TLS
- ✅ Database in user-controlled location

### Code
- ✅ Input validation on all user inputs
- ✅ SQL injection prevention (parameterized queries)
- ✅ Exception handling prevents crashes
- ✅ Logging doesn't expose secrets

## Testing Strategy

### Unit Tests
- DataTransformer logic
- Alert threshold logic
- Configuration parsing
- Data validation

### Integration Tests
- Full pipeline execution
- Database operations
- API calls (with mocking)

### Manual Testing
- Run with different configurations
- Verify outputs (DB, CSV, logs)
- Test alert triggers
- Test error scenarios

## Deployment Patterns

### Development
```
.env → Use yfinance (no API key)
LOG_LEVEL → DEBUG
Email → Disabled
```

### Production
```
.env → Use Alpha Vantage (with API key)
LOG_LEVEL → INFO
Email → Enabled
Cron → Scheduled execution
```

### Monitoring
```
Logs → logs/app.log
Cron logs → logs/cron.log
Database size → Monitor growth
Alert frequency → Track in logs
```

## Future Enhancements

### Potential Additions
1. **Web Dashboard** - Visualize data with Flask/Dash
2. **Machine Learning** - Price predictions
3. **Technical Indicators** - RSI, MACD, etc.
4. **Backtesting** - Test strategies on historical data
5. **Multi-asset** - Support for forex, commodities
6. **Cloud Storage** - S3, Google Cloud Storage
7. **API Server** - RESTful API for data access
8. **Mobile App** - React Native companion app
9. **Slack Integration** - Alerts in Slack channels
10. **Real-time Streaming** - WebSocket for live data

---

**This architecture is designed to be:**
- 📦 Modular
- 🔒 Secure
- ⚡ Performant
- 🧪 Testable
- 📈 Scalable
