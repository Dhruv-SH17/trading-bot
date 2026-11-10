from datetime import datetime
from paths import CONFIG_PATH
import yaml


def load_config(path = CONFIG_PATH) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
        symbols = [s.strip().upper() for s in cfg['universe']]

        if not symbols:
            raise ValueError("Universe must contain at least one ticker: add one to config.yaml")
        if len(set(symbols)) != len(symbols):
            raise ValueError("Universe contains duplicate tickers: {symbols}")

        cfg['universe'] = symbols
        cfg['benchmark'] = cfg['benchmark'].strip().upper()

        cfg['data']['start'] = datetime.fromisoformat(cfg['data']['start'])
        if cfg['data']['end'] is not None:
             cfg['data']['end'] = datetime.fromisoformat(cfg['data']['end'])

        return cfg