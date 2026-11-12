import pandas as pd
from market_data import MarketData
from dataclasses import dataclass


@dataclass(frozen=True)
class MovingAverageCrossover:
    """Moving-average crossover strategy with a stop-loss and re-entry cooldown.

    Buy signal: If the 50 day SMA (simple moving average) is at least 1% higher
    than the 200 day SMA for 3 consecutive days.
    
    How much to buy: Instead of using risk-based sizing, the weight will just divided equally at
    1/N (N=number of stocks in the universe)

    Sell signal: If the 50 day SMA price is at least 2% lower than the 200 day SMA price for 3 days consecutively.

    Stop-loss: If the close of the stock falls more than 2.5% below entry price (open price on the day position was entered)
    for 3 days consecutively. (checked at each close, and filled at next open)

    Re-entry cooldown: If there is a stop-loss, but then immediately another buy signal 3 days later, no trades will happen.
    There is a cooldown of 12 trading days before re-entry into a stock.

    Warm-up: No trades for the first 200 days + 3 days for signal checks.

    The middle zone: If the 50 day SMA is neither 1% above or 2% below the 200 day SMA, nothing happens.

    Timing: follows the standard model in strategies/base.py. Decisions are made
    at each day's close and filled at the next day's open.
    """

    @property
    def name(self) -> str:
        """Identifies the strategy and its settings, e.g. 'ma_crossover_50_200'."""    
        return f"ma_crossover_{self.short_window}_{self.long_window}"

    short_window: int = 50 # how long is the short SMA window (in days)
    long_window: int = 200 # how long is the long SMA window (in days)
    buy_margin: float = 0.01 # how far above the long sma must the short sma be for a buy signal 
    sell_margin: float = 0.02 # how far below the long sma must the short sma be for a sell signal
    confirm_days: int = 3 # how many consecutive days trigger a signal (buy or sell)
    cooldown_days: int = 12
    stop_days: int = 3 # how many consecutive days trigger a stop-loss signal
    stop_distance: float = 0.025 # what percentage below entry triggers stop-loss