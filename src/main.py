from config import load_config
from market_data import symbol_bars, field_table
from data import get_bars, data_report
from paths import LOG_DIR
import logging
from backtester import run_backtest, CostModel
from strategies.buy_and_hold import BuyAndHold
from market_data import MarketData
import matplotlib.pyplot as plt


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

strategy = BuyAndHold()

weights = strategy.weights(data)

backtest_cfg = cfg['backtest']

result = run_backtest(
    weights,
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

result.equity.plot(title=f"{strategy.name}: portfolio value")
plt.show()

