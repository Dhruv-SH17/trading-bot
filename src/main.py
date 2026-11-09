from config import load_config
from data import get_bars, field_table, symbol_bars, data_report
from features import calculate_daily_returns

cfg = load_config()

symbols = cfg['universe'] + [cfg['benchmark']]

bars = get_bars(symbols, cfg['data']['start'], cfg['data']['end'])

report = data_report(bars)

daily = calculate_daily_returns(symbol_bars(bars, 'SPY')['close'])
print(daily)

print(report.loc['XLK'])

