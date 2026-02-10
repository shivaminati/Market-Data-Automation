"""
Unit Tests for Market Data Automation Tool
Run with: python -m unittest tests/test_all.py
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from transform_data import DataTransformer
import pandas as pd


class TestDataTransformer(unittest.TestCase):
    """Test data transformation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_data = [
            {
                'symbol': 'AAPL',
                'price': 150.50,
                'volume': 1000000,
                'timestamp': '2024-02-10T10:00:00',
                'provider': 'yfinance'
            },
            {
                'symbol': 'MSFT',
                'price': 350.75,
                'volume': 500000,
                'timestamp': '2024-02-10T10:00:00',
                'provider': 'yfinance'
            }
        ]
    
    def test_clean_and_standardize(self):
        """Test data cleaning and standardization"""
        df = DataTransformer.clean_and_standardize(self.sample_data)
        
        # Check DataFrame is not empty
        self.assertFalse(df.empty)
        
        # Check required columns exist
        required_cols = ['symbol', 'price', 'volume', 'timestamp', 'provider']
        for col in required_cols:
            self.assertIn(col, df.columns)
        
        # Check data types
        self.assertTrue(pd.api.types.is_numeric_dtype(df['price']))
        self.assertTrue(pd.api.types.is_integer_dtype(df['volume']))
    
    def test_remove_duplicates(self):
        """Test duplicate removal"""
        # Create data with duplicates
        duplicate_data = self.sample_data + [self.sample_data[0]]
        df = DataTransformer.clean_and_standardize(duplicate_data)
        
        # Remove duplicates
        df_clean = DataTransformer.remove_duplicates(df)
        
        # Should have 2 unique records (AAPL and MSFT)
        self.assertEqual(len(df_clean), 2)
    
    def test_handle_missing_price(self):
        """Test handling of missing price data"""
        bad_data = [
            {
                'symbol': 'TEST',
                'price': None,  # Missing price
                'volume': 0,
                'timestamp': '2024-02-10T10:00:00',
                'provider': 'test'
            }
        ]
        
        df = DataTransformer.clean_and_standardize(bad_data)
        
        # Should drop rows with missing price
        self.assertTrue(df.empty)
    
    def test_numeric_conversion(self):
        """Test numeric value conversion"""
        df = DataTransformer.clean_and_standardize(self.sample_data)
        
        # Prices should be float
        self.assertEqual(df['price'].dtype, 'float64')
        
        # Volumes should be int
        self.assertEqual(df['volume'].dtype, 'int64')


class TestAlertLogic(unittest.TestCase):
    """Test alert threshold logic"""
    
    def test_threshold_check_below(self):
        """Test alert when price goes below threshold"""
        from alerts import AlertManager
        
        manager = AlertManager()
        # Override thresholds for testing
        manager.thresholds = {'TEST': {'min': 100.0, 'max': 200.0}}
        
        quote = {
            'symbol': 'TEST',
            'price': 95.0,
            'volume': 1000,
            'timestamp': '2024-02-10T10:00:00'
        }
        
        alerts = manager.check_thresholds(quote)
        
        # Should trigger one alert (below minimum)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['threshold_type'], 'BELOW_MINIMUM')
    
    def test_threshold_check_above(self):
        """Test alert when price goes above threshold"""
        from alerts import AlertManager
        
        manager = AlertManager()
        manager.thresholds = {'TEST': {'min': 100.0, 'max': 200.0}}
        
        quote = {
            'symbol': 'TEST',
            'price': 205.0,
            'volume': 1000,
            'timestamp': '2024-02-10T10:00:00'
        }
        
        alerts = manager.check_thresholds(quote)
        
        # Should trigger one alert (above maximum)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['threshold_type'], 'ABOVE_MAXIMUM')
    
    def test_threshold_check_within_range(self):
        """Test no alert when price is within range"""
        from alerts import AlertManager
        
        manager = AlertManager()
        manager.thresholds = {'TEST': {'min': 100.0, 'max': 200.0}}
        
        quote = {
            'symbol': 'TEST',
            'price': 150.0,
            'volume': 1000,
            'timestamp': '2024-02-10T10:00:00'
        }
        
        alerts = manager.check_thresholds(quote)
        
        # Should not trigger any alerts
        self.assertEqual(len(alerts), 0)


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_symbols_parsing(self):
        """Test symbol list parsing"""
        from config import Config
        
        # Should be a list
        self.assertIsInstance(Config.SYMBOLS, list)
        
        # Should not be empty (from .env)
        self.assertGreater(len(Config.SYMBOLS), 0)
    
    def test_config_thresholds_parsing(self):
        """Test threshold parsing"""
        from config import Config
        
        # Should be a dictionary
        self.assertIsInstance(Config.ALERT_THRESHOLDS, dict)
        
        # Check structure if thresholds exist
        if Config.ALERT_THRESHOLDS:
            for symbol, thresholds in Config.ALERT_THRESHOLDS.items():
                self.assertIn('min', thresholds)
                self.assertIn('max', thresholds)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
