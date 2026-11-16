import pandas as pd
import pytest

from market_data import MarketData
from backtester import CostModel, run_backtest
from strategies.buy_and_hold import BuyAndHold


def build_market_data(opens: pd.DataFrame, closes: pd.DataFrame) -> MarketData:
    """Test helper. This function just """
    return MarketData(opens, closes, closes, closes, closes)

def test_final_equity_matches_hand_calculation():

    dates = pd.bdate_range("2024-01-01", periods=4)
    opens = pd.DataFrame({"A": [100, 101, 103, 99], "B": [40, 44, 45, 42]}, index=dates)
    closes = pd.DataFrame({"A": [102, 102, 101, 98], "B": [42, 44, 43, 42]}, index=dates)
    market = build_market_data(opens, closes)
    weights = BuyAndHold().weights(market)

    result = run_backtest(weights, market, 10_000, CostModel(slippage=0.0, commission=0.0), cash_buffer=0)

    assert result.equity.iloc[-1] == pytest.approx(9621.99)