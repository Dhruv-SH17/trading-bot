import os
import pandas as pd
from features import calculate_daily_returns
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment
from alpaca.data.models import BarSet
from datetime import datetime, timedelta, timezone
from market_data import field_table
from typing import Literal
from pathlib import Path
from paths import CACHE_DIR
import logging



from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

"""
alpaca defines timeframe with a custom classproperty that typecheckers can't follow.
It returns a valid TimeFrame at runtime. (alpaca-py 0.45.0)
"""

DAILY: TimeFrame = TimeFrame.Day # pyright: ignore
OVERLAP = timedelta(days=7)   # re-fetch the last week to catch provider corrections

stock_client = StockHistoricalDataClient(api_key, api_secret)

def get_bars(symbols: list[str], 
             start: datetime, 
             end: datetime | None = None, 
             refresh: bool = False, 
             update: bool = True) -> pd.DataFrame:
    """Daily OHLCV bars for all symbols, indexed by (symbol, date). if end=None then it loads up to the latest data."""

    #if update is false, the function resorts to using cached data for symbols that are already cached ()

    frames = []

    for symbol in symbols:
        
        cached = None if refresh else _read_cache(symbol)

        if cached is None or _first_date(cached) > start + OVERLAP:
            logger.info("%s: full download", symbol)
            bars = _fetch_bars([symbol], start, end)

        elif not update:
            logger.info("%s using cached data only", symbol)
            frames.append(cached)
            continue
        
        else:
            logger.debug("%s: accessing cache, fetching recent days", symbol)
            new_data = _fetch_bars([symbol], _last_date(cached) - OVERLAP, end)
            bars = _merge(cached, new_data)

        _validate(bars, symbol) 
        _write_cache(symbol, bars)
        frames.append(bars)
    
    return _slice_dates(pd.concat(frames), start, end)


def data_report(bars: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe with the first date, last date, # of rows, # of missing days, 
    # of zero volume days and the maximum % move up or down"""

    closes = field_table(bars, 'close')
    volumes = field_table(bars, 'volume')
    returns = calculate_daily_returns(closes)

    
    return pd.DataFrame({
        "first_date": pd.Series({sym: col.first_valid_index() for sym, col in closes.items()}),
        "last_date": pd.Series({sym: col.last_valid_index() for sym, col in closes.items()}),
        "rows": closes.notna().sum(),
        "missing_days": closes.apply(_missing_inside_range),
        "zero_volume_days": (volumes == 0).sum(),
        "max_daily_move_pct": (returns.abs().max() * 100).round(2)
    })






#helper functions

def _fetch_bars(symbols: list[str], start: datetime, end: datetime | None) -> pd.DataFrame:

        #since the free tier on alpaca can't query data for the latest 15 minutes.
    if end is None:
        end = datetime.now(timezone.utc) - timedelta(minutes=20)


    request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=DAILY,
            start=start,
            end=end,
            adjustment=Adjustment.ALL
    )
    
    bars = stock_client.get_stock_bars(request_params)
    
        
    if not isinstance(bars, BarSet):
        raise TypeError(f"Expected BarSet from api, got {type(bars).__name__}")
    
    bars_df = bars.df

    if bars_df.empty:
        raise ValueError(f"Alpaca returned no data for {symbols} between {start:%y-%m-%d} and {end:%y-%m-%d}")

    dates = (pd.DatetimeIndex(bars_df.index.get_level_values("timestamp"))
            .tz_convert('America/New_York')
            .tz_localize(None)
    )

    bars_df.index = pd.MultiIndex.from_arrays(
        [bars_df.index.get_level_values("symbol"), dates],
        names=["symbol", "date"]
    )
    
    return bars_df


def _cache_path (symbol: str) -> Path:

    return CACHE_DIR/f"{symbol}.parquet"


def _write_cache(symbol: str, bars: pd.DataFrame) -> None:

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(symbol)
    temp_path = path.with_suffix(".parquet.tmp")

    bars.to_parquet(temp_path)
    temp_path.replace(path)
    
    return

def _read_cache(symbol: str) -> pd.DataFrame | None:

    path = _cache_path(symbol)

    if not path.exists():
        return None

    loaded = pd.read_parquet(path)
    
    return loaded

def _validate(bars: pd.DataFrame, symbol: str) -> None:

    prices = bars[['open', 'high', 'low', 'close']]

    if bars.empty:
        raise ValueError(f"{symbol}: no data.")
    if bars.index.duplicated().any():
        raise ValueError(f"{symbol} dates are duplicated.")
    if prices.isna().any().any():
        raise ValueError(f"{symbol} is missing prices.")
    if (prices <= 0).any().any():
        raise ValueError(f"{symbol} zero or negative prices.")
    if (bars['high'] < bars['low']).any():
        raise ValueError(f"{symbol} high values are less than low")

    return

def _slice_dates(bars: pd.DataFrame, start: datetime, end: datetime | None) -> pd.DataFrame:
    """Slice the data between start and end(inclusive) dates. if End = None, then there's no limit."""

    dates = bars.index.get_level_values("date")
    mask = dates >= start
    if end is not None:
        mask &= dates <= end
    
    return bars[mask]

def _merge (current: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    
    combined = pd.concat([current, new])
    
    combined = combined[~combined.index.duplicated(keep="last")]
    
    return combined.sort_index()

def _first_date(bars: pd.DataFrame) -> pd.Timestamp:
    
    return bars.index.get_level_values("date").min()


def _last_date(bars: pd.DataFrame) -> pd.Timestamp:
    
    return bars.index.get_level_values("date").max()

def _missing_inside_range(prices: pd.Series) -> int:

    trimmed = prices.loc[prices.first_valid_index():prices.last_valid_index()]
    
    return int(trimmed.isna().sum())