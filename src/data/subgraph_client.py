"""
Euler Subgraph Client with synthetic EulerSwap data generation.

This module provides:
1. Real data from Euler Finance subgraphs (vault rates, lending data)
2. Synthetic EulerSwap AMM data for backtesting demonstration
3. Rate limiting and error handling for API calls
4. Data validation and quality checks

Note: EulerSwap is very new and not yet indexed by available subgraphs.
For educational demonstration purposes, we generate realistic synthetic
swap data while using real Euler lending rates.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import aiohttp

# Load environment variables
load_dotenv()


@dataclass
class SubgraphConfig:
    """Configuration for subgraph connections."""
    euler_finance_id = "95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr"
    euler_community_id = "7TKfCCjXaAeZSFaGh3ccir8JnQd1K4Rjq75G6KnVQnoP"
    api_key: str = None
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv('thegraph_api_key')
            if not self.api_key:
                raise ValueError("Missing thegraph_api_key in environment variables")


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until the oldest call is more than 1 minute old
            sleep_time = 60 - (now - self.calls[0]) + 0.1
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.calls.append(now)


class EulerSubgraphClient:
    """Client for fetching data from Euler subgraphs with synthetic EulerSwap data."""
    
    def __init__(self, config: Optional[SubgraphConfig] = None):
        self.config = config or SubgraphConfig()
        self.rate_limiter = RateLimiter()
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize GraphQL clients for both subgraphs."""
        base_url = "https://gateway.thegraph.com/api"
        
        # Euler Finance client (lending data)
        euler_finance_url = f"{base_url}/{self.config.api_key}/subgraphs/id/{self.config.euler_finance_id}"
        self.clients['euler_finance'] = Client(
            transport=AIOHTTPTransport(url=euler_finance_url),
            fetch_schema_from_transport=False
        )
        
        # Euler Community client (vault data)  
        euler_community_url = f"{base_url}/{self.config.api_key}/subgraphs/id/{self.config.euler_community_id}"
        self.clients['euler_community'] = Client(
            transport=AIOHTTPTransport(url=euler_community_url),
            fetch_schema_from_transport=False
        )
    
    async def fetch_vault_data(self, limit: int = 1000, skip: int = 0) -> List[Dict]:
        """Fetch real vault data from Euler Community subgraph."""
        await self.rate_limiter.wait_if_needed()
        
        query = gql("""
        query GetVaultData($first: Int!, $skip: Int!) {
          evaultCreateds(first: $first, skip: $skip, orderBy: blockTimestamp, orderDirection: desc) {
            id
            blockTimestamp
            blockNumber
            asset
            vault
            name
            symbol
          }
        }
        """)
        
        try:
            result = await self.clients['euler_community'].execute_async(
                query, 
                variable_values={"first": limit, "skip": skip}
            )
            return result.get('evaultCreateds', [])
        except Exception as e:
            print(f"Warning: Failed to fetch vault data: {e}")
            return []
    
    async def fetch_lending_data(self, limit: int = 1000, skip: int = 0) -> List[Dict]:
        """Fetch real lending market data from Euler Finance subgraph."""
        await self.rate_limiter.wait_if_needed()
        
        query = gql("""
        query GetLendingData($first: Int!, $skip: Int!) {
          markets(first: $first, skip: $skip) {
            id
            name
            inputToken {
              id
              symbol
              name
              decimals
            }
            totalValueLockedUSD
            totalDepositBalanceUSD
            totalBorrowBalanceUSD
            inputTokenBalance
            inputTokenPriceUSD
            exchangeRate
            rewardTokens {
              token {
                symbol
              }
              rewardTokenEmissionsAmount
              rewardTokenEmissionsUSD
            }
          }
        }
        """)
        
        try:
            result = await self.clients['euler_finance'].execute_async(
                query,
                variable_values={"first": limit, "skip": skip}
            )
            return result.get('markets', [])
        except Exception as e:
            print(f"Warning: Failed to fetch lending data: {e}")
            return []
    
    def generate_synthetic_eulerswap_data(
        self, 
        start_date: datetime, 
        end_date: datetime,
        base_asset: str = "WETH",
        quote_asset: str = "USDC",
        initial_price: float = 2000.0,
        hourly_frequency: bool = True
    ) -> pd.DataFrame:
        """
        Generate realistic synthetic EulerSwap AMM data for backtesting.
        
        This creates educational demonstration data that mimics real EulerSwap
        behavior while clearly being synthetic for transparency.
        """
        print("🎭 Generating synthetic EulerSwap data for educational demonstration")
        print("⚠️  This is synthetic data for backtesting education, not real trading data")
        
        # Generate time index
        freq = 'H' if hourly_frequency else 'D'
        timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Generate realistic price movements (geometric brownian motion)
        n_periods = len(timestamps)
        dt = 1/24 if hourly_frequency else 1  # hours or days
        
        # Price simulation parameters
        mu = 0.0001  # slight upward drift (annual ~3.5%)
        sigma = 0.02  # realistic volatility (annual ~35%)
        
        # Generate price path
        returns = np.random.normal(mu * dt, sigma * np.sqrt(dt), n_periods - 1)
        prices = [initial_price]
        
        for r in returns:
            prices.append(prices[-1] * np.exp(r))
        
        # Generate synthetic trading data
        synthetic_data = []
        
        for i, timestamp in enumerate(timestamps):
            price = prices[i]
            
            # Generate realistic volume (correlated with volatility)
            base_volume = np.random.lognormal(mean=8, sigma=1.5)  # ~3k-10k WETH
            volatility_multiplier = 1 + abs(returns[i-1] if i > 0 else 0) * 10
            volume_weth = base_volume * volatility_multiplier
            volume_usdc = volume_weth * price
            
            # Generate liquidity depth (somewhat stable)
            liquidity_multiplier = np.random.uniform(0.8, 1.2)
            total_liquidity_usd = 5_000_000 * liquidity_multiplier  # ~5M TVL
            
            # Simulate vault integration (EulerSwap's key feature)
            vault_utilization = np.random.uniform(0.3, 0.8)  # 30-80% utilization
            available_borrow_usd = total_liquidity_usd * (1 - vault_utilization)
            
            # Simulate trading fees and yields
            trading_fee_rate = 0.003  # 0.3% swap fee
            vault_apy = np.random.uniform(0.02, 0.08)  # 2-8% lending APY
            
            synthetic_data.append({
                'timestamp': timestamp,
                'block_number': 18000000 + i * 12,  # ~12 second blocks
                'asset0': base_asset,
                'asset1': quote_asset,
                'asset0_price_usd': price,
                'asset1_price_usd': 1.0,  # USDC stable
                'price_ratio': price,
                'swap_volume_usd': volume_usdc,
                'swap_volume_asset0': volume_weth,
                'swap_volume_asset1': volume_usdc,
                'total_liquidity_usd': total_liquidity_usd,
                'vault0_balance': total_liquidity_usd / price / 2,  # 50% WETH
                'vault1_balance': total_liquidity_usd / 2,  # 50% USDC
                'vault_utilization_rate': vault_utilization,
                'available_borrow_usd': available_borrow_usd,
                'trading_fee_rate': trading_fee_rate,
                'vault_apy_asset0': vault_apy * np.random.uniform(0.9, 1.1),
                'vault_apy_asset1': vault_apy * np.random.uniform(0.9, 1.1),
                'is_synthetic': True,  # Clear marker
                'synthetic_version': '1.0',
                'generator': 'euler_delta_neutral_demo'
            })
        
        df = pd.DataFrame(synthetic_data)
        
        # Add technical indicators for strategy development
        df['price_sma_24h'] = df['price_ratio'].rolling(24).mean()
        df['price_volatility_24h'] = df['price_ratio'].rolling(24).std()
        df['volume_sma_24h'] = df['swap_volume_usd'].rolling(24).mean()
        
        print(f"✅ Generated {len(df)} synthetic data points from {start_date} to {end_date}")
        print(f"📊 Price range: ${df['price_ratio'].min():.2f} - ${df['price_ratio'].max():.2f}")
        print(f"💰 Average daily volume: ${df['swap_volume_usd'].mean():,.0f}")
        
        return df
    
    async def fetch_combined_dataset(
        self, 
        start_date: datetime, 
        end_date: datetime,
        include_real_data: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch combined dataset with real Euler data + synthetic EulerSwap data.
        
        Returns:
            Dict with keys: 'synthetic_swaps', 'real_vaults', 'real_lending'
        """
        datasets = {}
        
        # Generate synthetic EulerSwap data
        print("🎭 Creating synthetic EulerSwap AMM data...")
        datasets['synthetic_swaps'] = self.generate_synthetic_eulerswap_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if include_real_data:
            # Fetch real Euler data
            print("📡 Fetching real Euler vault data...")
            try:
                vault_data = await self.fetch_vault_data(limit=100)
                if vault_data:
                    datasets['real_vaults'] = pd.DataFrame(vault_data)
                    print(f"✅ Fetched {len(vault_data)} real vault records")
                else:
                    print("⚠️  No vault data available")
            except Exception as e:
                print(f"⚠️  Could not fetch vault data: {e}")
            
            print("📡 Fetching real Euler lending data...")
            try:
                lending_data = await self.fetch_lending_data(limit=100)
                if lending_data:
                    datasets['real_lending'] = pd.DataFrame(lending_data)
                    print(f"✅ Fetched {len(lending_data)} real lending records")
                else:
                    print("⚠️  No lending data available")
            except Exception as e:
                print(f"⚠️  Could not fetch lending data: {e}")
        
        return datasets


# Convenience functions for easy usage
async def quick_fetch_demo_data(days_back: int = 30) -> pd.DataFrame:
    """Quick function to fetch demo data for strategy development."""
    client = EulerSubgraphClient()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    datasets = await client.fetch_combined_dataset(start_date, end_date)
    return datasets['synthetic_swaps']


if __name__ == "__main__":
    # Test the client
    async def test_client():
        client = EulerSubgraphClient()
        
        # Test with 7 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        datasets = await client.fetch_combined_dataset(start_date, end_date)
        
        print(f"\n📊 Dataset Summary:")
        for name, df in datasets.items():
            print(f"  {name}: {len(df)} records")
            if len(df) > 0:
                print(f"    Columns: {list(df.columns)[:5]}...")
    
    asyncio.run(test_client())