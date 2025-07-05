# Technical Architecture

## System Architecture Overview

The Euler Delta-Neutral LP Strategy project is built using a modern data science stack optimized for quantitative finance research and development. The architecture emphasizes reproducibility, performance, and educational clarity.

## Technology Stack

### Core Environment: Anaconda Python 3.11
**Why Anaconda?**
- **Dependency Management**: Superior handling of complex scientific computing dependencies
- **Pre-compiled Packages**: Faster installation and better optimization (Intel MKL, etc.)
- **Environment Isolation**: Clean separation from system Python
- **Cross-platform Support**: Consistent experience across macOS, Windows, Linux
- **Scientific Computing Focus**: Optimized for data science and quantitative analysis

### Key Libraries and Their Roles

#### Data Processing & Analysis
```python
# Core data manipulation
pandas==2.1.0           # Time series analysis and data frames
numpy==1.24.0           # Numerical computing and linear algebra
pyarrow==13.0.0         # Fast columnar data format (Parquet)
fastparquet==2023.8.0   # High-performance Parquet I/O

# Statistical analysis
scipy==1.11.0           # Statistical functions and optimization
statsmodels==0.14.0     # Econometric analysis and time series
```

#### Backtesting & Optimization
```python
# High-performance backtesting
vectorbt==0.25.0        # Vectorized backtesting framework
numba==0.57.0           # JIT compilation for numerical code
bottleneck==1.3.7       # Fast NumPy array functions

# Hyperparameter optimization
optuna==3.3.0           # Bayesian optimization
scikit-optimize==0.9.0  # Alternative optimization algorithms
```

#### Visualization & Reporting
```python
# Interactive plotting
plotly==5.17.0          # Interactive web-based charts
matplotlib==3.7.0       # Publication-quality static plots
seaborn==0.12.0         # Statistical visualization

# Jupyter ecosystem
jupyterlab==4.0.0       # Interactive development environment
ipywidgets==8.1.0       # Interactive notebook widgets
```

#### Data Acquisition
```python
# GraphQL and API integration
requests==2.31.0        # HTTP requests for API calls
gql==3.4.1             # GraphQL client for subgraph queries
aiohttp==3.8.6         # Async HTTP for concurrent requests
python-dotenv==1.0.0   # Environment variable management
```

## Project Structure Design

### Directory Organization
```
euler-delta-neutral/
├── environment.yml              # Conda environment specification
├── requirements.txt             # Additional pip packages
├── .env                        # Environment variables (gitignored)
├── .gitignore                  # Git ignore rules
├── CLAUDE.md                   # Claude development guidelines
├── README.md                   # Project overview and setup
│
├── notebooks/                  # Interactive Jupyter notebooks
│   ├── 01_data_exploration.ipynb      # Subgraph analysis
│   ├── 02_data_pipeline.ipynb         # Data fetching and processing
│   ├── 03_strategy_development.ipynb  # Strategy implementation
│   ├── 04_backtesting_engine.ipynb    # Performance analysis
│   ├── 05_optimization.ipynb          # Hyperparameter tuning
│   └── 06_results_dashboard.ipynb     # Final results and visualization
│
├── src/                        # Reusable Python modules
│   ├── __init__.py
│   ├── data/                   # Data acquisition and processing
│   │   ├── __init__.py
│   │   ├── subgraph_client.py  # GraphQL client for The Graph
│   │   ├── data_loader.py      # Parquet data loading utilities
│   │   └── preprocessor.py     # Data cleaning and feature engineering
│   │
│   ├── strategy/               # Strategy implementation
│   │   ├── __init__.py
│   │   ├── delta_neutral.py    # Core delta-neutral logic
│   │   ├── rebalancer.py       # Position rebalancing algorithms
│   │   └── risk_manager.py     # Risk management utilities
│   │
│   ├── backtesting/            # Backtesting framework
│   │   ├── __init__.py
│   │   ├── engine.py           # VectorBT integration
│   │   ├── metrics.py          # Performance metrics calculation
│   │   └── attribution.py     # Return attribution analysis
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── config.py           # Configuration management
│       ├── plotting.py         # Standardized plotting functions
│       └── validation.py       # Data validation utilities
│
├── data/                       # Data storage (gitignored)
│   ├── raw/                    # Raw subgraph data
│   ├── processed/              # Cleaned and processed data
│   ├── cache/                  # Cached API responses
│   └── features/               # Engineered features
│
├── config/                     # Configuration files
│   ├── strategy_params.yml     # Strategy parameter defaults
│   ├── optimization_config.yml # Optuna optimization settings
│   └── data_sources.yml        # Subgraph endpoints and queries
│
├── results/                    # Generated outputs (gitignored)
│   ├── backtests/              # Backtest results
│   ├── optimizations/          # Hyperparameter optimization results
│   ├── plots/                  # Generated charts and figures
│   └── reports/                # Summary reports
│
├── docs/                       # Documentation
│   ├── project-overview.md
│   ├── technical-architecture.md
│   ├── data-sources.md
│   └── api-reference.md
│
└── plans/                      # Implementation plans
    └── delta-neutral-backtesting-strategy.md
```

### Design Principles

#### 1. Separation of Concerns
- **Notebooks**: Interactive exploration and presentation
- **Source Code**: Reusable, tested, production-ready modules
- **Configuration**: Externalized parameters and settings
- **Data**: Isolated storage with clear data lineage

#### 2. Reproducibility
- **Environment Management**: Conda environment.yml for exact replication
- **Deterministic Seeds**: Fixed random seeds for consistent results
- **Version Control**: All code and configuration under git
- **Documentation**: Comprehensive inline and external documentation

#### 3. Performance Optimization
- **Vectorized Operations**: Leverage NumPy and VectorBT for speed
- **Efficient Storage**: Parquet format for fast I/O
- **Caching**: Strategic caching of expensive computations
- **Memory Management**: Careful handling of large datasets

#### 4. Educational Clarity
- **Progressive Complexity**: Notebooks build from simple to advanced
- **Inline Documentation**: Extensive comments and docstrings
- **Visual Explanations**: Charts and plots to illustrate concepts
- **Clear Limitations**: Explicit discussion of assumptions and risks

## Data Architecture

### Data Flow Pipeline
```
The Graph Subgraphs → GraphQL Queries → Raw JSON → Pandas DataFrames → Parquet Files → Analysis
```

#### Stage 1: Data Acquisition
```python
# Subgraph client with rate limiting and error handling
class SubgraphClient:
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.session = self._create_session()
    
    async def fetch_euler_data(self, query: str, variables: dict) -> dict:
        """Fetch data with retries and error handling"""
        # Implementation with exponential backoff
```

#### Stage 2: Data Processing
```python
# Data preprocessor with validation
class EulerDataProcessor:
    def process_swap_data(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw subgraph data to structured format"""
        # Data validation, cleaning, and feature engineering
    
    def calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators and risk metrics"""
        # Delta calculations, volatility measures, etc.
```

#### Stage 3: Data Storage
```python
# Efficient storage with metadata
class DataStore:
    def save_dataset(self, df: pd.DataFrame, name: str, metadata: dict):
        """Save with compression and metadata"""
        # Parquet with lz4 compression, metadata in separate JSON
    
    def load_dataset(self, name: str) -> Tuple[pd.DataFrame, dict]:
        """Load with automatic type inference"""
        # Fast loading with proper data types
```

### Data Schema Design

#### Core Data Schema
```python
EulerSwapData = {
    # Time and block information
    'timestamp': 'datetime64[ns]',
    'block_number': 'int64',
    'transaction_hash': 'string',
    
    # Asset and pool information
    'pool_address': 'string',
    'asset0_address': 'string',
    'asset1_address': 'string',
    'asset0_symbol': 'string',
    'asset1_symbol': 'string',
    
    # Price and volume data
    'asset0_price_usd': 'float64',
    'asset1_price_usd': 'float64',
    'swap_volume_usd': 'float64',
    'total_liquidity_usd': 'float64',
    
    # Vault-specific data
    'vault0_balance': 'float64',
    'vault1_balance': 'float64',
    'borrow_rate_0': 'float64',
    'borrow_rate_1': 'float64',
    
    # Derived features
    'price_ratio': 'float64',
    'volatility_1h': 'float64',
    'volatility_24h': 'float64',
    'delta_exposure': 'float64'
}
```

## Strategy Architecture

### Core Strategy Framework
```python
class DeltaNeutralStrategy:
    """Base class for delta-neutral LP strategies"""
    
    def __init__(self, params: StrategyParams):
        self.params = params
        self.position = Position()
        self.risk_manager = RiskManager(params.risk_limits)
    
    def calculate_delta(self, market_data: MarketData) -> float:
        """Calculate current delta exposure"""
        # Implementation depends on specific LP position
    
    def generate_signals(self, market_data: MarketData) -> List[Signal]:
        """Generate rebalancing signals"""
        delta = self.calculate_delta(market_data)
        
        if abs(delta) > self.params.delta_threshold:
            return self._create_hedge_signals(delta)
        return []
    
    def execute_rebalance(self, signals: List[Signal]) -> List[Transaction]:
        """Execute rebalancing transactions"""
        # Apply risk management and position sizing
```

### VectorBT Integration
```python
class VectorBTBacktester:
    """High-performance backtesting using VectorBT"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.price_data = self._prepare_price_data()
    
    def run_backtest(self, strategy: DeltaNeutralStrategy) -> BacktestResults:
        """Run vectorized backtest"""
        # Generate all signals at once
        signals = strategy.generate_all_signals(self.data)
        
        # Vectorized execution
        portfolio = vbt.Portfolio.from_signals(
            close=self.price_data,
            entries=signals.entries,
            exits=signals.exits,
            **strategy.params.to_dict()
        )
        
        return BacktestResults(portfolio)
```

## Optimization Architecture

### Hyperparameter Optimization with Optuna
```python
class StrategyOptimizer:
    """Bayesian optimization of strategy parameters"""
    
    def __init__(self, data: pd.DataFrame, strategy_class: Type[DeltaNeutralStrategy]):
        self.data = data
        self.strategy_class = strategy_class
        self.study = None
    
    def objective(self, trial: optuna.Trial) -> float:
        """Optimization objective function"""
        # Sample parameters from search space
        params = self._sample_parameters(trial)
        
        # Run backtest with these parameters
        strategy = self.strategy_class(params)
        results = self.run_backtest(strategy)
        
        # Return objective (e.g., Sharpe ratio)
        return results.sharpe_ratio
    
    def optimize(self, n_trials: int = 500) -> StrategyParams:
        """Run Bayesian optimization"""
        self.study = optuna.create_study(direction='maximize')
        self.study.optimize(self.objective, n_trials=n_trials)
        
        return StrategyParams.from_dict(self.study.best_params)
```

### Multi-Objective Optimization
```python
class MultiObjectiveOptimizer:
    """Optimize for multiple objectives simultaneously"""
    
    def objective(self, trial: optuna.Trial) -> Tuple[float, float, float]:
        """Multi-objective function"""
        params = self._sample_parameters(trial)
        results = self.run_backtest(params)
        
        return (
            results.sharpe_ratio,      # Maximize
            -results.max_drawdown,     # Minimize (negative for maximization)
            -results.transaction_costs # Minimize transaction costs
        )
```

## Performance and Scalability

### Computational Optimization
1. **Vectorized Operations**: Use NumPy and VectorBT for array operations
2. **JIT Compilation**: Numba for critical numerical code
3. **Parallel Processing**: Multiprocessing for parameter sweeps
4. **Memory Management**: Efficient data types and chunked processing
5. **Caching**: Redis or disk-based caching for expensive computations

### Data Efficiency
1. **Columnar Storage**: Parquet for fast I/O and compression
2. **Type Optimization**: Appropriate data types to minimize memory
3. **Lazy Loading**: Load only necessary data for each analysis
4. **Incremental Updates**: Only fetch new data since last update

### Development Workflow
1. **Interactive Development**: Jupyter notebooks for exploration
2. **Module Testing**: Unit tests for core modules
3. **Performance Profiling**: Regular performance monitoring
4. **Documentation**: Automated API documentation generation

This architecture provides a solid foundation for developing, testing, and optimizing delta-neutral LP strategies while maintaining code quality, performance, and educational value.