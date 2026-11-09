# Trading Bot

Systematic trading research and automated paper trading for US sector ETFs.

This project builds a complete algorithmic trading pipeline in Python: it
downloads and validates daily market data from the Alpaca API, tests
rule-based strategies (trend following, mean reversion and momentum) with a
backtester that includes trading costs, and evaluates them with walk-forward
testing against a buy-and-hold benchmark. The best-performing strategy is then
deployed as a scheduled bot that places daily orders on an Alpaca
paper-trading account, with risk limits, logging and a dashboard comparing
live results with the backtest.

**Status:** in progress: data pipeline done; strategies and backtester next.

- [x] Data pipeline: Alpaca download, Parquet cache, validation, data-quality report
- [ ] Strategies: shared interface, buy-and-hold benchmark, trend, mean-reversion and momentum strategies
- [ ] Backtester: daily simulation with commissions, slippage and position sizing
- [ ] Evaluation: Sharpe ratio, drawdown, walk-forward testing, parameter sensitivity
- [ ] Live bot: scheduled paper trading on Alpaca with risk limits and a kill switch
- [ ] Monitoring: dashboard comparing live results with the backtest
- [ ] Write-up: results, limitations and lessons learned


## Setup
1. Python 3.14, then `python -m venv .venv` and activate it
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Alpaca paper-trading keys
4. `python src/main.py`


### Possible future extensions
- Small-scale live trading with real money, after the paper-trading phase
- Options pricing and volatility analysis (binomial, Black-Scholes, Monte Carlo, implied volatility surface)
- C++ backtesting engine, benchmarked against the Python version (possibly as a separate repository)