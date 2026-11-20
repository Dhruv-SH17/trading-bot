import pandas as pd
from math import sqrt
from numpy import nan, isclose
from features import calculate_daily_returns


def calculate_rolling_volatility[PricesData: (pd.DataFrame, pd.Series)](prices: PricesData,
                                                                        window: int,
                                                                        periods_per_year: int = 252) -> PricesData:
    """Rolling volatility: the sample standard deviation of simple daily returns.

    window: number of returns in each rolling window. Must be at least 2.
    periods_per_year: rows per year in the data, used to scale the result by.
    sqrt(periods_per_year). 252 (default) gives annualized volatility for
    daily data; For weekly data, the value would be 52.
    1 leaves it as per-row (daily) volatility.

    The first `window` rows are NaN: returns start with one NaN, and each
    window needs `window` valid returns
    """
    if window < 2:
        raise ValueError(f"Window cannot be less than 2, got: {window}")
    if periods_per_year < 1:
        raise ValueError(f"Periods Per Year cannot be less than 1, got: {periods_per_year}")
    volatility = calculate_daily_returns(prices).rolling(window).std()

    return sqrt(periods_per_year)*volatility

def calculate_annual_volatility(equity: pd.Series,
                                periods_per_year: int = 252) -> float:
    """"""
    if periods_per_year < 1:
        raise ValueError(f"Periods Per Year cannot be less than 1. Got: {periods_per_year}")
    _validate_equity(equity)
    
    daily_returns = calculate_daily_returns(equity)
    standard_deviation = daily_returns.std(ddof=1)

    return float(standard_deviation*sqrt(periods_per_year))

def calculate_total_return(equity: pd.Series) -> float:
    """Returns the total equity change from day 1 to the latest entry. 0.5 = 50%"""

    _validate_equity(equity)
    
    total_return = equity.iloc[-1]/equity.iloc[0] - 1
    
    return float(total_return)

def calculate_drawdown_series(equity: pd.Series) -> pd.Series:
    """Returns the drawdown for each day. 
    
    -0.25 means 25% lower than the running peak."""
    _validate_equity(equity)
    running_peak = equity.cummax()

    return equity/running_peak-1

def calculate_max_drawdown(equity: pd.Series) -> float:
    """Returns the maximum drawdown for an entire equity curve.

    e.g -0.25 means the maximum drawdown was 25% lower than the previous peak.
    Returns 0 if the curve never fell below the previous peak.
    """
    drawdown_series = calculate_drawdown_series(equity)

    return float(drawdown_series.min())

def calculate_cagr(equity: pd.Series) -> float:
    """Returns Compound Annual Growth Rate.
    
    0.2 means an average growth of 20% over the total amount of years.
    This doesn't show the ups and downs of the strategy,
    just a value that represents the returns averaged over the span of years.
    This is useful for comparing different strategies across different time horizons.
    """
    _validate_equity(equity)
    index = equity.index

    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"The index is not type of DatetimeIndex. Got: {type(index).__name__}")
    
    first_date = index[0].date()
    last_date = index[-1].date()
    starting_equity = float(equity.iloc[0])
    ending_equity = float(equity.iloc[-1])    

    total_days_timedelta = last_date-first_date

    # 365.25 for the average length of a year (including leap years)
    years = total_days_timedelta.days / 365.25
    if years == 0:
        raise ValueError(f"The year difference can't be 0. Got: {years}")

    return float(ending_equity/starting_equity)**(1/years)-1

def _validate_equity(equity: pd.Series, size: int = 2) -> None:

    if equity.index.size < size:
        raise ValueError(f"The Equity series can't have less than {size} values. Got: {equity.index.size}")

    if pd.isna(equity.iloc[0]) or equity.iloc[0] <= 0:
        raise ValueError(f"The first equity value must be positive. Got: {equity.iloc[0]}")

def calculate_sharpe_ratio(equity: pd.Series,
                           risk_free_rate: float = 0,
                           periods_per_year: int = 252) -> float:
    """Sharpe measures: annualized mean excess return divided by annualized volatility.

    risk_free_rate is an annual rate (0.04 = 4%), converted per period by dividing by periods_per_year.
    periods_per_year defaults to 252 (for daily data), you could use 52 for weekly data for example.
    This will return NaN for data with zero volatility.
    """
    excess_return_series = _calculate_excess_returns(equity, risk_free_rate, periods_per_year)
    excess_return = excess_return_series.mean()
    standard_deviation = excess_return_series.std(ddof=1)
    

    if isclose(standard_deviation, 0):
        return nan
    
    return float(excess_return/standard_deviation)*sqrt(periods_per_year)

def calculate_sortino_ratio(equity: pd.Series,
                           risk_free_rate: float = 0,
                           periods_per_year: int = 252) -> float:
    """Sortino measures: annualized mean excess return divided by annualized downside volatility.

    risk_free_rate is an annual rate (0.04 = 4%), converted per period by dividing by periods_per_year.
    periods_per_year defaults to 252 (for daily data), you could use 52 for weekly data for example.
    This will return NaN for data with zero downside deviation
    because there are no days with a loss below the risk-free rate.
    """

    excess_return_series = _calculate_excess_returns(equity, risk_free_rate, periods_per_year)
    excess_return = excess_return_series.mean()
    downside_deviation = sqrt(((excess_return_series.clip(upper=0))**2).mean())

    if isclose(downside_deviation, 0):
        return nan
    
    return float(excess_return/downside_deviation)*sqrt(periods_per_year)

def _calculate_excess_returns(equity: pd.Series, risk_free_rate: float, periods_per_year: int) -> pd.Series:

    if periods_per_year < 1:
            raise ValueError(f"Periods Per Year cannot be less than 1. Got: {periods_per_year}")
    
    _validate_equity(equity, 3)
    daily_returns = calculate_daily_returns(equity)
    return daily_returns-(risk_free_rate/periods_per_year)

def summarize_metrics(equity: pd.Series, risk_free_rate: float = 0, periods_per_year: int = 252) -> pd.Series:
    """Return the main performance metrics for one equity curve.

    risk_free_rate: annual rate (0.04 = 4%), used by the Sharpe and Sortino ratios.
    periods_per_year: rows per year in the data (252 for daily, 52 for
    weekly), used by volatility, Sharpe and Sortino.

    The result is a Series indexed by metric name:
    total_return, cagr, max_drawdown, annualized_volatility, sharpe, sortino.
    
    Each value follows its own function's conventions: max_drawdown is zero
    or negative, and sharpe and sortino are NaN when their denominator is
    zero. Combine several summaries with pd.concat(axis=1) to compare
    strategies.
    """
    summary = pd.Series({
        "total_return": calculate_total_return(equity),
        "cagr": calculate_cagr(equity),
        "max_drawdown": calculate_max_drawdown(equity),
        "annualized_volatility": calculate_annual_volatility(equity, periods_per_year),
        "sharpe": calculate_sharpe_ratio(equity, risk_free_rate, periods_per_year),
        "sortino": calculate_sortino_ratio(equity, risk_free_rate, periods_per_year)
    })

    return summary