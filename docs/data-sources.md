# Data Sources and Subgraph Analysis

## Overview

This document analyzes the available data sources for implementing delta-neutral LP strategies on EulerSwap, focusing on The Graph Protocol subgraphs and their data quality, availability, and suitability for backtesting.

## Available Subgraphs

### 1. Official Euler Finance Subgraph
- **Subgraph ID**: `95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr`
- **Network**: Arbitrum One
- **Last Updated**: ~2 years ago
- **Status**: Official but potentially outdated
- **URL**: `https://gateway.thegraph.com/api/subgraphs/id/95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr`

### 2. Community Euler Subgraph
- **Subgraph ID**: `7TKfCCjXaAeZSFaGh3ccir8JnQd1K4Rjq75G6KnVQnoP`
- **Network**: Arbitrum One  
- **Last Updated**: ~4 months ago
- **Status**: Community-maintained, more recent
- **URL**: `https://gateway.thegraph.com/api/subgraphs/id/7TKfCCjXaAeZSFaGh3ccir8JnQd1K4Rjq75G6KnVQnoP`

## Subgraph Capabilities Analysis

### Key Question: Euler Finance vs. EulerSwap Data

The critical distinction is between:
- **Euler Finance**: The lending protocol with vaults and borrowing
- **EulerSwap**: The DEX/AMM built on top of Euler's infrastructure

**Investigation Required**: Determine which subgraph contains EulerSwap-specific data vs. just Euler Finance lending data.

### Expected Data Entities

#### For Delta-Neutral LP Strategies, we need:

#### 1. Swap/AMM Data
```graphql
type Swap {
  id: ID!
  timestamp: BigInt!
  blockNumber: BigInt!
  transactionHash: Bytes!
  
  # Pool information
  pool: Pool!
  asset0: Asset!
  asset1: Asset!
  
  # Swap details
  amount0In: BigDecimal!
  amount1In: BigDecimal!
  amount0Out: BigDecimal!
  amount1Out: BigDecimal!
  
  # Price and fees
  priceImpact: BigDecimal!
  swapFee: BigDecimal!
  
  # User and gas
  user: Bytes!
  gasUsed: BigInt!
}
```

#### 2. Liquidity Pool Data
```graphql
type Pool {
  id: ID!
  asset0: Asset!
  asset1: Asset!
  
  # Reserves and liquidity
  reserve0: BigDecimal!
  reserve1: BigDecimal!
  totalLiquidity: BigDecimal!
  
  # Price and volume metrics
  asset0Price: BigDecimal!
  asset1Price: BigDecimal!
  volumeUSD24h: BigDecimal!
  
  # EulerSwap specific
  vault0: Vault!
  vault1: Vault!
  curve: CurveParameters!
  
  # Time-based data
  hourlyData: [PoolHourData!]!
  dailyData: [PoolDayData!]!
}
```

#### 3. Vault Integration Data
```graphql
type Vault {
  id: ID!
  asset: Asset!
  
  # Vault metrics
  totalSupply: BigDecimal!
  totalBorrow: BigDecimal!
  utilizationRate: BigDecimal!
  
  # Interest rates
  supplyRate: BigDecimal!
  borrowRate: BigDecimal!
  
  # EulerSwap integration
  poolsAsCollateral: [Pool!]!
  poolsAsBorrow: [Pool!]!
}
```

#### 4. Liquidity Position Data
```graphql
type LiquidityPosition {
  id: ID!
  user: Bytes!
  pool: Pool!
  
  # Position details
  liquidity: BigDecimal!
  token0Balance: BigDecimal!
  token1Balance: BigDecimal!
  
  # Borrowed amounts (for leverage)
  borrowed0: BigDecimal!
  borrowed1: BigDecimal!
  
  # Delta and risk metrics
  deltaExposure: BigDecimal!
  healthFactor: BigDecimal!
}
```

## Required GraphQL Queries

### 1. Historical Swap Data
```graphql
query GetSwapHistory($first: Int!, $skip: Int!, $startTime: BigInt!) {
  swaps(
    first: $first
    skip: $skip
    where: { timestamp_gte: $startTime }
    orderBy: timestamp
    orderDirection: asc
  ) {
    id
    timestamp
    blockNumber
    pool {
      id
      asset0 { symbol decimals }
      asset1 { symbol decimals }
    }
    amount0In
    amount1In
    amount0Out
    amount1Out
    priceImpact
    swapFee
    user
  }
}
```

### 2. Pool State Evolution
```graphql
query GetPoolHistory($poolId: String!, $startTime: BigInt!) {
  poolHourDatas(
    where: { 
      pool: $poolId
      periodStartUnix_gte: $startTime 
    }
    orderBy: periodStartUnix
    orderDirection: asc
  ) {
    periodStartUnix
    reserve0
    reserve1
    asset0Price
    asset1Price
    volumeUSD
    feesUSD
    utilizationRate0
    utilizationRate1
  }
}
```

### 3. Vault Interest Rates
```graphql
query GetVaultRates($asset: String!, $startTime: BigInt!) {
  vaultHourDatas(
    where: {
      vault_: { asset: $asset }
      periodStartUnix_gte: $startTime
    }
    orderBy: periodStartUnix
    orderDirection: asc
  ) {
    periodStartUnix
    supplyRate
    borrowRate
    utilizationRate
    totalSupply
    totalBorrow
  }
}
```

### 4. Liquidity Positions
```graphql
query GetLiquidityPositions($user: String!) {
  liquidityPositions(
    where: { user: $user }
  ) {
    id
    pool {
      id
      asset0 { symbol }
      asset1 { symbol }
    }
    liquidity
    token0Balance
    token1Balance
    borrowed0
    borrowed1
    deltaExposure
    healthFactor
    lastUpdated
  }
}
```

## Data Pipeline Implementation

### 1. Subgraph Client Setup
```python
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os

class EulerSubgraphClient:
    def __init__(self, api_key: str, subgraph_id: str):
        self.api_key = api_key
        self.endpoint = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"
        
        transport = AIOHTTPTransport(
            url=self.endpoint,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
    
    async def fetch_swaps(self, start_time: int, limit: int = 1000) -> list:
        query = gql("""
        query GetSwaps($startTime: BigInt!, $first: Int!) {
          swaps(
            first: $first
            where: { timestamp_gte: $startTime }
            orderBy: timestamp
            orderDirection: asc
          ) {
            id
            timestamp
            blockNumber
            # ... rest of fields
          }
        }
        """)
        
        result = await self.client.execute_async(
            query, 
            variable_values={"startTime": start_time, "first": limit}
        )
        return result["swaps"]
```

### 2. Data Processing Pipeline
```python
import pandas as pd
from typing import List, Dict

class EulerDataProcessor:
    def __init__(self):
        self.client = EulerSubgraphClient(
            api_key=os.getenv("THEGRAPH_API_KEY"),
            subgraph_id="7TKfCCjXaAeZSFaGh3ccir8JnQd1K4Rjq75G6KnVQnoP"  # Community subgraph
        )
    
    async def fetch_historical_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch and process historical data for backtesting"""
        start_time = int(pd.Timestamp(start_date).timestamp())
        end_time = int(pd.Timestamp(end_date).timestamp())
        
        # Fetch data in chunks to handle large time ranges
        all_swaps = []
        current_time = start_time
        
        while current_time < end_time:
            swaps = await self.client.fetch_swaps(current_time, limit=1000)
            if not swaps:
                break
                
            all_swaps.extend(swaps)
            current_time = int(swaps[-1]["timestamp"]) + 1
        
        # Convert to DataFrame
        df = pd.DataFrame(all_swaps)
        return self._process_swap_data(df)
    
    def _process_swap_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and enhance swap data"""
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Calculate derived metrics
        df['price_ratio'] = df['amount1Out'] / df['amount0In']
        df['swap_volume_usd'] = df['amount0In'] * df['asset0_price_usd']
        
        # Add technical indicators
        df['price_sma_1h'] = df['price_ratio'].rolling('1H').mean()
        df['volatility_1h'] = df['price_ratio'].rolling('1H').std()
        
        return df
```

### 3. Data Validation and Quality Checks
```python
class DataValidator:
    @staticmethod
    def validate_swap_data(df: pd.DataFrame) -> Dict[str, bool]:
        """Validate data quality for backtesting"""
        checks = {
            'no_missing_timestamps': df['timestamp'].isna().sum() == 0,
            'no_negative_amounts': (df[['amount0In', 'amount1In', 'amount0Out', 'amount1Out']] >= 0).all().all(),
            'reasonable_price_range': df['price_ratio'].between(0.001, 1000).all(),
            'sufficient_data_points': len(df) > 1000,
            'time_continuity': df['timestamp'].is_monotonic_increasing,
            'no_extreme_outliers': (df['price_ratio'] < df['price_ratio'].quantile(0.99) * 10).all()
        }
        
        return checks
    
    @staticmethod
    def generate_quality_report(df: pd.DataFrame) -> str:
        """Generate comprehensive data quality report"""
        checks = DataValidator.validate_swap_data(df)
        
        report = f"""
        Data Quality Report
        ==================
        Total Records: {len(df):,}
        Date Range: {df['datetime'].min()} to {df['datetime'].max()}
        Duration: {(df['datetime'].max() - df['datetime'].min()).days} days
        
        Quality Checks:
        """
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"  {check}: {status}\n"
        
        return report
```

## Data Storage Strategy

### 1. Parquet-based Storage
```python
import pyarrow as pa
import pyarrow.parquet as pq

class EulerDataStore:
    def __init__(self, base_path: str = "data/"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save_swap_data(self, df: pd.DataFrame, dataset_name: str):
        """Save swap data with compression and metadata"""
        file_path = self.base_path / "processed" / f"{dataset_name}_swaps.parquet"
        
        # Add metadata
        metadata = {
            'created_at': pd.Timestamp.now().isoformat(),
            'source': 'euler_subgraph',
            'record_count': str(len(df)),
            'date_range': f"{df['datetime'].min()} to {df['datetime'].max()}"
        }
        
        # Save with compression
        table = pa.Table.from_pandas(df)
        table = table.replace_schema_metadata(metadata)
        
        pq.write_table(table, file_path, compression='lz4')
    
    def load_swap_data(self, dataset_name: str) -> Tuple[pd.DataFrame, dict]:
        """Load swap data with metadata"""
        file_path = self.base_path / "processed" / f"{dataset_name}_swaps.parquet"
        
        table = pq.read_table(file_path)
        df = table.to_pandas()
        metadata = table.schema.metadata
        
        return df, metadata
```

## Data Requirements for Delta-Neutral Strategies

### Minimum Data Requirements
1. **6+ months** of historical data for robust backtesting
2. **1-hour or finer granularity** for intraday rebalancing analysis
3. **Complete price series** with no gaps longer than 4 hours
4. **Volume and liquidity data** for realistic transaction cost modeling
5. **Vault interest rates** for borrowing cost calculations

### Preferred Data Features
1. **Block-level precision** for exact ordering of transactions
2. **Gas cost data** for transaction cost modeling
3. **Liquidation events** for risk model calibration
4. **Pool parameter changes** for strategy adaptation
5. **Cross-asset correlation data** for portfolio risk analysis

### Data Quality Thresholds
- **Completeness**: > 95% of expected data points
- **Accuracy**: < 1% of records with obvious errors
- **Timeliness**: Data latency < 1 hour for recent periods
- **Consistency**: Price series without unexplained gaps
- **Volume**: Sufficient trading activity for realistic modeling

## Next Steps

1. **Subgraph Investigation**: Test both subgraphs to determine data availability
2. **Schema Discovery**: Use introspection to understand available entities
3. **Data Quality Assessment**: Run comprehensive data quality checks
4. **Optimization**: Implement efficient batch fetching and caching
5. **Monitoring**: Set up data pipeline monitoring and alerting

This data foundation will enable robust backtesting of delta-neutral LP strategies while maintaining transparency about data limitations and quality.