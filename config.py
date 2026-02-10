"""
Configuration Module
Loads and validates environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Application configuration class"""
    
    # API Configuration
    API_KEY = os.getenv('API_KEY', '')
    API_PROVIDER = os.getenv('API_PROVIDER', 'yfinance')  # Default to yfinance (no API key needed)
    
    # Symbols to track
    SYMBOLS = [s.strip() for s in os.getenv('SYMBOLS', 'AAPL,MSFT,BTC-USD').split(',')]
    
    # Alert Thresholds
    ALERT_THRESHOLDS = {}
    thresholds_str = os.getenv('ALERT_THRESHOLDS', '')
    if thresholds_str:
        for threshold in thresholds_str.split(','):
            parts = threshold.strip().split(':')
            if len(parts) == 3:
                symbol = parts[0]
                min_val = float(parts[1]) if parts[1] else None
                max_val = float(parts[2]) if parts[2] else None
                ALERT_THRESHOLDS[symbol] = {'min': min_val, 'max': max_val}
    
    # Email Configuration
    ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'False').lower() == 'true'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', '')
    
    # Data Storage
    DATABASE_PATH = BASE_DIR / os.getenv('DATABASE_PATH', 'data/market_data.db')
    CSV_EXPORT_PATH = BASE_DIR / os.getenv('CSV_EXPORT_PATH', 'data/market_data.csv')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / os.getenv('LOG_FILE', 'logs/app.log')
    
    # API Rate Limiting
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 2  # seconds
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if cls.API_PROVIDER == 'alphavantage' and not cls.API_KEY:
            raise ValueError("API_KEY is required when using Alpha Vantage. Get one at https://www.alphavantage.co/support/#api-key")
        
        if not cls.SYMBOLS:
            raise ValueError("At least one symbol must be configured in SYMBOLS")
        
        if cls.ENABLE_EMAIL_ALERTS:
            if not all([cls.SMTP_USERNAME, cls.SMTP_PASSWORD, cls.ALERT_EMAIL_TO]):
                raise ValueError("Email alerts enabled but SMTP credentials are incomplete")
        
        # Ensure directories exist
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CSV_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        return True


# Validate configuration on import
try:
    Config.validate()
except Exception as e:
    print(f"⚠️  Configuration Warning: {e}")
    print("Please check your .env file configuration")
