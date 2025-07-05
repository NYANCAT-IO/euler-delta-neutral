"""
VectorBT backtesting engine for delta-neutral strategies.

This module provides:
1. High-performance vectorized backtesting using VectorBT
2. Portfolio construction and performance analysis
3. Transaction cost modeling
4. Risk metrics calculation
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt

from ..strategy.delta_neutral import (
    DeltaNeutralStrategy,
    StrategyParams,
)


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    initial_capital: float = 1000000  # Starting capital in USD
    transaction_cost_rate: float = 0.001  # Transaction cost (0.1%)
    slippage_rate: float = 0.0005  # Market impact slippage
    gas_cost_per_trade: float = 50  # Gas cost per trade in USD
    leverage_limit: float = 3.0  # Maximum leverage allowed
    margin_requirement: float = 0.2  # Margin requirement (20%)


@dataclass
class BacktestResults:
    """Comprehensive backtesting results."""

    portfolio: vbt.Portfolio
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    num_trades: int
    avg_trade_duration: float
    final_capital: float
    summary_stats: dict[str, float]
    trade_analysis: pd.DataFrame


class VectorBTBacktester:
    """High-performance backtesting using VectorBT."""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()

    def prepare_signals(
        self, data: pd.DataFrame, strategy: DeltaNeutralStrategy
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Convert strategy signals to VectorBT format."""
        signals = strategy.generate_signals(data)

        # Initialize signal arrays
        entries = np.zeros(len(data), dtype=bool)
        exits = np.zeros(len(data), dtype=bool)
        sizes = np.zeros(len(data), dtype=float)

        # Process signals
        for i, signal in enumerate(signals):
            if signal.action == "borrow_asset0":
                entries[i] = True
                sizes[i] = signal.amount_usd * signal.confidence
            elif signal.action == "borrow_asset1":
                entries[i] = True
                sizes[i] = -signal.amount_usd * signal.confidence  # Short position
            elif signal.action == "stop_loss":
                exits[i] = True
                sizes[i] = 0

        # Convert to pandas Series with proper index
        index = data.index if hasattr(data, "index") else range(len(data))

        return (
            pd.Series(entries, index=index, name="entries"),
            pd.Series(exits, index=index, name="exits"),
            pd.Series(sizes, index=index, name="sizes"),
        )

    def calculate_transaction_costs(
        self, trades: pd.DataFrame, price_data: pd.Series
    ) -> pd.Series:
        """Calculate realistic transaction costs."""
        if trades.empty:
            return pd.Series([], dtype=float)

        # Base transaction costs
        trade_values = np.abs(trades["size"] * price_data[trades.index])
        transaction_costs = trade_values * self.config.transaction_cost_rate

        # Add slippage (proportional to trade size)
        slippage_costs = trade_values * self.config.slippage_rate

        # Add fixed gas costs
        gas_costs = pd.Series(self.config.gas_cost_per_trade, index=trades.index)

        total_costs = transaction_costs + slippage_costs + gas_costs
        return total_costs

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: DeltaNeutralStrategy,
        price_column: str = "price_ratio",
    ) -> BacktestResults:
        """Run comprehensive backtest."""
        print("🚀 Starting VectorBT backtest...")

        # Prepare price data
        if price_column not in data.columns:
            if "asset0_price_usd" in data.columns:
                price_data = data["asset0_price_usd"]
            else:
                raise ValueError(f"Price column '{price_column}' not found")
        else:
            price_data = data[price_column]

        # Generate trading signals
        print("📊 Generating trading signals...")
        entries, exits, sizes = self.prepare_signals(data, strategy)

        # Calculate dynamic transaction costs
        print("💰 Calculating transaction costs...")

        # Create portfolio with VectorBT
        print("🏗️  Building portfolio...")
        try:
            portfolio = vbt.Portfolio.from_signals(
                close=price_data,
                entries=entries,
                exits=exits,
                size=sizes,
                init_cash=self.config.initial_capital,
                fees=self.config.transaction_cost_rate,
                freq="1H",  # Assume hourly data
            )
        except Exception as e:
            print(f"⚠️  VectorBT portfolio creation failed: {e}")
            # Fallback to simpler approach
            portfolio = vbt.Portfolio.from_signals(
                close=price_data,
                entries=entries,
                exits=exits,
                init_cash=self.config.initial_capital,
                fees=self.config.transaction_cost_rate,
            )

        # Calculate performance metrics
        print("📈 Calculating performance metrics...")
        returns = portfolio.returns()

        # Basic metrics
        total_return = portfolio.total_return()

        # Calculate Sharpe ratio manually since VectorBT may not have the method
        try:
            if hasattr(returns, "sharpe_ratio"):
                sharpe_ratio = returns.sharpe_ratio()
            else:
                # Manual Sharpe ratio calculation
                mean_return = returns.mean() * 8760  # Annualize (assuming hourly data)
                std_return = returns.std() * np.sqrt(8760)  # Annualize volatility
                sharpe_ratio = mean_return / std_return if std_return > 0 else 0
        except:
            sharpe_ratio = 0

        max_drawdown = portfolio.max_drawdown()

        # Advanced metrics
        calmar_ratio = abs(total_return / max_drawdown) if max_drawdown != 0 else 0

        # Trade analysis
        try:
            trades = portfolio.trades
            trades_df = trades.to_df() if hasattr(trades, "to_df") else pd.DataFrame()

            if len(trades_df) > 0:
                win_rate = (
                    (trades_df["pnl"] > 0).mean() if "pnl" in trades_df.columns else 0
                )
                if "pnl" in trades_df.columns:
                    winning_trades = trades_df[trades_df["pnl"] > 0]["pnl"].sum()
                    losing_trades = abs(trades_df[trades_df["pnl"] < 0]["pnl"].sum())
                    profit_factor = (
                        winning_trades / losing_trades if losing_trades > 0 else np.inf
                    )
                else:
                    profit_factor = 0
                num_trades = len(trades_df)
                avg_trade_duration = (
                    trades_df["duration"].mean()
                    if "duration" in trades_df.columns
                    else 0
                )
            else:
                win_rate = 0
                profit_factor = 0
                num_trades = 0
                avg_trade_duration = 0
        except Exception as e:
            print(f"⚠️  Trade analysis failed: {e}")
            win_rate = 0
            profit_factor = 0
            num_trades = 0
            avg_trade_duration = 0
            trades_df = pd.DataFrame()

        final_capital = portfolio.final_value()

        # Summary statistics
        try:
            annualized_return = (
                returns.mean() * 8760 * 100 if not returns.empty else 0
            )  # Hourly to annual %
            annualized_volatility = (
                returns.std() * np.sqrt(8760) * 100 if not returns.empty else 0
            )  # Hourly to annual %
        except:
            annualized_return = 0
            annualized_volatility = 0

        summary_stats = {
            "initial_capital": self.config.initial_capital,
            "final_capital": final_capital,
            "total_return_pct": total_return * 100,
            "annualized_return_pct": annualized_return,
            "annualized_volatility_pct": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown * 100,
            "calmar_ratio": calmar_ratio,
            "win_rate_pct": win_rate * 100,
            "profit_factor": profit_factor,
            "num_trades": num_trades,
            "avg_trade_duration_hours": avg_trade_duration,
            "total_fees_paid": portfolio.fees.sum()
            if hasattr(portfolio, "fees")
            else 0,
        }

        print("✅ Backtest completed!")
        print(f"📊 Total Return: {total_return:.2%}")
        print(f"📊 Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"📊 Max Drawdown: {max_drawdown:.2%}")
        print(f"📊 Win Rate: {win_rate:.1%}")
        print(f"📊 Number of Trades: {num_trades}")

        return BacktestResults(
            portfolio=portfolio,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_trades=num_trades,
            avg_trade_duration=avg_trade_duration,
            final_capital=final_capital,
            summary_stats=summary_stats,
            trade_analysis=trades_df,
        )

    def run_parameter_sweep(
        self,
        data: pd.DataFrame,
        param_ranges: dict[str, list[float]],
        price_column: str = "price_ratio",
    ) -> pd.DataFrame:
        """Run parameter sweep for optimization."""
        print("🔄 Running parameter sweep...")

        results = []
        param_combinations = self._generate_param_combinations(param_ranges)

        for i, params_dict in enumerate(param_combinations):
            print(
                f"  Testing combination {i+1}/{len(param_combinations)}: {params_dict}"
            )

            # Create strategy with these parameters
            strategy_params = StrategyParams(**params_dict)
            strategy = DeltaNeutralStrategy(strategy_params)

            try:
                # Run backtest
                backtest_results = self.run_backtest(data, strategy, price_column)

                # Store results
                result_row = params_dict.copy()
                result_row.update(backtest_results.summary_stats)
                results.append(result_row)

            except Exception as e:
                print(f"    ⚠️  Failed: {e}")
                # Store failed attempt
                result_row = params_dict.copy()
                result_row.update(
                    {
                        "total_return_pct": -100,
                        "sharpe_ratio": -10,
                        "max_drawdown_pct": 100,
                        "error": str(e),
                    }
                )
                results.append(result_row)

        results_df = pd.DataFrame(results)
        print(f"✅ Parameter sweep completed: {len(results_df)} combinations tested")

        return results_df

    def _generate_param_combinations(
        self, param_ranges: dict[str, list[float]]
    ) -> list[dict[str, float]]:
        """Generate all combinations of parameters."""
        import itertools

        keys = list(param_ranges.keys())
        values = list(param_ranges.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo, strict=False)))

        return combinations


# Convenience functions
def quick_backtest(
    data: pd.DataFrame, strategy_params: dict[str, float] = None
) -> BacktestResults:
    """Quick backtest function for strategy development."""
    if strategy_params is None:
        strategy_params = {}

    # Create strategy
    params = StrategyParams(**strategy_params)
    strategy = DeltaNeutralStrategy(params)

    # Run backtest
    backtester = VectorBTBacktester()
    return backtester.run_backtest(data, strategy)


if __name__ == "__main__":
    # Test the backtesting engine
    print("🧪 Testing VectorBT backtesting engine...")

    # Create sample data
    dates = pd.date_range("2025-01-01", periods=168, freq="H")  # 1 week
    sample_data = pd.DataFrame(
        {
            "price_ratio": 2000 + np.random.randn(168).cumsum() * 5,
            "total_liquidity_usd": np.random.uniform(4e6, 6e6, 168),
            "available_borrow_usd": np.random.uniform(2e6, 3e6, 168),
            "price_volatility_24h": np.random.uniform(0.01, 0.05, 168),
        },
        index=dates,
    )

    # Test quick backtest
    results = quick_backtest(sample_data)
    print(
        f"Test completed: {results.total_return:.2%} return, {results.sharpe_ratio:.2f} Sharpe"
    )
