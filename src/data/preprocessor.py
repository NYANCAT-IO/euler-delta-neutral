"""
Data preprocessing and feature engineering for delta-neutral strategies.

This module provides:
1. Data cleaning and validation
2. Technical indicator calculation
3. Feature engineering for delta-neutral strategies
4. Data quality checks and reporting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings


@dataclass
class DataQualityReport:
    """Report on data quality metrics."""
    total_records: int
    missing_values: Dict[str, int]
    outliers: Dict[str, int]
    date_range: Tuple[str, str]
    data_gaps: List[str]
    quality_score: float
    warnings: List[str]
    recommendations: List[str]


class EulerDataProcessor:
    """Data processor specialized for Euler delta-neutral strategies."""
    
    def __init__(self):
        self.required_columns = [
            'timestamp', 'asset0_price_usd', 'asset1_price_usd', 
            'swap_volume_usd', 'total_liquidity_usd'
        ]
        self.optional_columns = [
            'vault0_balance', 'vault1_balance', 'vault_utilization_rate',
            'trading_fee_rate', 'vault_apy_asset0', 'vault_apy_asset1'
        ]
    
    def validate_data(self, df: pd.DataFrame) -> DataQualityReport:
        """Comprehensive data quality validation."""
        warnings = []
        recommendations = []
        
        # Check required columns
        missing_required = [col for col in self.required_columns if col not in df.columns]
        if missing_required:
            warnings.append(f"Missing required columns: {missing_required}")
        
        # Check for missing values
        missing_values = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                missing_values[col] = missing_count
                if missing_count / len(df) > 0.1:  # >10% missing
                    warnings.append(f"High missing values in {col}: {missing_count} ({missing_count/len(df)*100:.1f}%)")
        
        # Check for outliers using IQR method
        outliers = {}
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col not in ['timestamp', 'block_number']:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_count = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
                if outlier_count > 0:
                    outliers[col] = outlier_count
        
        # Check date range and gaps
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            date_range = (str(df_sorted['timestamp'].min()), str(df_sorted['timestamp'].max()))
            
            # Check for significant time gaps (>2x expected frequency)
            time_diffs = df_sorted['timestamp'].diff()
            median_diff = time_diffs.median()
            large_gaps = time_diffs[time_diffs > median_diff * 2]
            data_gaps = [str(gap) for gap in large_gaps.head(5)]  # Top 5 gaps
            
            if len(large_gaps) > len(df) * 0.05:  # >5% of records have large gaps
                warnings.append(f"Frequent data gaps detected: {len(large_gaps)} gaps")
        else:
            date_range = ("Unknown", "Unknown")
            data_gaps = []
            warnings.append("No timestamp column found")
        
        # Calculate quality score
        quality_score = 100.0
        quality_score -= len(missing_required) * 20  # -20 per missing required column
        quality_score -= sum(missing_values.values()) / len(df) * 50  # -50 for 100% missing
        quality_score -= len(outliers) * 5  # -5 per column with outliers
        quality_score -= len(data_gaps) * 2  # -2 per data gap
        quality_score = max(0, quality_score)
        
        # Generate recommendations
        if missing_values:
            recommendations.append("Consider imputing missing values or filtering incomplete records")
        if outliers:
            recommendations.append("Review outliers - may indicate data quality issues or extreme market events")
        if data_gaps:
            recommendations.append("Fill data gaps using interpolation or mark as missing periods")
        if quality_score < 80:
            recommendations.append("Data quality is below recommended threshold - review before backtesting")
        
        return DataQualityReport(
            total_records=len(df),
            missing_values=missing_values,
            outliers=outliers,
            date_range=date_range,
            data_gaps=data_gaps,
            quality_score=quality_score,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def clean_data(self, df: pd.DataFrame, aggressive: bool = False) -> pd.DataFrame:
        """Clean and prepare data for analysis."""
        df_clean = df.copy()
        
        # Convert timestamp to datetime
        if 'timestamp' in df_clean.columns:
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
            df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
        
        # Handle missing values
        numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in ['price_ratio', 'asset0_price_usd', 'asset1_price_usd']:
                # Forward fill prices (reasonable for short gaps)
                df_clean[col] = df_clean[col].fillna(method='ffill')
            elif col in ['swap_volume_usd', 'swap_volume_asset0', 'swap_volume_asset1']:
                # Fill volume with 0 (no trading)
                df_clean[col] = df_clean[col].fillna(0)
            else:
                # Forward fill other numeric columns
                df_clean[col] = df_clean[col].fillna(method='ffill')
        
        # Remove extreme outliers if aggressive cleaning
        if aggressive:
            for col in ['asset0_price_usd', 'asset1_price_usd', 'swap_volume_usd']:
                if col in df_clean.columns:
                    Q1 = df_clean[col].quantile(0.01)
                    Q99 = df_clean[col].quantile(0.99)
                    df_clean = df_clean[(df_clean[col] >= Q1) & (df_clean[col] <= Q99)]
        
        # Ensure positive values for prices and volumes
        price_columns = ['asset0_price_usd', 'asset1_price_usd', 'price_ratio']
        for col in price_columns:
            if col in df_clean.columns:
                df_clean = df_clean[df_clean[col] > 0]
        
        volume_columns = ['swap_volume_usd', 'total_liquidity_usd']
        for col in volume_columns:
            if col in df_clean.columns:
                df_clean = df_clean[df_clean[col] >= 0]
        
        return df_clean.reset_index(drop=True)
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for strategy development."""
        df_indicators = df.copy()
        
        if 'price_ratio' not in df_indicators.columns and 'asset0_price_usd' in df_indicators.columns:
            df_indicators['price_ratio'] = df_indicators['asset0_price_usd'] / df_indicators.get('asset1_price_usd', 1)
        
        # Price-based indicators
        if 'price_ratio' in df_indicators.columns:
            # Moving averages (multiple timeframes)
            for window in [6, 12, 24, 48, 168]:  # 6h, 12h, 24h, 48h, 1w
                df_indicators[f'price_sma_{window}h'] = df_indicators['price_ratio'].rolling(window).mean()
                df_indicators[f'price_ema_{window}h'] = df_indicators['price_ratio'].ewm(span=window).mean()
            
            # Volatility indicators
            for window in [12, 24, 168]:  # 12h, 24h, 1w
                df_indicators[f'price_volatility_{window}h'] = df_indicators['price_ratio'].rolling(window).std()
                df_indicators[f'price_returns_{window}h'] = df_indicators['price_ratio'].pct_change(window)
            
            # Price momentum
            df_indicators['price_momentum_6h'] = df_indicators['price_ratio'] / df_indicators['price_ratio'].shift(6) - 1
            df_indicators['price_momentum_24h'] = df_indicators['price_ratio'] / df_indicators['price_ratio'].shift(24) - 1
            
            # Bollinger Bands (24h)
            sma_24 = df_indicators['price_ratio'].rolling(24).mean()
            std_24 = df_indicators['price_ratio'].rolling(24).std()
            df_indicators['bb_upper_24h'] = sma_24 + (std_24 * 2)
            df_indicators['bb_lower_24h'] = sma_24 - (std_24 * 2)
            df_indicators['bb_position_24h'] = (df_indicators['price_ratio'] - df_indicators['bb_lower_24h']) / (df_indicators['bb_upper_24h'] - df_indicators['bb_lower_24h'])
        
        # Volume-based indicators
        if 'swap_volume_usd' in df_indicators.columns:
            for window in [6, 24, 168]:  # 6h, 24h, 1w
                df_indicators[f'volume_sma_{window}h'] = df_indicators['swap_volume_usd'].rolling(window).mean()
                df_indicators[f'volume_ratio_{window}h'] = df_indicators['swap_volume_usd'] / df_indicators[f'volume_sma_{window}h']
        
        # Liquidity indicators
        if 'total_liquidity_usd' in df_indicators.columns:
            df_indicators['liquidity_change_24h'] = df_indicators['total_liquidity_usd'].pct_change(24)
            df_indicators['liquidity_sma_24h'] = df_indicators['total_liquidity_usd'].rolling(24).mean()
        
        return df_indicators
    
    def calculate_delta_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features specifically for delta-neutral strategies."""
        df_delta = df.copy()
        
        # Ensure we have price ratio
        if 'price_ratio' not in df_delta.columns:
            if 'asset0_price_usd' in df_delta.columns:
                df_delta['price_ratio'] = df_delta['asset0_price_usd'] / df_delta.get('asset1_price_usd', 1)
            else:
                raise ValueError("Cannot calculate delta features without price data")
        
        # Delta exposure calculation (assuming 50/50 LP position initially)
        df_delta['lp_value_asset0'] = 0.5  # Assume 50% allocation
        df_delta['lp_value_asset1'] = 0.5  # Assume 50% allocation
        
        # Calculate implied delta for LP position
        # For a constant product AMM: delta = 0.5 * (1 - sqrt(price_current/price_initial))
        if len(df_delta) > 0:
            initial_price = df_delta['price_ratio'].iloc[0]
            df_delta['price_ratio_normalized'] = df_delta['price_ratio'] / initial_price
            df_delta['lp_delta'] = 0.5 * (1 - np.sqrt(df_delta['price_ratio_normalized']))
        
        # Delta hedge requirements
        df_delta['required_hedge_ratio'] = -df_delta['lp_delta']  # Opposite to neutralize
        
        # Rebalancing triggers
        for threshold in [0.05, 0.1, 0.2]:  # 5%, 10%, 20% delta thresholds
            df_delta[f'rebalance_signal_{int(threshold*100)}pct'] = (
                np.abs(df_delta['lp_delta']) > threshold
            ).astype(int)
        
        # Impermanent loss calculation
        df_delta['impermanent_loss'] = (
            2 * np.sqrt(df_delta['price_ratio_normalized']) / 
            (1 + df_delta['price_ratio_normalized']) - 1
        )
        
        # Vault utilization impact (if available)
        if 'vault_utilization_rate' in df_delta.columns:
            df_delta['available_leverage'] = 1 / (1 - df_delta['vault_utilization_rate'].clip(0, 0.95))
            df_delta['borrow_capacity'] = (1 - df_delta['vault_utilization_rate']).clip(0, 1)
        
        return df_delta
    
    def process_for_backtesting(
        self, 
        df: pd.DataFrame, 
        clean_data: bool = True,
        add_indicators: bool = True,
        add_delta_features: bool = True
    ) -> Tuple[pd.DataFrame, DataQualityReport]:
        """Complete processing pipeline for backtesting."""
        print("🔄 Processing data for backtesting...")
        
        # Validate input data
        quality_report = self.validate_data(df)
        print(f"📊 Initial data quality score: {quality_report.quality_score:.1f}/100")
        
        # Clean data
        if clean_data:
            df_processed = self.clean_data(df, aggressive=False)
            print(f"🧹 Cleaned data: {len(df)} → {len(df_processed)} records")
        else:
            df_processed = df.copy()
        
        # Add technical indicators
        if add_indicators:
            df_processed = self.calculate_technical_indicators(df_processed)
            print("📈 Added technical indicators")
        
        # Add delta-neutral features
        if add_delta_features:
            df_processed = self.calculate_delta_features(df_processed)
            print("⚖️  Added delta-neutral features")
        
        # Set timestamp as index if available
        if 'timestamp' in df_processed.columns:
            df_processed = df_processed.set_index('timestamp').sort_index()
        
        # Final quality check
        final_quality = self.validate_data(df_processed.reset_index())
        print(f"✅ Final data quality score: {final_quality.quality_score:.1f}/100")
        
        return df_processed, final_quality


def quick_process_synthetic_data(df: pd.DataFrame) -> pd.DataFrame:
    """Quick processing function for synthetic data."""
    processor = EulerDataProcessor()
    processed_df, _ = processor.process_for_backtesting(df)
    return processed_df


if __name__ == "__main__":
    # Test the processor with sample data
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=168, freq='H'),  # 1 week hourly
        'asset0_price_usd': 2000 + np.random.randn(168).cumsum() * 10,
        'asset1_price_usd': np.ones(168),  # Stable
        'swap_volume_usd': np.random.exponential(10000, 168),
        'total_liquidity_usd': 5000000 + np.random.randn(168).cumsum() * 50000,
        'vault_utilization_rate': np.random.uniform(0.3, 0.8, 168),
        'is_synthetic': True
    })
    
    processor = EulerDataProcessor()
    
    # Test validation
    quality_report = processor.validate_data(sample_data)
    print(f"Quality Score: {quality_report.quality_score}")
    print(f"Warnings: {quality_report.warnings}")
    
    # Test full processing
    processed_data, final_report = processor.process_for_backtesting(sample_data)
    print(f"Processed shape: {processed_data.shape}")
    print(f"New columns: {[col for col in processed_data.columns if col not in sample_data.columns][:5]}...")