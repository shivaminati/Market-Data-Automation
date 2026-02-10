# 🚀 Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

### Linux/Mac:
```bash
# Run the setup script
bash setup.sh

# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows:
```cmd
# Run the setup script
setup.bat

# OR manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure

Edit the `.env` file (it's already created with defaults):

```env
# These are the only required settings:
API_PROVIDER=yfinance
SYMBOLS=AAPL,MSFT,GOOGL
ALERT_THRESHOLDS=AAPL:150:250,MSFT:300:500
```

## Step 3: Run

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Run the tool
cd src
python main.py
```

## Expected Output

You should see:
```
======================================================================
Market Data Automation Tool - Starting
======================================================================
API Provider: yfinance
Tracking Symbols: AAPL, MSFT, GOOGL
...
✅ Run completed successfully
```

## What Just Happened?

1. ✅ Fetched latest prices for AAPL, MSFT, GOOGL
2. ✅ Saved data to `data/market_data.db` (SQLite)
3. ✅ Exported to `data/market_data.csv`
4. ✅ Checked price alerts (none triggered if prices are normal)
5. ✅ Created logs in `logs/app.log`

## View Your Data

### Check the database:
```bash
sqlite3 data/market_data.db "SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 5;"
```

### Check the CSV:
```bash
cat data/market_data.csv
```

### Check the logs:
```bash
tail -f logs/app.log
```

## Schedule Automation

### Linux/Mac (Cron):
```bash
# Open crontab
crontab -e

# Add this line to run every hour:
0 * * * * cd /full/path/to/market-data-automation/src && /full/path/to/venv/bin/python main.py >> ../logs/cron.log 2>&1
```

### Windows (Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task → "Market Data Automation"
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\market-data-automation\src`

## Test Alerts

Edit `.env` to trigger an alert:

```env
# Set a threshold that will definitely trigger
# For example, if AAPL is ~$180, set:
ALERT_THRESHOLDS=AAPL:170:190
```

Run again:
```bash
python main.py
```

You should see:
```
🚨 PRICE ALERTS TRIGGERED 🚨
```

## Troubleshooting

**Problem:** "No module named 'requests'"
**Solution:** Activate virtual environment and reinstall:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Problem:** "No data fetched"
**Solution:** 
- Check internet connection
- Verify symbol names (use uppercase: AAPL not aapl)
- Check logs: `cat logs/app.log`

**Problem:** Can't connect to API
**Solution:** 
- Default yfinance should work without API key
- If using Alpha Vantage, verify API key is correct

## Next Steps

1. ✅ **Customize symbols** - Add your favorite stocks/crypto in `.env`
2. ✅ **Set alert thresholds** - Define price levels to monitor
3. ✅ **Schedule automation** - Set up cron or Task Scheduler
4. ✅ **Enable email alerts** - Configure SMTP settings in `.env`
5. ✅ **Explore data** - Query the SQLite database

## Common Commands

```bash
# Run the tool
cd src && python main.py

# Check logs
tail -f logs/app.log

# View database
sqlite3 data/market_data.db "SELECT * FROM market_data LIMIT 10;"

# Check CSV
head -20 data/market_data.csv

# Clean old data (optional)
sqlite3 data/market_data.db "DELETE FROM market_data WHERE datetime(timestamp) < datetime('now', '-30 days');"
```

## Full Documentation

See `README.md` for complete documentation.

---

**You're all set! 🎉**
