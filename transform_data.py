"""
Data Transformation Module
Cleans, validates, and standardizes market data
"""

import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Transforms raw market data into clean, standardized format
    """
    
    @staticmethod
    def clean_and_standardize(raw_data: List[Dict]) -> pd.DataFrame:
        """
        Clean and standardize raw market data
        
        Args:
            raw_data: List of quote dictionaries from API
        
        Returns:
            Cleaned pandas DataFrame
        """
        logger.info(f"Transforming {len(raw_data)} records")
        
        if not raw_data:
            logger.warning("No data to transform")
            return pd.DataFrame(columns=['symbol', 'price', 'volume', 'timestamp', 'provider'])
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Initial record count
        initial_count = len(df)
        logger.info(f"Initial record count: {initial_count}")
        
        # Step 1: Standardize column names (convert to lowercase)
        df.columns = df.columns.str.lower().str.strip()
        
        # Step 2: Ensure required columns exist
        required_columns = ['symbol', 'price', 'timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Add optional columns if missing
        if 'volume' not in df.columns:
            df['volume'] = 0
            logger.info("Added missing 'volume' column with default value 0")
        
        if 'provider' not in df.columns:
            df['provider'] = 'unknown'
            logger.info("Added missing 'provider' column with default value 'unknown'")
        
        # Step 3: Clean missing values
        # Drop rows where price is None/NaN (critical field)
        df = df.dropna(subset=['price'])
        logger.info(f"Dropped {initial_count - len(df)} rows with missing price")
        
        # Fill missing volume with 0
        df['volume'] = df['volume'].fillna(0)
        
        # Fill missing symbols with 'UNKNOWN'
        df['symbol'] = df['symbol'].fillna('UNKNOWN')
        
        # Step 4: Ensure numeric consistency
        try:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            logger.error(f"Error converting to numeric: {e}")
            raise
        
        # Drop any rows where price conversion failed
        before_numeric_clean = len(df)
        df = df.dropna(subset=['price'])
        if before_numeric_clean > len(df):
            logger.warning(f"Dropped {before_numeric_clean - len(df)} rows with invalid numeric values")
        
        # Step 5: Convert timestamps to UTC
        df['timestamp'] = df['timestamp'].apply(DataTransformer._normalize_timestamp)
        
        # Step 6: Add processed timestamp
        df['processed_at'] = datetime.utcnow().isoformat()
        
        # Step 7: Sort by timestamp
        df = df.sort_values('timestamp', ascending=False)
        
        # Step 8: Validate price values (must be positive)
        df = df[df['price'] > 0]
        
        # Final validation
        final_count = len(df)
        logger.info(f"Transformation complete: {final_count} clean records")
        
        if final_count == 0:
            logger.warning("⚠️  No valid records after transformation!")
        
        return df
    
    @staticmethod
    def _normalize_timestamp(timestamp_str: str) -> str:
        """
        Normalize timestamp to UTC ISO format
        
        Args:
            timestamp_str: Timestamp string
        
        Returns:
            ISO format UTC timestamp
        """
        try:
            # If already ISO format, validate and return
            if isinstance(timestamp_str, str):
                # Try parsing as ISO format
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return dt.isoformat()
            else:
                # If datetime object
                return timestamp_str.isoformat()
        
        except Exception as e:
            logger.warning(f"Error normalizing timestamp '{timestamp_str}': {e}. Using current UTC time.")
            return datetime.utcnow().isoformat()
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, existing_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Remove duplicate records based on symbol and timestamp
        
        Args:
            df: New data DataFrame
            existing_df: Existing data DataFrame (optional)
        
        Returns:
            DataFrame with duplicates removed
        """
        initial_count = len(df)
        
        # Remove duplicates within new data
        df = df.drop_duplicates(subset=['symbol', 'timestamp'], keep='first')
        
        # If existing data provided, remove records that already exist
        if existing_df is not None and not existing_df.empty:
            # Create a composite key for comparison
            df['_key'] = df['symbol'] + '_' + df['timestamp']
            existing_df['_key'] = existing_df['symbol'] + '_' + existing_df['timestamp']
            
            # Filter out existing records
            df = df[~df['_key'].isin(existing_df['_key'])]
            
            # Drop the temporary key column
            df = df.drop('_key', axis=1)
            if '_key' in existing_df.columns:
                existing_df.drop('_key', axis=1, inplace=True)
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate records")
        
        return df
    
    @staticmethod
    def get_summary_statistics(df: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for the dataset
        
        Args:
            df: DataFrame with market data
        
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {
                'total_records': 0,
                'symbols': [],
                'date_range': None
            }
        
        stats = {
            'total_records': len(df),
            'symbols': df['symbol'].unique().tolist(),
            'symbol_count': df['symbol'].nunique(),
            'date_range': {
                'earliest': df['timestamp'].min(),
                'latest': df['timestamp'].max()
            },
            'price_stats': df.groupby('symbol')['price'].agg(['min', 'max', 'mean']).to_dict('index')
        }
        
        return stats


# Convenience function
def transform_market_data(raw_data: List[Dict], existing_data: pd.DataFrame = None) -> pd.DataFrame:
    """
    Convenience function to transform market data
    
    Args:
        raw_data: List of raw quote dictionaries
        existing_data: Existing DataFrame to check for duplicates
    
    Returns:
        Clean, transformed DataFrame
    """
    transformer = DataTransformer()
    
    # Clean and standardize
    df = transformer.clean_and_standardize(raw_data)
    
    # Remove duplicates
    df = transformer.remove_duplicates(df, existing_data)
    
    return df
