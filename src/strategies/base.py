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

    def target_weights(self, data: MarketData, current: pd.Series) -> pd.Series:
        """
        Return the target weight for each symbol. data: market data up to and including today.
        current: the current target weights for each symbol in the portfolio (0 if not held).
        Returning 'current' unchanged means: make no trades.
        """
        target = pd.Series([])
        

        return target