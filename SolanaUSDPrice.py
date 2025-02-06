import requests
import os
from dotenv import load_dotenv

load_dotenv()

coinbase_api_key = os.getenv('coinbase_api_key')
coingecko_api_key = os.getenv('coingecko_api_key')
binance_api_key = os.getenv('binance_api_key')

def get_sol_price():
   # Coinbase API
   try:
       coinbase_response = requests.get(coinbase_api_key)
       if coinbase_response.status_code == 200:
           price = float(coinbase_response.json()['data']['amount'])
           #print("Price source: Coinbase")
           return price
   except Exception:
       pass
   
   # CoinGecko API
   try:
       coingecko_response = requests.get(coingecko_api_key)
       if coingecko_response.status_code == 200:
           price = coingecko_response.json()['solana']['usd']
           #print("Price source: CoinGecko")
           return price
   except Exception:
       pass
   
   # Binance API
   try:
       binance_response = requests.get(binance_api_key)
       if binance_response.status_code == 200:
           price = float(binance_response.json()['price'])
           #print("Price source: Binance")
           return price
   except Exception:
       pass
   
   return None

# Removed module-level code
