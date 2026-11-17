import pandas as pd
from market_data import MarketData
from dataclasses import dataclass
from features import calculate_sma
import numpy as np
from backtester import _validate_weights

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
    The first day is counted at t+1's close (because the entry price )

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

    def weights(self, data: MarketData) -> pd.DataFrame:
        """Returns a weights table where buys are replaced with 1/N and sells are replaced with 0. NaN means nothing happens"""
        holding_table = self._holdings(data, self._signals(data))
        yesterday_holdings = holding_table.shift(1, fill_value=False)
        bought_mask = holding_table & ~yesterday_holdings
        sold_mask = yesterday_holdings & ~holding_table
        num_of_symbols = len(data.close.columns)

        table = pd.DataFrame(np.nan, index=holding_table.index, columns=holding_table.columns)
        bought_table = table.mask(bought_mask, 1/num_of_symbols)
        sold_table = bought_table.mask(sold_mask, 0)
        target_weights = sold_table.dropna(how='all')
    
        _validate_weights(target_weights, data.close.columns, pd.DatetimeIndex(data.close.index))
        return target_weights
    
    def _signals(self, data: MarketData) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Returns a tuple with a two dataframes for all symboles. 
        The first one is where buys are confirmed.
        The second one is where sells are confirmed."""
        close = data.close
        close_sma_short = calculate_sma(close, self.short_window)
        close_sma_long = calculate_sma(close, self.long_window)

        buy_condition = close_sma_short >= (close_sma_long * (1 + self.buy_margin))
        sell_condition = close_sma_short <= (close_sma_long * (1 - self.sell_margin))

        buy_confirmed = buy_condition.rolling(self.confirm_days).sum() == self.confirm_days
        sell_confirmed = sell_condition.rolling(self.confirm_days).sum() == self.confirm_days

        return (buy_confirmed, sell_confirmed) 


    def _holdings_for_symbol(self, opens: pd.Series, closes: pd.Series, buy_signal: pd.Series, sell_signal: pd.Series) -> pd.Series:
        """Returns a Series for whether a symbol is held."""
        held = []
        cooldown = 0
        stop_loss_count = 0
        entry_price = None
        holding: bool = False
        bought_at_next_open: bool = False

        open_arr = opens.to_numpy()
        close_arr = closes.to_numpy()
        buy_signal_arr = buy_signal.to_numpy()
        sell_signal_arr = sell_signal.to_numpy()


        for i in range(len(close_arr)):
            open_today = open_arr[i]
            close_today = close_arr[i]
            buy_signal_today = buy_signal_arr[i]
            sell_signal_today = sell_signal_arr[i]

            # in the morning, fill yesterday's decision
            if bought_at_next_open:
                entry_price = open_today
                bought_at_next_open = False
                stop_loss_count = 0

            if holding:
                if entry_price is not None:
                    if close_today < (entry_price*(1-self.stop_distance)):
                        stop_loss_count += 1
                    else:
                        stop_loss_count = 0
                if stop_loss_count >= self.stop_days:
                    holding = False
                    # the day the stop-loss is executed counts as day 1 for the cooldown.
                    cooldown = self.cooldown_days - 1
                    entry_price = None
                    stop_loss_count = 0
                elif sell_signal_today:
                    holding = False
                    entry_price = None
                    stop_loss_count = 0
            else:
                if cooldown > 0:
                    cooldown -= 1
                elif buy_signal_today:
                    holding = True
                    bought_at_next_open = True                
                

            held.append(holding)

                
        return pd.Series(held, index=closes.index)

    def _holdings(self, data: MarketData, confirmed_tables: tuple[pd.DataFrame, pd.DataFrame]) -> pd.DataFrame:
        """Combines all the holding data per symbol into one dataframe."""
        buy_confirmed, sell_confirmed = confirmed_tables

        opens = data.open
        closes = data.close

        holdings = {}

        for symbol in closes.columns:
            holdings[symbol] = self._holdings_for_symbol(
                opens[symbol],
                closes[symbol],
                buy_confirmed[symbol],
                sell_confirmed[symbol]
            )

        return pd.DataFrame(holdings, columns=closes.columns)