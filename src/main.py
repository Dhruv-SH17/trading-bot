from config import load_config
from market_data import symbol_bars, field_table
from data import get_bars, data_report
from paths import LOG_DIR
import logging
from backtester import run_backtest, CostModel
from strategies.buy_and_hold import BuyAndHold
from strategies.moving_average_crossover import MovingAverageCrossover
from market_data import MarketData
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[
                        logging.StreamHandler(),
                        #logging.FileHandler(LOG_DIR/"bot.log", encoding="utf-8") for future live bot logging
                    ])

cfg = load_config()

#symbols = cfg['universe'] + [cfg['benchmark']]


universe_symbols = cfg['universe']
benchmark_symbol = cfg['benchmark']

universe_bars = get_bars(universe_symbols, cfg['data']['start'], cfg['data']['end'])

data = MarketData.from_bars(universe_bars)

buyhold_strategy = BuyAndHold()
ma_crossover_strategy = MovingAverageCrossover()
ma_weights = ma_crossover_strategy.weights(data)
buy_hold_weights = buyhold_strategy.weights(data)


backtest_cfg = cfg['backtest']

result_ma = run_backtest(
    ma_weights,
    data,
    float(backtest_cfg['initial_cash']),
    CostModel(cfg['backtest']['costs']['slippage'], 0.0),
    float(cfg['backtest']['cash_buffer'])
)

result_buy_hold = run_backtest(
    buy_hold_weights,
    data,
    float(backtest_cfg['initial_cash']),
    CostModel(cfg['backtest']['costs']['slippage'], 0.0),
    float(cfg['backtest']['cash_buffer'])
)


#report = data_report(bars)

#print(report.loc['XLK'])
# print("TRADES")
# print(result.trades)
# print("CASH")
# print(result.cash)
# print("EQUITY")
# print(result.equity.tail())



# print(field_table(universe_bars, 'open'))
# print(f"Printing Trades\n {result.trades}")
fig, (left, right) = plt.subplots(1, 2, sharey=True, figsize=(12,4))
result_ma.equity.plot(title=f"{ma_crossover_strategy.name}: portfolio value", ax=left)
result_buy_hold.equity.plot(title=f"{buyhold_strategy.name}: portfolio value", ax=right)
left: Axes
right: Axes
summary_ma = (
    f"Final equity: {result_ma.equity.iloc[-1]:,.0f}\n"
    f"Returns: {result_ma.equity.iloc[-1]/result_ma.equity.iloc[0]-1:.1%}"
)
left.text(
    0.02, 0.97, summary_ma,
    transform=left.transAxes,
    va='top',
    fontsize=9,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

summary_buy_hold = (
    f"Final equity: {result_buy_hold.equity.iloc[-1]:,.0f}\n"
    f"Returns: {result_buy_hold.equity.iloc[-1]/result_buy_hold.equity.iloc[0]-1:.1%}"
)
right.text(
    0.02, 0.97, summary_buy_hold,
    transform=right.transAxes,
    va='top',
    fontsize=9,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)


fig.tight_layout()
plt.show()
