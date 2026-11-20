import pandas as pd

#PricesData is a new variable which can take in a DataFrame or Series. This is to fix typehint issues

def calculate_daily_returns[PricesData: (pd.DataFrame, pd.Series)](prices: PricesData) -> PricesData:
    """Simple daily returns (0.01 = +1%). The first row is NaN: it has no previous day."""
    return prices.pct_change(fill_method=None)


def calculate_sma[PricesData: (pd.DataFrame, pd.Series)](prices: PricesData, window: int) -> PricesData:
    """Simple moving average over the last `window` values, including the current one.

    The first `window - 1` rows are NaN: there isn't enough history yet.
    """
    
    return prices.rolling(window).mean()

def calculate_trailing_return[PricesData: (pd.DataFrame, pd.Series)](prices: PricesData,
                                                                      period: int,
                                                                      shift: int = 0) -> PricesData:
    """Calculates the trailing average for n days and an optional shift parameter.
    The period parameter determines how many days the change is calculated over.
    e.g passing 5 into the period parameter checks how much the price has changed from 5 days ago (for every date in the data)
    The shift parameter skips n number of the most recent days. e.g passing 5 into shift will skip the 5 most recent days.
    """
    if shift < 0:
        raise ValueError(f"Shift cannot be negative: {shift}")

    if period > prices.index.size:
        raise ValueError(f"The period is longer than the number of dates available: {period}")

    return prices.pct_change(period, fill_method=None).shift(shift)
