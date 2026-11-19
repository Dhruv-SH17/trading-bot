import numpy as np
import pandas as pd
import pytest

from market_data import MarketData
from strategies import buy_and_hold, moving_average_crossover

SYMBOLS = ["AAA", "BBB", "CCC"]
STRATEGIES = [moving_average_crossover.MovingAverageCrossover(), buy_and_hold.BuyAndHold()]


def make_wavy_market(n_days: int = 800) -> MarketData:
    """Deterministic prices with long up and down swings, so the crossover trades."""
    dates = pd.date_range("2020-01-01", periods=n_days, freq="B")
    t = np.arange(n_days)
    closes = pd.DataFrame({
            symbol: 100 + 30 * np.sin(2 * np.pi * t / period)
            for symbol, period in zip(SYMBOLS, [300, 400, 500])
        },
        index=dates,
    )
    opens = closes.shift(1).fillna(closes)
    volume = pd.DataFrame(1_000.0, index=dates, columns=SYMBOLS)
    return MarketData(open=opens, high=closes, low=closes, close=closes, volume=volume)


@pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
@pytest.mark.parametrize("cutoff_position", [350, 600])
def test_weights_do_not_use_future_data(strategy, cutoff_position):
    market = make_wavy_market()
    cutoff = pd.Timestamp(market.close.index[cutoff_position]) # type: ignore

    full = strategy.weights(market)
    truncated = strategy.weights(market.up_to(cutoff)) 

    assert not truncated.empty, "test data produced no decisions before the cutoff"
    pd.testing.assert_frame_equal(full.loc[:cutoff], truncated, check_freq=False)