import pandas as pd


def calculate_daily_returns (prices: pd.DataFrame) -> pd.DataFrame:
    """Simple daily returns (0.01 = +1%). The first row is NaN: it has no previous day."""
    return prices.pct_change(fill_method=None)
