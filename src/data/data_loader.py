"""
Data loader and storage management using Parquet format.

This module handles:
1. Efficient storage and retrieval of market data using Parquet
2. Data caching and compression
3. Metadata management for datasets
4. Fast loading for backtesting operations
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np


class DataStore:
    """Efficient data storage and retrieval using Parquet format."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"
        self.cache_path = self.base_path / "cache"
        self.features_path = self.base_path / "features"
        
        # Ensure directories exist
        for path in [self.raw_path, self.processed_path, self.cache_path, self.features_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def save_dataset(
        self, 
        df: pd.DataFrame, 
        name: str, 
        category: str = "processed",
        metadata: Optional[Dict[str, Any]] = None,
        compression: str = "lz4"
    ) -> str:
        """
        Save dataset with compression and metadata.
        
        Args:
            df: DataFrame to save
            name: Dataset name (will be used as filename)
            category: Storage category (raw, processed, cache, features)
            metadata: Additional metadata to store
            compression: Compression algorithm (lz4, snappy, gzip)
        
        Returns:
            Path to saved file
        """
        if category == "raw":
            storage_path = self.raw_path
        elif category == "processed":
            storage_path = self.processed_path
        elif category == "cache":
            storage_path = self.cache_path
        elif category == "features":
            storage_path = self.features_path
        else:
            raise ValueError(f"Invalid category: {category}")
        
        # Prepare file paths
        file_path = storage_path / f"{name}.parquet"
        meta_path = storage_path / f"{name}_metadata.json"
        
        # Prepare metadata
        auto_metadata = {
            'created_at': datetime.now().isoformat(),
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'compression': compression,
            'category': category,
            'file_size_mb': None,  # Will be filled after saving
        }
        
        if metadata:
            auto_metadata.update(metadata)
        
        # Save DataFrame as Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_path, compression=compression)
        
        # Update file size in metadata
        auto_metadata['file_size_mb'] = file_path.stat().st_size / 1024 / 1024
        
        # Save metadata
        with open(meta_path, 'w') as f:
            json.dump(auto_metadata, f, indent=2)
        
        print(f"✅ Saved {name} ({df.shape[0]:,} rows, {df.shape[1]} cols) to {file_path}")
        print(f"📁 File size: {auto_metadata['file_size_mb']:.2f} MB")
        
        return str(file_path)
    
    def load_dataset(
        self, 
        name: str, 
        category: str = "processed",
        columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load dataset with metadata.
        
        Args:
            name: Dataset name
            category: Storage category
            columns: Specific columns to load (for performance)
        
        Returns:
            Tuple of (DataFrame, metadata)
        """
        if category == "raw":
            storage_path = self.raw_path
        elif category == "processed":
            storage_path = self.processed_path
        elif category == "cache":
            storage_path = self.cache_path
        elif category == "features":
            storage_path = self.features_path
        else:
            raise ValueError(f"Invalid category: {category}")
        
        file_path = storage_path / f"{name}.parquet"
        meta_path = storage_path / f"{name}_metadata.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")
        
        # Load metadata
        metadata = {}
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
        
        # Load DataFrame
        if columns:
            df = pd.read_parquet(file_path, columns=columns)
        else:
            df = pd.read_parquet(file_path)
        
        print(f"📖 Loaded {name} ({df.shape[0]:,} rows, {df.shape[1]} cols)")
        
        return df, metadata
    
    def list_datasets(self, category: str = "processed") -> List[Dict[str, Any]]:
        """List all available datasets in a category."""
        if category == "raw":
            storage_path = self.raw_path
        elif category == "processed":
            storage_path = self.processed_path
        elif category == "cache":
            storage_path = self.cache_path
        elif category == "features":
            storage_path = self.features_path
        else:
            raise ValueError(f"Invalid category: {category}")
        
        datasets = []
        for file_path in storage_path.glob("*.parquet"):
            name = file_path.stem
            meta_path = storage_path / f"{name}_metadata.json"
            
            metadata = {'name': name, 'file_path': str(file_path)}
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    metadata.update(json.load(f))
            
            datasets.append(metadata)
        
        return sorted(datasets, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def dataset_exists(self, name: str, category: str = "processed") -> bool:
        """Check if a dataset exists."""
        if category == "raw":
            storage_path = self.raw_path
        elif category == "processed":
            storage_path = self.processed_path
        elif category == "cache":
            storage_path = self.cache_path
        elif category == "features":
            storage_path = self.features_path
        else:
            return False
        
        file_path = storage_path / f"{name}.parquet"
        return file_path.exists()
    
    def delete_dataset(self, name: str, category: str = "processed") -> bool:
        """Delete a dataset and its metadata."""
        if category == "raw":
            storage_path = self.raw_path
        elif category == "processed":
            storage_path = self.processed_path
        elif category == "cache":
            storage_path = self.cache_path
        elif category == "features":
            storage_path = self.features_path
        else:
            return False
        
        file_path = storage_path / f"{name}.parquet"
        meta_path = storage_path / f"{name}_metadata.json"
        
        deleted = False
        if file_path.exists():
            file_path.unlink()
            deleted = True
        
        if meta_path.exists():
            meta_path.unlink()
        
        if deleted:
            print(f"🗑️  Deleted dataset: {name}")
        
        return deleted
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """Get summary of storage usage."""
        summary = {
            'categories': {},
            'total_size_mb': 0,
            'total_files': 0
        }
        
        for category, path in [
            ('raw', self.raw_path),
            ('processed', self.processed_path), 
            ('cache', self.cache_path),
            ('features', self.features_path)
        ]:
            datasets = self.list_datasets(category)
            size_mb = sum(d.get('file_size_mb', 0) for d in datasets)
            
            summary['categories'][category] = {
                'count': len(datasets),
                'size_mb': size_mb,
                'datasets': [d['name'] for d in datasets]
            }
            
            summary['total_size_mb'] += size_mb
            summary['total_files'] += len(datasets)
        
        return summary


class QuickDataLoader:
    """Convenience class for quick data loading operations."""
    
    def __init__(self, base_path: str = "data"):
        self.store = DataStore(base_path)
    
    def load_latest_synthetic_swaps(self) -> pd.DataFrame:
        """Load the most recent synthetic swap data."""
        datasets = self.store.list_datasets("processed")
        swap_datasets = [d for d in datasets if 'synthetic_swaps' in d['name']]
        
        if not swap_datasets:
            raise FileNotFoundError("No synthetic swap datasets found")
        
        latest_dataset = swap_datasets[0]  # Already sorted by creation time
        df, _ = self.store.load_dataset(latest_dataset['name'], "processed")
        return df
    
    def load_strategy_data(
        self, 
        dataset_name: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """Load data optimized for strategy development."""
        if dataset_name is None:
            df = self.load_latest_synthetic_swaps()
        else:
            df, _ = self.store.load_dataset(dataset_name, "processed")
        
        # Convert timestamp column if it exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp').sort_index()
        
        # Filter by date range if specified
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        return df
    
    def get_data_summary(self) -> None:
        """Print a summary of available data."""
        summary = self.store.get_storage_summary()
        
        print("📊 Data Storage Summary")
        print("=" * 50)
        print(f"Total files: {summary['total_files']}")
        print(f"Total size: {summary['total_size_mb']:.2f} MB")
        print()
        
        for category, info in summary['categories'].items():
            print(f"📁 {category.upper()}:")
            print(f"   Files: {info['count']}")
            print(f"   Size: {info['size_mb']:.2f} MB")
            if info['datasets']:
                print(f"   Datasets: {', '.join(info['datasets'][:3])}")
                if len(info['datasets']) > 3:
                    print(f"            ... and {len(info['datasets']) - 3} more")
            print()


# Convenience functions
def save_synthetic_data(df: pd.DataFrame, name: str = None) -> str:
    """Quick function to save synthetic swap data."""
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"synthetic_swaps_{timestamp}"
    
    store = DataStore()
    return store.save_dataset(
        df, 
        name, 
        category="processed",
        metadata={
            'data_type': 'synthetic_eulerswap',
            'purpose': 'backtesting_demonstration',
            'warning': 'synthetic_data_for_educational_use_only'
        }
    )


def load_latest_data() -> pd.DataFrame:
    """Quick function to load latest synthetic data for strategy development."""
    loader = QuickDataLoader()
    return loader.load_latest_synthetic_swaps()


if __name__ == "__main__":
    # Test the data loader
    store = DataStore()
    
    # Create sample data
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=100, freq='H'),
        'price': np.random.randn(100).cumsum() + 2000,
        'volume': np.random.exponential(1000, 100),
        'synthetic': True
    })
    
    # Test save and load
    store.save_dataset(sample_data, "test_dataset", metadata={'test': True})
    
    # Test load
    loaded_df, metadata = store.load_dataset("test_dataset")
    print(f"Original shape: {sample_data.shape}")
    print(f"Loaded shape: {loaded_df.shape}")
    print(f"Metadata: {metadata.get('test')}")
    
    # Test summary
    loader = QuickDataLoader()
    loader.get_data_summary()
    
    # Cleanup
    store.delete_dataset("test_dataset")