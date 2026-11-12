import math
import pandas as pd
import pytest

from features import calculate_daily_returns


def test_calculate_daily_returns_match_hand_calc():
    prices = pd.Series([100.0, 110.0, 99.0])

    returns = calculate_daily_returns(prices)

    assert math.isnan(returns.iloc[0])
    assert returns.iloc[1] == pytest.approx(0.10)
    assert returns.iloc[2] == pytest.approx(-0.10)