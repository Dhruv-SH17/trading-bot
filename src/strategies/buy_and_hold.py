import pandas as pd
from market_data import MarketData


class BuyAndHold:
    """Buy and hold equally all symbols universe. Used as a benchmark."""

    name = "buy_and_hold"

    def target_weights(self, data: MarketData, current: pd.Series) -> pd.Series:

        if current.sum() > 0:
            return current  # means we are already invested

        symbols = data.close.columns

        return pd.Series(1/len(symbols), index=symbols) # gives roughly a ~ 0.111 weight to each ticker (since the unvierse has 9 stocks currently.)