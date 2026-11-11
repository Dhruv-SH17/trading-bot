import pandas as pd
from market_data import MarketData


class BuyAndHold:
    """Buy and hold equally all symbols universe. Used as a benchmark."""

    name = "buy_and_hold"

    def weights(self, data: MarketData) -> pd.DataFrame:

        symbols = data.close.columns

        first_date = data.close.index[0]

        # Generates a dataframe with exactly one row with the first date as the index.
        # gives roughly a ~ 0.111 weight to each ticker (since the unvierse has 9 stocks currently.)
        return pd.DataFrame(1/len(symbols), index=[first_date], columns=symbols) 