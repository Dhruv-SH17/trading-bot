import pandas as pd
from strategies.moving_average_crossover import MovingAverageCrossover
from market_data import MarketData


def test_holdings_buy_stop_cooldown_reentry_sell():
    dates = pd.bdate_range("2024-01-01", periods=10)
    opens = pd.Series([100, 100, 102, 101, 97, 96, 95, 96, 99, 100], index=dates)
    closes = pd.Series([100, 101, 101, 97, 96, 95, 96, 99, 100, 99], index=dates)
    buy = pd.Series([False, True, True, True, True, True, True, True, False, False], index=dates)
    sell = pd.Series([False, False, False, False, False, False, False, False, False, True], index=dates)


    strategy = MovingAverageCrossover(cooldown_days=2)

    result = strategy._holdings_for_symbol(opens, closes, buy, sell)
    expected = pd.Series([False, True, True, True, True, False, False, True, True, False], index=dates)

    pd.testing.assert_series_equal(result, expected)
    assert list(result) == [False, True, True, True, True, False, False, True, True, False]