"""
Data Storage Module
Handles SQLite database and CSV file operations
"""

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
from config import Config

# Configure logging
logger = logging.getLogger(__name__)


class DataStorage:
    """
    Manages data persistence in SQLite and CSV formats
    """
    
    def __init__(self, db_path: Path = None, csv_path: Path = None):
        """
        Initialize storage manager
        
        Args:
            db_path: Path to SQLite database file
            csv_path: Path to CSV export file
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self.csv_path = csv_path or Config.CSV_EXPORT_PATH
        
        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"Storage initialized: DB={self.db_path}, CSV={self.csv_path}")
    
    def _initialize_database(self):
        """Create database table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create market_data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume INTEGER DEFAULT 0,
                        timestamp TEXT NOT NULL,
                        provider TEXT,
                        processed_at TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timestamp)
                    )
                ''')
                
                # Create index for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                    ON market_data(symbol, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON market_data(timestamp)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_to_database(self, df: pd.DataFrame) -> int:
        """
        Save DataFrame to SQLite database
        
        Args:
            df: DataFrame to save
        
        Returns:
            Number of records saved
        """
        if df.empty:
            logger.info("No data to save to database")
            return 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use 'replace' to handle duplicates (based on UNIQUE constraint)
                records_saved = df.to_sql(
                    'market_data',
                    conn,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                
                logger.info(f"Saved {len(df)} records to database")
                return len(df)
        
        except sqlite3.IntegrityError as e:
            # Handle duplicate entries
            logger.warning(f"Duplicate entries detected, using individual inserts: {e}")
            return self._save_with_ignore_duplicates(df)
        
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            raise
    
    def _save_with_ignore_duplicates(self, df: pd.DataFrame) -> int:
        """
        Save records individually, ignoring duplicates
        
        Args:
            df: DataFrame to save
        
        Returns:
            Number of records actually saved
        """
        saved_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for _, row in df.iterrows():
                    try:
                        cursor.execute('''
                            INSERT INTO market_data 
                            (symbol, price, volume, timestamp, provider, processed_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            row['symbol'],
                            row['price'],
                            row['volume'],
                            row['timestamp'],
                            row.get('provider', 'unknown'),
                            row.get('processed_at', pd.Timestamp.utcnow().isoformat())
                        ))
                        saved_count += 1
                    
                    except sqlite3.IntegrityError:
                        # Skip duplicate
                        continue
                
                conn.commit()
                logger.info(f"Saved {saved_count}/{len(df)} records (skipped duplicates)")
        
        except Exception as e:
            logger.error(f"Error in individual save: {e}")
            raise
        
        return saved_count
    
    def load_from_database(self, symbol: str = None, limit: int = None) -> pd.DataFrame:
        """
        Load data from database
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of records to return (optional)
        
        Returns:
            DataFrame with market data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM market_data"
                params = []
                
                if symbol:
                    query += " WHERE symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                logger.info(f"Loaded {len(df)} records from database")
                return df
        
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return pd.DataFrame()
    
    def get_latest_prices(self) -> pd.DataFrame:
        """
        Get the latest price for each symbol
        
        Returns:
            DataFrame with latest prices per symbol
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT symbol, price, volume, timestamp, provider
                    FROM market_data
                    WHERE (symbol, timestamp) IN (
                        SELECT symbol, MAX(timestamp)
                        FROM market_data
                        GROUP BY symbol
                    )
                    ORDER BY symbol
                '''
                
                df = pd.read_sql_query(query, conn)
                logger.info(f"Retrieved latest prices for {len(df)} symbols")
                return df
        
        except Exception as e:
            logger.error(f"Error getting latest prices: {e}")
            return pd.DataFrame()
    
    def export_to_csv(self, df: pd.DataFrame = None, append: bool = False):
        """
        Export data to CSV file
        
        Args:
            df: DataFrame to export (loads all from DB if not provided)
            append: Whether to append to existing file
        """
        try:
            if df is None:
                # Load all data from database
                df = self.load_from_database()
            
            if df.empty:
                logger.info("No data to export to CSV")
                return
            
            # Remove database-specific columns if present
            columns_to_drop = ['id', 'created_at']
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
            
            # Export to CSV
            mode = 'a' if append and self.csv_path.exists() else 'w'
            header = not (append and self.csv_path.exists())
            
            df.to_csv(self.csv_path, mode=mode, header=header, index=False)
            
            logger.info(f"Exported {len(df)} records to {self.csv_path}")
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def get_statistics(self) -> dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with database stats
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute("SELECT COUNT(*) FROM market_data")
                total_records = cursor.fetchone()[0]
                
                # Unique symbols
                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_data")
                unique_symbols = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM market_data")
                date_range = cursor.fetchone()
                
                # Records per symbol
                cursor.execute('''
                    SELECT symbol, COUNT(*) as count 
                    FROM market_data 
                    GROUP BY symbol
                    ORDER BY count DESC
                ''')
                symbol_counts = cursor.fetchall()
                
                stats = {
                    'total_records': total_records,
                    'unique_symbols': unique_symbols,
                    'date_range': {
                        'earliest': date_range[0],
                        'latest': date_range[1]
                    },
                    'records_per_symbol': dict(symbol_counts)
                }
                
                return stats
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Remove data older than specified days
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of records deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM market_data 
                    WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
                ''', (days,))
                
                deleted = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted} records older than {days} days")
                return deleted
        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0


# Convenience functions
def save_data(df: pd.DataFrame) -> int:
    """
    Convenience function to save data
    
    Args:
        df: DataFrame to save
    
    Returns:
        Number of records saved
    """
    storage = DataStorage()
    count = storage.save_to_database(df)
    storage.export_to_csv(df, append=True)
    return count


def load_data(symbol: str = None, limit: int = None) -> pd.DataFrame:
    """
    Convenience function to load data
    
    Args:
        symbol: Filter by symbol
        limit: Maximum records
    
    Returns:
        DataFrame with data
    """
    storage = DataStorage()
    return storage.load_from_database(symbol, limit)
