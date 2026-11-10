from typing import Literal, Self
import pandas as pd
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketData:
    """Daily data for all symbols. Each field is a table, one row per date, one column per symbol."""

    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame    

    @classmethod
    def from_bars(cls, bars: pd.DataFrame) -> Self:
        return cls(
            open=field_table(bars, 'open'),
            high=field_table(bars, 'high'),
            low=field_table(bars, 'low'),
            close=field_table(bars, 'close'),
            volume=field_table(bars, 'volume'),
        )


    def up_to(self, date: pd.Timestamp) -> Self:
        return type(self)(
            open=self.open.loc[:date],
            high=self.high.loc[:date],
            low=self.low.loc[:date],
            close=self.close.loc[:date],
            volume=self.volume.loc[:date],
        )


BarField = Literal["open", "high", "low", "close", "volume", "vwap", "trade_count"]

def field_table (bars: pd.DataFrame, name: BarField) -> pd.DataFrame:

    return bars[name].unstack(level='symbol')

def symbol_bars (bars: pd.DataFrame, symbol: str) -> pd.DataFrame:

    available = bars.index.unique(level='symbol')

    if symbol not in available:
        raise KeyError(f"{symbol} is not in the loaded data. Available: {sorted(available)}")

    table = bars.xs(symbol, level="symbol")
    if not isinstance(table, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame for {symbol}, got {type(table).__name__}")
    
    return table 