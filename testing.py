from MarketManager import MarketManager
from SolanaRpcApi import SolanaRpcApi
from TradesManager import TradesManager
import os
from dotenv import load_dotenv

load_dotenv()
# Load environment variables
http_uri = os.getenv('http_rpc_uri')
wss_uri = os.getenv('wss_rpc_uri')
keys_hash = os.getenv('payer_hash')
wallet_address = os.getenv('wallet_address')

    
solana_rpc_api = SolanaRpcApi(http_uri, wss_uri, http_uri, wallet_address)   
market_manager = MarketManager(solana_rpc_api)
trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)

token_address = "Hjw6bEcHtbHGpQr8onG3izfJY5DJiWdt7uk2BfdSpump"
wallet_balance = trades_manager.get_account_balance(token_address)
print(wallet_balance)
