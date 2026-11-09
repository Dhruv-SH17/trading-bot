import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")

#establish the paper trading client
trading_client = TradingClient(api_key, api_secret, paper=True)

account = trading_client.get_account()

# def __self__ ():
#     print("working")