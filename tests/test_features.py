import math
import pandas as pd
import pytest

from features import calculate_daily_returns
from indicators import calculate_cagr


def test_calculate_daily_returns_match_hand_calc():
    prices = pd.Series([100.0, 110.0, 99.0])

    returns = calculate_daily_returns(prices)

    assert math.isnan(returns.iloc[0])
    assert returns.iloc[1] == pytest.approx(0.10)
    assert returns.iloc[2] == pytest.approx(-0.10)

def test_calculate_cagr():
    starting_date = pd.Timestamp("2022-01-01")
    ending_date = pd.Timestamp("2026-01-01")

    data = {
        starting_date: 100,
        ending_date: 146.41
    }

    equity = pd.Series(data)

    results = calculate_cagr(equity)

    assert results == pytest.approx(0.10)
