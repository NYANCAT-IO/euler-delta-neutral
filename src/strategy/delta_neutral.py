"""
Delta-Neutral LP Strategy Core Logic (≤50 lines)

Ultra-simple delta-neutral rebalancing strategy for EulerSwap LP positions.
This is the core algorithm that determines when and how to rebalance positions
to maintain delta neutrality while leveraging Euler's vault borrowing capabilities.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class StrategyParams:
    """Strategy hyperparameters for optimization."""

    delta_threshold: float = 0.1  # Rebalance when |delta| > threshold
    hedge_ratio: float = 1.0  # How much to hedge (1.0 = full hedge)
    max_position_size: float = 1000000  # Maximum position size in USD
    stop_loss: float = 0.15  # Stop loss level (15%)
    rebalance_cooldown: int = 6  # Hours between rebalances
    min_liquidity_ratio: float = 0.1  # Minimum available liquidity ratio


@dataclass
class RebalanceSignal:
    """Signal output from strategy."""

    action: str  # 'borrow_asset0', 'borrow_asset1', 'hold', 'stop_loss'
    amount_usd: float  # Amount to borrow/trade in USD
    confidence: float  # Signal confidence (0-1)
    reason: str  # Human readable reason


def calculate_position_delta(price_current: float, price_initial: float) -> float:
    """Calculate delta exposure for constant product AMM LP position."""
    price_ratio = price_current / price_initial
    return 0.5 * (1 - np.sqrt(price_ratio))


def delta_neutral_rebalance(
    current_price: float,
    initial_price: float,
    market_data: dict[str, Any],
    params: StrategyParams,
    position_state: dict[str, Any] = None,
) -> RebalanceSignal:
    """
    Core delta-neutral rebalancing logic (≤50 lines).

    Args:
        current_price: Current asset price
        initial_price: LP position entry price
        market_data: Dict with liquidity, volume, etc.
        params: Strategy parameters
        position_state: Current position state

    Returns:
        RebalanceSignal with action and amount
    """
    # Initialize position state if not provided
    if position_state is None:
        position_state = {"last_rebalance": 0, "current_hedge": 0, "pnl": 0}

    # Calculate current delta exposure of LP position
    delta = calculate_position_delta(current_price, initial_price)

    # Check rebalancing cooldown
    if position_state["last_rebalance"] < params.rebalance_cooldown:
        return RebalanceSignal("hold", 0, 0.1, "cooldown_period")

    # Calculate unrealized PnL for stop-loss
    price_change = (current_price / initial_price) - 1
    if abs(price_change) > params.stop_loss:
        return RebalanceSignal(
            "stop_loss", 0, 0.9, f"stop_loss_triggered_{price_change:.2%}"
        )

    # Check if rebalancing is needed
    if abs(delta) <= params.delta_threshold:
        return RebalanceSignal("hold", 0, 0.3, f"delta_within_threshold_{delta:.3f}")

    # Calculate required hedge amount
    hedge_amount_ratio = -delta * params.hedge_ratio  # Opposite sign to neutralize

    # Determine action based on hedge direction
    if hedge_amount_ratio > 0:
        action = "borrow_asset1"  # Borrow quote asset (USDC)
        base_amount = (
            market_data.get("total_liquidity_usd", 1000000) * 0.5
        )  # 50% of pool
        hedge_amount_usd = base_amount * abs(hedge_amount_ratio)
    else:
        action = "borrow_asset0"  # Borrow base asset (WETH)
        base_amount = (
            market_data.get("total_liquidity_usd", 1000000) * 0.5
        )  # 50% of pool
        hedge_amount_usd = base_amount * abs(hedge_amount_ratio)

    # Apply position sizing limits
    hedge_amount_usd = min(hedge_amount_usd, params.max_position_size)

    # Check available liquidity in Euler vaults
    available_liquidity = market_data.get("available_borrow_usd", hedge_amount_usd)
    if hedge_amount_usd > available_liquidity * 0.9:  # Don't use >90% of available
        hedge_amount_usd = available_liquidity * 0.9
        if hedge_amount_usd < 1000:  # Minimum viable trade size
            return RebalanceSignal("hold", 0, 0.2, "insufficient_liquidity")

    # Calculate confidence based on delta magnitude and market conditions
    confidence = min(0.9, abs(delta) / params.delta_threshold * 0.5 + 0.3)

    # Adjust for market volatility
    volatility = market_data.get("price_volatility_24h", 0.02)
    if volatility > 0.05:  # High volatility - reduce confidence
        confidence *= 0.8

    return RebalanceSignal(
        action=action,
        amount_usd=hedge_amount_usd,
        confidence=confidence,
        reason=f"delta_hedge_required_{delta:.3f}",
    )


class DeltaNeutralStrategy:
    """Strategy class for backtesting integration."""

    def __init__(self, params: StrategyParams = None):
        self.params = params or StrategyParams()
        self.position_state = {"last_rebalance": 0, "current_hedge": 0, "pnl": 0}
        self.trade_history = []

    def generate_signals(self, data: pd.DataFrame) -> list[RebalanceSignal]:
        """Generate rebalancing signals for entire dataset."""
        signals = []
        initial_price = (
            data["price_ratio"].iloc[0]
            if "price_ratio" in data.columns
            else data["asset0_price_usd"].iloc[0]
        )

        for idx, row in data.iterrows():
            current_price = row.get(
                "price_ratio", row.get("asset0_price_usd", initial_price)
            )

            market_data = {
                "total_liquidity_usd": row.get("total_liquidity_usd", 1000000),
                "available_borrow_usd": row.get("available_borrow_usd", 500000),
                "price_volatility_24h": row.get("price_volatility_24h", 0.02),
                "swap_volume_usd": row.get("swap_volume_usd", 10000),
            }

            signal = delta_neutral_rebalance(
                current_price=current_price,
                initial_price=initial_price,
                market_data=market_data,
                params=self.params,
                position_state=self.position_state,
            )

            signals.append(signal)

            # Update position state
            if signal.action != "hold":
                self.position_state["last_rebalance"] = 0
                if signal.action in ["borrow_asset0", "borrow_asset1"]:
                    self.position_state["current_hedge"] += signal.amount_usd
            else:
                self.position_state["last_rebalance"] += 1

        return signals
