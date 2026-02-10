# 📈 Market Data Automation Tool

A production-ready Python automation tool for fetching, processing, storing, and monitoring stock and cryptocurrency market data with intelligent price alerts.

## 🎯 Features

- ✅ **Multi-Source Data Fetching**: Support for Yahoo Finance (yfinance) and Alpha Vantage APIs
- 🧹 **Data Transformation**: Automatic cleaning, validation, and standardization
- 💾 **Dual Storage**: SQLite database + CSV export for data persistence
- 🚨 **Smart Alerts**: Configurable price threshold monitoring with console and email notifications
- 🔄 **Automation Ready**: Designed for scheduled execution via cron or Windows Task Scheduler
- 📊 **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ⚡ **Retry Logic**: Built-in API call retry mechanism for reliability
- 🔒 **Production Quality**: Clean code, error handling, and modular architecture

## 📁 Project Structure

```
market-data-automation/
│
├── data/                      # Data storage directory
│   ├── market_data.db         # SQLite database (auto-created)
│   └── market_data.csv        # CSV export (auto-created)
│
├── logs/                      # Log files directory
│   └── app.log                # Application logs (auto-created)
│
├── src/                       # Source code
│   ├── fetch_data.py          # API data fetching with retry logic
│   ├── transform_data.py      # Data cleaning and transformation
│   ├── storage.py             # Database and CSV operations
│   ├── alerts.py              # Price monitoring and alerts
│   └── main.py                # Main orchestrator
│
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment configuration
├── .env                       # Your configuration (create from .env.example)
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for API calls

### 2. Installation

```bash
# Clone or download the repository
cd market-data-automation

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example configuration file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Minimal Configuration (.env):**

```env
# Use Yahoo Finance (no API key needed)
API_PROVIDER=yfinance
SYMBOLS=AAPL,MSFT,GOOGL

# Set price thresholds (format: SYMBOL:MIN:MAX)
ALERT_THRESHOLDS=AAPL:150:200,MSFT:300:450
```

### 4. Run the Tool

```bash
# Navigate to src directory
cd src

# Run the automation
python main.py
```

## 📖 Detailed Configuration

### API Providers

#### Yahoo Finance (Default - No API Key Required)

```env
API_PROVIDER=yfinance
SYMBOLS=AAPL,MSFT,TSLA,BTC-USD,ETH-USD
```

**Supports:**
- US stocks: AAPL, GOOGL, MSFT, TSLA, etc.
- Crypto: BTC-USD, ETH-USD, etc.
- International stocks: 0700.HK, NESN.SW, etc.

#### Alpha Vantage (Requires Free API Key)

1. Get free API key: https://www.alphavantage.co/support/#api-key
2. Configure:

```env
API_PROVIDER=alphavantage
API_KEY=your_api_key_here
SYMBOLS=AAPL,MSFT,IBM
```

**Note:** Alpha Vantage has rate limits (5 calls/minute for free tier)

### Alert Thresholds

Configure price thresholds in the format: `SYMBOL:MIN:MAX`

```env
# Alert if AAPL goes below $150 or above $200
# Alert if MSFT goes below $300 or above $450
# Alert if BTC-USD goes below $30,000 or above $100,000
ALERT_THRESHOLDS=AAPL:150:200,MSFT:300:450,BTC-USD:30000:100000
```

**Leave MIN or MAX empty if not needed:**
```env
# Only alert if AAPL goes above $200 (no minimum)
ALERT_THRESHOLDS=AAPL::200

# Only alert if MSFT goes below $300 (no maximum)
ALERT_THRESHOLDS=MSFT:300:
```

### Email Alerts (Optional)

```env
ENABLE_EMAIL_ALERTS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=recipient@example.com
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use app password in SMTP_PASSWORD

## 🔄 Automation & Scheduling

### Linux/Mac (Cron)

Edit crontab:
```bash
crontab -e
```

Add schedule (examples):

```bash
# Run every 15 minutes
*/15 * * * * cd /path/to/market-data-automation/src && /path/to/venv/bin/python main.py >> ../logs/cron.log 2>&1

# Run every hour at minute 0
0 * * * * cd /path/to/market-data-automation/src && /path/to/venv/bin/python main.py >> ../logs/cron.log 2>&1

# Run Monday-Friday at 9:30 AM (market open)
30 9 * * 1-5 cd /path/to/market-data-automation/src && /path/to/venv/bin/python main.py >> ../logs/cron.log 2>&1

# Run Monday-Friday at 4:00 PM (market close)
0 16 * * 1-5 cd /path/to/market-data-automation/src && /path/to/venv/bin/python main.py >> ../logs/cron.log 2>&1
```

**Verify cron jobs:**
```bash
crontab -l
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 9:30 AM)
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\market-data-automation\src`
5. Save and test

**PowerShell command to create task:**

```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\venv\Scripts\python.exe" -Argument "main.py" -WorkingDirectory "C:\path\to\market-data-automation\src"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:30AM
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Market Data Automation" -Description "Fetch and monitor market data"
```

## 📊 How It Works

### Workflow

```
1. Fetch Data
   ↓
2. Transform & Clean
   ↓
3. Store in Database & CSV
   ↓
4. Check Alert Thresholds
   ↓
5. Send Notifications (if triggered)
```

### Module Breakdown

#### `fetch_data.py` - Data Extraction
- Connects to Yahoo Finance or Alpha Vantage API
- Implements retry logic for failed requests
- Handles both stocks and cryptocurrencies
- Returns standardized quote data

#### `transform_data.py` - Data Transformation
- Cleans missing values
- Normalizes column names
- Converts timestamps to UTC ISO format
- Ensures numeric consistency
- Removes duplicates
- Validates data quality

#### `storage.py` - Data Persistence
- Creates and manages SQLite database
- Prevents duplicate records
- Exports to CSV format
- Provides query methods
- Generates statistics

#### `alerts.py` - Alert Management
- Monitors price thresholds
- Triggers console notifications
- Sends HTML email alerts (optional)
- Logs all alert events

#### `main.py` - Orchestration
- Coordinates all modules
- Manages execution flow
- Provides comprehensive logging
- Displays execution summary

## 📋 Sample Output

```
======================================================================
Market Data Automation Tool - Starting
======================================================================
API Provider: yfinance
Tracking Symbols: AAPL, MSFT, BTC-USD
Database: /path/to/data/market_data.db
Email Alerts: DISABLED

Configured Thresholds:
  AAPL: Min=$150.00, Max=$200.00
  MSFT: Min=$300.00, Max=$450.00
======================================================================

          🚀 Starting Data Collection Run           
      Timestamp: 2024-02-10T14:30:00.000000      

Step 1/5: Fetching market data...
✓ Fetched 3 quotes

Step 2/5: Transforming data...
✓ Cleaned 3 records

Step 3/5: Saving data...
✓ Saved 3 records to database and CSV

Step 4/5: Checking price alerts...
✓ No alerts triggered

Step 5/5: Generating summary...

======================================================================
📊 EXECUTION SUMMARY
======================================================================

💰 LATEST PRICES:
  AAPL: $185.50 (Volume: 52,345,678)
  MSFT: $425.75 (Volume: 28,456,123)
  BTC-USD: $45,678.90 (Volume: 0)

📁 DATABASE STATISTICS:
  Total Records: 156
  Unique Symbols: 3
  Records Saved This Run: 3
  Data Range: 2024-02-01T10:00:00 to 2024-02-10T14:30:00

✓ No price alerts triggered

======================================================================

✅ Run completed successfully in 3.45 seconds
```

### Alert Example

```
======================================================================
🚨 PRICE ALERTS TRIGGERED 🚨
======================================================================

🔴 ALERT: AAPL fell below $150.00! Current: $148.50
   Time: 2024-02-10T14:30:00.000000
   Threshold: $150.00
   Type: BELOW_MINIMUM

======================================================================
```

## 🧪 Testing

Run a test to verify setup:

```bash
cd src
python main.py
```

Check logs:
```bash
cat ../logs/app.log
```

Verify database:
```bash
sqlite3 ../data/market_data.db "SELECT * FROM market_data LIMIT 5;"
```

## 📝 Advanced Usage

### Query Database Directly

```python
from src.storage import DataStorage

storage = DataStorage()

# Get latest prices
latest = storage.get_latest_prices()
print(latest)

# Get historical data for a symbol
aapl_data = storage.load_from_database(symbol='AAPL', limit=100)

# Get statistics
stats = storage.get_statistics()
print(stats)
```

### Fetch Specific Symbols

```python
from src.fetch_data import fetch_market_data

# Fetch custom symbols
quotes = fetch_market_data(['TSLA', 'NVDA', 'AMD'])
```

### Manual Alert Check

```python
from src.alerts import check_and_alert

quotes = [
    {'symbol': 'AAPL', 'price': 145.0, 'volume': 1000000, 'timestamp': '...'}
]

alerts = check_and_alert(quotes)
```

## 🔧 Troubleshooting

### Common Issues

**1. No data fetched**
- Check internet connection
- Verify symbol names are correct
- Check API rate limits
- Review logs in `logs/app.log`

**2. Import errors**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

**3. Email alerts not working**
- Verify SMTP credentials
- For Gmail, use app password, not regular password
- Check firewall settings
- Test with `ENABLE_EMAIL_ALERTS=False` first

**4. Database locked**
- Only one process should write at a time
- Check for zombie processes
- Restart if needed

### Logs Location

- Application logs: `logs/app.log`
- Cron logs: `logs/cron.log` (if configured)

### Debug Mode

Enable debug logging in `.env`:

```env
LOG_LEVEL=DEBUG
```

## 🎁 Bonus Features

### Multi-Symbol Support ✅
Already implemented - add unlimited symbols to `SYMBOLS` config

### Retry Logic ✅
API calls automatically retry 3 times with 2-second delays

### Unit Tests (Template)

Create `tests/test_fetch.py`:

```python
import unittest
from src.fetch_data import MarketDataFetcher

class TestFetch(unittest.TestCase):
    def test_fetch_quote(self):
        fetcher = MarketDataFetcher('yfinance')
        quote = fetcher.fetch_quote('AAPL')
        
        self.assertIsNotNone(quote)
        self.assertEqual(quote['symbol'], 'AAPL')
        self.assertIsInstance(quote['price'], float)

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m unittest discover tests
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional API providers (IEX Cloud, Finnhub, etc.)
- More alert channels (Slack, Discord, SMS)
- Web dashboard for visualization
- Machine learning price predictions
- Technical indicators calculation

## 📄 License

This project is provided as-is for educational and personal use.

## 🙏 Acknowledgments

- **Yahoo Finance** - Free market data API
- **Alpha Vantage** - Comprehensive financial data API
- **yfinance** - Python library for Yahoo Finance

## 📞 Support

For issues or questions:
1. Check logs in `logs/app.log`
2. Review this README
3. Verify `.env` configuration
4. Test with minimal config first

---

**Happy Trading! 📈💰**

*Built with ❤️ for automated market data monitoring*
