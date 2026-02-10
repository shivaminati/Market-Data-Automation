"""
Main Module
Orchestrates the complete market data automation workflow
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_data import fetch_market_data
from transform_data import transform_market_data
from storage import DataStorage, save_data
from alerts import AlertManager, check_and_alert
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class MarketDataAutomation:
    """
    Main orchestrator for market data automation
    """
    
    def __init__(self):
        """Initialize the automation system"""
        logger.info("="*70)
        logger.info("Market Data Automation Tool - Starting")
        logger.info("="*70)
        
        self.storage = DataStorage()
        self.alert_manager = AlertManager()
        
        # Display configuration
        self._display_configuration()
    
    def _display_configuration(self):
        """Display current configuration"""
        logger.info(f"API Provider: {Config.API_PROVIDER}")
        logger.info(f"Tracking Symbols: {', '.join(Config.SYMBOLS)}")
        logger.info(f"Database: {Config.DATABASE_PATH}")
        logger.info(f"Email Alerts: {'ENABLED' if Config.ENABLE_EMAIL_ALERTS else 'DISABLED'}")
        
        # Display thresholds
        if Config.ALERT_THRESHOLDS:
            logger.info("\nConfigured Thresholds:")
            for symbol, thresholds in Config.ALERT_THRESHOLDS.items():
                min_val = f"${thresholds['min']:.2f}" if thresholds['min'] else "N/A"
                max_val = f"${thresholds['max']:.2f}" if thresholds['max'] else "N/A"
                logger.info(f"  {symbol}: Min={min_val}, Max={max_val}")
        
        logger.info("="*70)
    
    def run(self):
        """
        Execute the complete automation workflow
        
        Returns:
            Success status (True/False)
        """
        start_time = datetime.utcnow()
        logger.info(f"\n{'🚀 Starting Data Collection Run':^70}")
        logger.info(f"{'Timestamp: ' + start_time.isoformat():^70}\n")
        
        try:
            # Step 1: Fetch data
            logger.info("Step 1/5: Fetching market data...")
            raw_data = fetch_market_data(Config.SYMBOLS)
            
            if not raw_data:
                logger.warning("No data fetched. Exiting.")
                return False
            
            logger.info(f"✓ Fetched {len(raw_data)} quotes")
            
            # Step 2: Transform data
            logger.info("\nStep 2/5: Transforming data...")
            existing_data = self.storage.load_from_database()
            clean_data = transform_market_data(raw_data, existing_data)
            
            if clean_data.empty:
                logger.info("No new data to process (all duplicates or invalid)")
                # Still check alerts with raw data
                check_and_alert(raw_data)
                return True
            
            logger.info(f"✓ Cleaned {len(clean_data)} records")
            
            # Step 3: Save data
            logger.info("\nStep 3/5: Saving data...")
            saved_count = save_data(clean_data)
            logger.info(f"✓ Saved {saved_count} records to database and CSV")
            
            # Step 4: Check alerts
            logger.info("\nStep 4/5: Checking price alerts...")
            alerts = check_and_alert(raw_data)
            
            if alerts:
                logger.info(f"🚨 Triggered {len(alerts)} alert(s)")
            else:
                logger.info("✓ No alerts triggered")
            
            # Step 5: Display summary
            logger.info("\nStep 5/5: Generating summary...")
            self._display_summary(raw_data, saved_count, alerts)
            
            # Display execution time
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "="*70)
            logger.info(f"✅ Run completed successfully in {duration:.2f} seconds")
            logger.info("="*70 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"\n❌ Error during execution: {e}", exc_info=True)
            return False
    
    def _display_summary(self, quotes, saved_count, alerts):
        """
        Display execution summary
        
        Args:
            quotes: List of fetched quotes
            saved_count: Number of records saved
            alerts: List of triggered alerts
        """
        print("\n" + "="*70)
        print("📊 EXECUTION SUMMARY")
        print("="*70)
        
        # Latest prices
        print("\n💰 LATEST PRICES:")
        for quote in quotes:
            symbol = quote['symbol']
            price = quote['price']
            volume = quote.get('volume', 0)
            
            # Check if any alerts for this symbol
            symbol_alerts = [a for a in alerts if a['symbol'] == symbol]
            alert_indicator = " 🚨" if symbol_alerts else ""
            
            print(f"  {symbol}: ${price:.2f} (Volume: {volume:,}){alert_indicator}")
        
        # Database stats
        stats = self.storage.get_statistics()
        print(f"\n📁 DATABASE STATISTICS:")
        print(f"  Total Records: {stats.get('total_records', 0):,}")
        print(f"  Unique Symbols: {stats.get('unique_symbols', 0)}")
        print(f"  Records Saved This Run: {saved_count}")
        
        if stats.get('date_range'):
            print(f"  Data Range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        
        # Alert summary
        if alerts:
            print(f"\n🚨 ALERTS TRIGGERED: {len(alerts)}")
            for alert in alerts:
                print(f"  - {alert['message']}")
        else:
            print(f"\n✓ No price alerts triggered")
        
        print("\n" + "="*70 + "\n")
    
    def display_historical_data(self, symbol: str = None, limit: int = 10):
        """
        Display historical data from database
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Number of records to display
        """
        print("\n" + "="*70)
        print(f"📜 HISTORICAL DATA" + (f" - {symbol}" if symbol else ""))
        print("="*70 + "\n")
        
        df = self.storage.load_from_database(symbol, limit)
        
        if df.empty:
            print("No historical data available")
        else:
            # Format and display
            pd_options = [
                'display.max_rows', None,
                'display.max_columns', None,
                'display.width', None,
                'display.max_colwidth', 30
            ]
            
            import pandas as pd
            with pd.option_context(*pd_options):
                print(df[['symbol', 'price', 'volume', 'timestamp', 'provider']].to_string(index=False))
        
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create automation instance
        automation = MarketDataAutomation()
        
        # Run the automation
        success = automation.run()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
