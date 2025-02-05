import requests

def get_sol_price():
   # Coinbase API
   try:
       coinbase_response = requests.get('https://api.coinbase.com/v2/prices/SOL-USD/spot')
       if coinbase_response.status_code == 200:
           price = float(coinbase_response.json()['data']['amount'])
           print("Price source: Coinbase")
           return price
   except Exception:
       pass
   
   # CoinGecko API
   try:
       coingecko_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd')
       if coingecko_response.status_code == 200:
           price = coingecko_response.json()['solana']['usd']
           print("Price source: CoinGecko")
           return price
   except Exception:
       pass
   
   # Binance API
   try:
       binance_response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT')
       if binance_response.status_code == 200:
           price = float(binance_response.json()['price'])
           print("Price source: Binance")
           return price
   except Exception:
       pass
   
   return None

# Usage
sol_price = get_sol_price()
if sol_price:
   print(f"Current SOL/USD Price: ${sol_price:.2f}")
else:
   print("Failed to retrieve SOL price from available sources.")