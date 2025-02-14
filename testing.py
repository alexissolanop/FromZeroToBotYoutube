import asyncio
import os
from colorama import Fore
from config.config import sol_buy_amount, slippage, priority_fee,MAX_FEE_RETRIES,PRIORITY_FEE_INCREMENT_SOL,PRIORITY_FEE_MAX_SOL
from config.setup import http_uri, wss_uri, keys_hash, wallet_address
from utils.ui import print_separator
from utility import get_time_greeting, get_random_quote,colorize_sol,get_fear_greed_index,colorize_greed_index,get_fear_greed_index_alternative,get_bitcoin_dominance
from MarketManager import MarketManager
from SolanaRpcApi import SolanaRpcApi
from TradesManager import TradesManager
from TradingDTOs import Order, Order_Type, Amount  # Import necessary classes
from SolanaUSDPrice import get_sol_price
from utils.ui import clear_terminal, print_startup_banner, print_dashboard_header, print_quote_of_the_day, print_fear_greed_index,print_initial_sol_price,print_wallet_balance,should_clear_terminal,print_separator
from datetime import datetime
import time
from colorama import Fore, Style
  # Show everything inside the module


async def main():  # main function needs to be async
    if keys_hash:
        print(Fore.MAGENTA + "✓ Keys hash is available")
        solana_rpc_api = SolanaRpcApi(http_uri, wss_uri, http_uri, wallet_address)
        print(Fore.BLUE + "✓ Connected to Solana RPC")

        market_manager = MarketManager(solana_rpc_api)
        trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)




if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
