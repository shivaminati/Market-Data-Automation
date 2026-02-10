"""
Data Fetching Module
Handles API calls to fetch market data from various providers
"""

import logging
import time
import requests
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional
from config import Config

# Configure logging
logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetches market data from public APIs
    Supports: Alpha Vantage and Yahoo Finance
    """
    
    def __init__(self, provider: str = None):
        """
        Initialize the data fetcher
        
        Args:
            provider: API provider ('alphavantage' or 'yfinance')
        """
        self.provider = provider or Config.API_PROVIDER
        self.api_key = Config.API_KEY
        self.retry_attempts = Config.API_RETRY_ATTEMPTS
        self.retry_delay = Config.API_RETRY_DELAY
        
        logger.info(f"Initialized MarketDataFetcher with provider: {self.provider}")
    
    def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current quote for a symbol
        
        Args:
            symbol: Stock/crypto symbol (e.g., 'AAPL', 'BTC-USD')
        
        Returns:
            Dictionary containing quote data or None if failed
        """
        logger.info(f"Fetching quote for {symbol}")
        
        for attempt in range(self.retry_attempts):
            try:
                if self.provider == 'alphavantage':
                    return self._fetch_alphavantage(symbol)
                else:  # yfinance (default)
                    return self._fetch_yfinance(symbol)
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{self.retry_attempts}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to fetch {symbol} after {self.retry_attempts} attempts")
                    return None
            
            except Exception as e:
                logger.error(f"Unexpected error fetching {symbol}: {e}")
                return None
        
        return None
    
    def _fetch_yfinance(self, symbol: str) -> Dict:
        """
        Fetch data using Yahoo Finance (yfinance)
        
        Args:
            symbol: Stock/crypto symbol
        
        Returns:
            Dictionary with quote data
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price - try multiple fields as yfinance structure can vary
            current_price = (
                info.get('currentPrice') or 
                info.get('regularMarketPrice') or 
                info.get('price') or
                info.get('previousClose')
            )
            
            if current_price is None:
                # Try getting it from history
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Get volume
            volume = (
                info.get('volume') or 
                info.get('regularMarketVolume') or 
                0
            )
            
            quote_data = {
                'symbol': symbol,
                'price': float(current_price) if current_price else None,
                'volume': int(volume) if volume else 0,
                'timestamp': datetime.utcnow().isoformat(),
                'provider': 'yfinance'
            }
            
            logger.info(f"Successfully fetched {symbol}: ${quote_data['price']}")
            return quote_data
        
        except Exception as e:
            logger.error(f"Error fetching from yfinance for {symbol}: {e}")
            raise
    
    def _fetch_alphavantage(self, symbol: str) -> Dict:
        """
        Fetch data using Alpha Vantage API
        
        Args:
            symbol: Stock/crypto symbol
        
        Returns:
            Dictionary with quote data
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
        
        # Determine if it's crypto or stock
        is_crypto = '-' in symbol or 'BTC' in symbol or 'ETH' in symbol
        
        if is_crypto:
            # For crypto, symbol format is "BTC-USD" -> from_currency=BTC, to_currency=USD
            parts = symbol.split('-')
            from_currency = parts[0]
            to_currency = parts[1] if len(parts) > 1 else 'USD'
            
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency,
                'apikey': self.api_key
            }
        else:
            # Stock quote
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parse response based on type
        if is_crypto:
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                quote_data = {
                    'symbol': symbol,
                    'price': float(rate_data['5. Exchange Rate']),
                    'volume': 0,  # Alpha Vantage doesn't provide volume for crypto exchange rates
                    'timestamp': datetime.utcnow().isoformat(),
                    'provider': 'alphavantage'
                }
            else:
                raise ValueError(f"Unexpected response format: {data}")
        else:
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                quote_data = {
                    'symbol': symbol,
                    'price': float(quote['05. price']),
                    'volume': int(quote.get('06. volume', 0)),
                    'timestamp': datetime.utcnow().isoformat(),
                    'provider': 'alphavantage'
                }
            else:
                raise ValueError(f"No quote data returned for {symbol}. Response: {data}")
        
        logger.info(f"Successfully fetched {symbol}: ${quote_data['price']}")
        return quote_data
    
    def fetch_multiple(self, symbols: List[str]) -> List[Dict]:
        """
        Fetch quotes for multiple symbols
        
        Args:
            symbols: List of symbols to fetch
        
        Returns:
            List of quote dictionaries
        """
        logger.info(f"Fetching quotes for {len(symbols)} symbols")
        
        results = []
        for symbol in symbols:
            quote = self.fetch_quote(symbol)
            if quote:
                results.append(quote)
            
            # Add small delay to respect API rate limits
            time.sleep(0.5)
        
        logger.info(f"Successfully fetched {len(results)}/{len(symbols)} quotes")
        return results


# Convenience function
def fetch_market_data(symbols: List[str] = None) -> List[Dict]:
    """
    Convenience function to fetch market data for configured symbols
    
    Args:
        symbols: List of symbols (uses Config.SYMBOLS if not provided)
    
    Returns:
        List of quote dictionaries
    """
    if symbols is None:
        symbols = Config.SYMBOLS
    
    fetcher = MarketDataFetcher()
    return fetcher.fetch_multiple(symbols)
