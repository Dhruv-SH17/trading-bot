import numpy as np
import pandas as pd

from backtester import CostModel, run_backtest
from market_data import MarketData

SYMBOLS = ["AAA", "BBB", "CCC"]
NO_COSTS = CostModel(slippage=0.0, commission=0.0)


def make_flat_market(n_days: int, price: float = 100.0) -> MarketData:
    """Market where every open and close equals `price`, so nothing moves."""
    dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
    prices = pd.DataFrame(price, index=dates, columns=SYMBOLS)
    volume = pd.DataFrame(1_000.0, index=dates, columns=SYMBOLS)
    return MarketData(
        open=prices, high=prices, low=prices, close=prices, volume=volume
    )


def test_nan_weight_leaves_symbol_untouched():
    market = make_flat_market(n_days=4)
    dates = market.close.index

    # Day 0: buy all three. Day 1: sell AAA, leave BBB and CCC alone.
    weights = pd.DataFrame({
            "AAA": [0.3, 0.0],
            "BBB": [0.3, np.nan],
            "CCC": [0.3, np.nan],
        },
        index=dates[:2],
    )

    result = run_backtest(
        weights, market, initial_cash=10_000, costs=NO_COSTS, cash_buffer=0.02
    )

    after_buy = result.positions.iloc[1]   # day 0 decision filled at day 1 open
    after_sell = result.positions.iloc[2]  # day 1 decision filled at day 2 open

    assert after_buy["BBB"] > 0
    assert after_buy["CCC"] > 0
    assert after_sell["AAA"] == 0
    assert after_sell["BBB"] == after_buy["BBB"]
    assert after_sell["CCC"] == after_buy["CCC"]


def test_all_nan_row_means_hold():
    market = make_flat_market(n_days=4)
    dates = market.close.index

    # Day 0: buy all three. Day 1: no opinion on any symbol.
    weights = pd.DataFrame({
            "AAA": [0.3, np.nan],
            "BBB": [0.3, np.nan],
            "CCC": [0.3, np.nan],
        },
        index=dates[:2],
    )

    result = run_backtest(
        weights, market, initial_cash=10_000, costs=NO_COSTS, cash_buffer=0.02
    )

    pd.testing.assert_series_equal(
        result.positions.iloc[2], result.positions.iloc[1], check_names=False
    )