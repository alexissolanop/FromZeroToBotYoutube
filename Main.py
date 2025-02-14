from utility import get_time_greeting, get_random_quote,get_fear_greed_index,get_bitcoin_dominance
from config.config import sol_buy_amount, slippage, priority_fee, profit_limit, stop_loss
from config.setup import http_uri, wss_uri, keys_hash, wallet_address
from utils.ui import clear_terminal, print_startup_banner, print_dashboard_header, print_quote_of_the_day, print_fear_greed_index,print_initial_sol_price,print_wallet_balance,should_clear_terminal,print_separator
from utils.wallet import update_and_print_token_holdings
from utils.market import update_sol_price, update_fear_greed_index
from utils.trading import buy_token, sell_token
from SolanaUSDPrice import get_sol_price
from MarketManager import MarketManager
from SolanaRpcApi import SolanaRpcApi
from TradesManager import TradesManager
from TradingDTOs import *
import os
import sys
import asyncio
from colorama import init, Fore, Style
import random
from datetime import datetime
import time

clear_terminal()

async def main():
    # Colorful startup banner
    print_startup_banner()
    
    # Import config variables
    from config.config import PRICE_REFRESH_INTERVAL, FEAR_GREED_REFRESH_INTERVAL, last_price_update, \
        last_fear_greed_update, previous_sol_price, previous_fear_greed, previous_token_accounts_dict, \
        colorized_index, classification, sol_price

    if keys_hash:
        print(Fore.MAGENTA + "✓ Keys hash is available")
        solana_rpc_api = SolanaRpcApi(http_uri, wss_uri, http_uri, wallet_address)
        print(Fore.BLUE + "✓ Connected to Solana RPC")
        
        # ✅ Initialize MarketManager BEFORE using it
        market_manager = MarketManager(solana_rpc_api)
        trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)

        # Print initial welcome messages
        # Separator
        print_separator()
        
        # Dynamic greeting
        print(Fore.GREEN + f"{get_time_greeting()}, MrMason!")
        
        # Random quote of the day
        quote = get_random_quote()
        print_quote_of_the_day(quote)

        # Fetch initial data
        sol_price = get_sol_price()
        sol_balance = market_manager.get_sol_balance(wallet_address)
        colorized_index, classification = get_fear_greed_index()
     
        # Set initial previous values
        previous_sol_price = sol_price
        previous_fear_greed = colorized_index
        #previous_token_accounts = solana_rpc_api.get_non_zero_token_accounts()

        # Print initial values SOL price
        print_initial_sol_price(sol_price)
        # Fetch Fear & Greed Index
        colorized_index, classification = get_fear_greed_index()
        print_fear_greed_index(colorized_index, classification)

        #Print Bitcon Dominance
        btc_dominance = get_bitcoin_dominance()
        print(f"₿ Bitcoin Dominance: {btc_dominance:.2f}% 🔥")

        # Separator
        print_separator()

        # Initialize your "previous" variable as a dictionary
        previous_token_accounts_dict = None
        
        try:
            while True: 
                # ✅ Refresh SOL price every 5 minutes
                sol_price, last_price_update = update_sol_price(sol_price, previous_sol_price, last_price_update, PRICE_REFRESH_INTERVAL)

                # ✅ Refresh Fear & Greed Index every 30 minutes
                colorized_index, classification, last_fear_greed_update = update_fear_greed_index(previous_fear_greed, last_fear_greed_update, FEAR_GREED_REFRESH_INTERVAL)
 
                # ✅ Always refresh wallet balance & tokens inside the loop
                sol_balance = market_manager.get_sol_balance(wallet_address)
                token_accounts = solana_rpc_api.get_non_zero_token_accounts() 
                
                # Print dashboard
                print_dashboard_header()
                # Print SOL balance             
                print_wallet_balance(sol_balance, sol_price)
                # Print Token Holdings
                previous_token_accounts_dict = update_and_print_token_holdings(token_accounts, previous_token_accounts_dict)

                # ✅ Clear terminal only when data changes (Prevents flickering)
                if should_clear_terminal(sol_price, previous_sol_price, colorized_index, previous_fear_greed, token_accounts, previous_token_accounts_dict):
                    clear_terminal()
                
                print("\nChoose an option:")
                print("1. Buy a token")
                print("2. Sell a token")
                print("3. Get wallet balance")
                print("4. Execute order with limits and stops")
                print("5. Exit")
                
                try:
                    choice = input("Enter your choice (1-5): ")
                except (KeyboardInterrupt, EOFError):
                    print("\nProgram interrupted. Exiting...")
                    break
                    
                if choice == '1':
                    try:
                        token_address = input("Enter a token address to buy: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    # Call the new buy function
                    await buy_token(trades_manager, market_manager, token_address, sol_buy_amount, slippage, priority_fee)
                    
                elif choice == '2':
                    try:
                        token_address = input("Enter a token address to sell: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    
                    await sell_token(trades_manager, market_manager, token_address, slippage, priority_fee)
            

                elif choice == '3':
                    try:
                        contract_address = input("Enter the contract address to check balance: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    balance = trades_manager.get_account_balance(contract_address)
                    print(f"Wallet balance: {balance}")

                elif choice == '4':
                    try:
                        token_address = input("Enter a token address to trade: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    order = Order(Order_Type.BUY, token_address, sol_buy_amount, slippage, priority_fee)
                    tx_signature = trades_manager.execute_order(order, True)
                    token_info = market_manager.get_token_info(token_address)
                    transaction_info = trades_manager.get_order_transaction(tx_signature)

                    if transaction_info and transaction_info.token_diff > 0:
                        temp_calc = abs(transaction_info.sol_diff / transaction_info.token_diff)
                        base_token_price = Amount.sol_ui(temp_calc/1E9)
                        tokens_bought = Amount.tokens_ui(transaction_info.token_diff, token_info.decimals_scale_factor)

                        order = OrderWithLimitsStops(token_address, base_token_price, tokens_bought, slippage, priority_fee)
                        order.add_pnl_option(profit_limit)
                        order.add_pnl_option(stop_loss)

                        trades_manager.execute_order(order, True)
                        print("Order with limits and stops executed")

                elif choice == '5':
                    print("Exiting the program.")
                    break

                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")

                # Wait 5 seconds before next loop iteration
                time.sleep(5)

        except KeyboardInterrupt:
            print("\nProgram interrupted. Exiting...")

        finally:
            # Close any open connections or resources
            if 'solana_rpc_api' in locals():
                await solana_rpc_api.close()
            
            # Force exit the event loop
            current_loop = asyncio.get_event_loop()
            current_loop.stop()
            current_loop.close()
            
            # Forcefully terminate the program
            os._exit(0)        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    finally:
        # Forcefully terminate the program
        os._exit(0)
