from typing import Protocol
import pandas as pd
from market_data import MarketData


class Strategy(Protocol):
    """
    A trading strategy decides what a portfolio should hold based on weights from 0-1.

    Timing: the strategy makes it's decisions after each day's close and makes any buy orders at the next day's opening price.
    This will naturally create some discrepancies between the last day's closing price and the current day's opening price.
    To protect against the portfolio going into a negative balance, 2% of the total portfolio value will be reserved for such situations.
    High, low and volume values are not look ahead.    
    """
    name: str

    def weights(self, data: MarketData) -> pd.DataFrame:
        """
        Returns a dataframe with all the trades that the strategy wants to execute for each day. 

        Rows: Decision dates (must be trading days in the data), Dates left out mean to hold for that day
        Columns: Same as the symbols in the data
        Values: >= 0. The entire row can add up to 1 at most; Leftover is cash.
        A row may be completely NaN meaning hold
        """

        return pd.DataFrame()