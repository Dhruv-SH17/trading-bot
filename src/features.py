import pandas as pd


#PricesData is a new variable which can take in a DataFrame or Series. This is to fix typehint issues

def calculate_daily_returns [PricesData: (pd.DataFrame, pd.Series)] (prices: PricesData) -> PricesData:
    """Simple daily returns (0.01 = +1%). The first row is NaN: it has no previous day."""
    return prices.pct_change(fill_method=None)
