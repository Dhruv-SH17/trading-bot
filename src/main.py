from config import load_config
from market_data import symbol_bars, field_table
from data import get_bars, data_report
from paths import LOG_DIR
import logging
import time


logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[
                        logging.StreamHandler(),
                        #logging.FileHandler(LOG_DIR/"bot.log", encoding="utf-8") for future live bot logging
                    ])

cfg = load_config()

symbols = cfg['universe'] + [cfg['benchmark']]

bars = get_bars(symbols, cfg['data']['start'], cfg['data']['end'])

report = data_report(bars)

print(report.loc['XLK'])

