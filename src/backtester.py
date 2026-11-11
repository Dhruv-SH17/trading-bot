import logging
from dataclasses import dataclass, asdict, fields
import pandas as pd
from market_data import MarketData


logger = logging.getLogger(__name__)


"""since decimals aren't really represented perfectly, these are some tolerance constants.
These basically say:
WEIGHT_TOLERANCE: weights may exceed 1 by this tiny amount before it counts as an error.
MIN_TRADE_SHARES: changes smaller than this are just rounding issues and not real trades.
CASH_TOLERANCE: cash this close to zero counts as zero, not negative.
"""
WEIGHT_TOLERANCE = 1e-9
MIN_TRADE_SHARES = 1e-9
CASH_TOLERANCE = 1e-6

@dataclass(frozen=True)
class CostModel:
    """Trading costs that are applied to every simulated fill."""

    slippage: float
    commission: float

    def __post_init__(self) -> None:
        if self.slippage < 0 or self.commission < 0:
            raise ValueError(f"Costs must be non-negative. got {self}")

@dataclass(frozen=True)
class Trade:
    """One filled trade. Shares > 0 is a buy and shares < 0 is a sell."""
    
    date: pd.Timestamp
    symbol: str
    shares: float
    price: float
    commission: float

@dataclass(frozen=True)
class BacktestResult:

    equity: pd.Series
    cash: pd.Series
    positions: pd.DataFrame
    trades: pd.DataFrame


class Portfolio:
    """Cash + Shares per symbol. Weights and Values are calculated and not stored."""
    
    def __init__(self, cash: float, symbols: pd.Index) -> None:
        
        self.cash=cash
        self.shares=pd.Series(0.0, index=symbols)

    def position_values(self, prices: pd.Series) -> pd.Series:

        held = self.shares[self.shares != 0]
        if prices[held.index].isna().any():
            raise ValueError(f"Missing price for a held symbol {held.index.tolist()}")
        
        return (self.shares * prices).fillna(0.0)

    def value(self, prices: pd.Series) -> float:

        return self.cash + float(self.position_values(prices).sum())

    def weights(self, prices: pd.Series) -> pd.Series:
    
        return self.position_values(prices) / self.value(prices)

    def apply_trade(self, trade: Trade) -> None:

        self.shares[trade.symbol] += trade.shares
        self.cash -= trade.shares * trade.price + trade.commission

        if self.cash < -CASH_TOLERANCE:
            raise RuntimeError(f"Cash is negative. ({self.cash:.2f}) after {trade}")


def run_backtest(
        weights: pd.DataFrame,
        market: MarketData,
        initial_cash: float,
        costs: CostModel,
        cash_buffer: float = 0.02
) -> BacktestResult:
    """Simulate trading the target weights on historical prices.
 
    weights: target weight per symbol for each decision date (dates x symbols). 
    A row of all NaN means hold. Dates missing from the table also mean hold.
    cash_buffer: fraction of portfolio value always kept in cash, so overnight price moves can't make planned buys unaffordable.
    """

    if initial_cash <= 0:
        raise ValueError(f"Initial cash must be positive, got: {initial_cash}")
    if not 0 <= cash_buffer < 1:
        raise ValueError(f"Cash buffer must be between [0, 1). Got: {cash_buffer}")

    symbols = market.close.columns

    dates = pd.DatetimeIndex(market.close.index)

    _validate_weights(weights, symbols, dates)

    decisions = weights[symbols].reindex(dates)

    opens = market.open[symbols]
    closes = market.close[symbols]

    portfolio = Portfolio(initial_cash, symbols)

    trades: list[Trade] = []
    equity: list[float] = []
    cash: list[float] = []
    positions: list[pd.Series] = []
    pending: pd.Series | None = None

    for i, date in enumerate(dates):
        #first fill anything pending from yesterday's trades
        if pending is not None:
            trades.extend(_execute(portfolio, pending, opens.iloc[i], date, costs))
            pending = None

        close_prices = closes.iloc[i]
        equity.append(portfolio.value(close_prices))
        cash.append(portfolio.cash)
        positions.append(portfolio.shares.copy())

        # store today's decision to execute tomorrow
        row = decisions.iloc[i]
        if row.notna().all():
            pending = _target_shares(portfolio, row, close_prices, cash_buffer)

    if pending is not None:
        logger.info("Decision on the last date (%s) was not fulfilled because there is no next date.", dates[-1].date())

    return BacktestResult(
        equity = pd.Series(equity, index=dates, name="equity"),
        cash = pd.Series(cash, index=dates, name="cash"),
        positions = pd.DataFrame(positions, index=dates),
        trades = pd.DataFrame([asdict(t) for t in trades], columns=[f.name for f in fields(Trade)])
    )



def _validate_weights(weights: pd.DataFrame, symbols: pd.Index, dates: pd.DatetimeIndex) -> None:

    missing = symbols.difference(weights.columns)
    extra = weights.columns.difference(symbols)
    # 'missing' is checking any symbols that are missing from the weights Dataframe
    # 'extra' is what symbols ARE present in the weights Dataframe that aren't supposed to be there
    if len(missing) or len(extra):
        raise ValueError(f"Weight columns must match symbols. missing: {list(missing)}, extra: {list(extra)}")

    non_trading_day = weights.index.difference(dates)
    # checks if there are any trades on a non-trading day (like saturday)
    if len(non_trading_day):
        raise ValueError(f"Weights contain dates with no market data. First example: {non_trading_day[0]}")

    nan_count = weights.isna().sum(axis=1)
    # checks how many NaN values there are per row
    partial = (nan_count > 0) & (nan_count < len(weights.columns))
    # checks whether any of the rows are partially NaNs (which would be an error because either the row can ALL be NaN's or ALL be weights)
    if partial.any():
        raise ValueError(f"Rows must be all weights or all NaN's. {partial[partial].index[0]}")

    decided = weights[nan_count == 0]
    # this is a series of rows that is a decision. So this is filtering out any rows with NaN's (hold)
    if (decided < 0).any().any():
        raise ValueError("Weights must be non-negative")

    over = decided.sum(axis=1) > 1 + WEIGHT_TOLERANCE
    # this checks if any row's weights add up to be MORE than 1 + the weight tolerance.
    if over.any():
        raise ValueError(f"Weights add up to be more than 1. at {over[over].index[0]}")

def _target_shares(
    portfolio: Portfolio,
    target_weights: pd.Series,
    close_prices: pd.Series,
    cash_buffer: float
) -> pd.Series:
    """Convert target weights into share counts, sized at current day's close."""

    wanted = target_weights[target_weights > 0]
    # keeps only the symbols that have a weight above 0 (meaning the strategy wants to keep them)
    if close_prices[wanted.index].isna().any():
        raise ValueError(f"Target weight given for a symbol with no price")

    investable = portfolio.value(close_prices) * (1 - cash_buffer)

    return (target_weights * investable / close_prices).fillna(0.0)

def _execute(
    portfolio: Portfolio,
    target_shares: pd.Series,
    open_prices: pd.Series,
    date: pd.Timestamp,
    costs: CostModel
) -> list[Trade]:

    changes = target_shares - portfolio.shares

    changes = changes[changes.abs() > MIN_TRADE_SHARES]

    if open_prices[changes.index].isna().any():
        raise ValueError(f"Missing open price on {date}")

    trades: list[Trade] = []

    sells = changes[changes < 0]

    sell_prices = open_prices[sells.index] * (1 - costs.slippage)

    for symbol, qty, price in zip(sells.index, sells.to_numpy(), sell_prices.to_numpy()):
        trade = Trade(date, symbol, float(qty), float(price), costs.commission)
        portfolio.apply_trade(trade)
        trades.append(trade)


    buys = changes[changes > 0]
    buy_prices = open_prices[buys.index] * (1 + costs.slippage)
    buy_cost = float((buys * buy_prices).sum())
    budget = portfolio.cash - (costs.commission * len(buys))

    if buy_cost > budget:

        if budget <= 0:
            logger.warning("%s: no cash left to buy, skipping these trades.", {date.date()})

            return trades
        #  shrink each weight by the same ratio to fit the buys in the budget
        buys = buys * (budget/buy_cost)
        

    for symbol, qty, price in zip(buys.index, buys.to_numpy(), buy_prices.to_numpy()):
        trade = Trade(date, symbol, float(qty), float(price), costs.commission)
        portfolio.apply_trade(trade)
        trades.append(trade)


    return trades