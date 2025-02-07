from utility import get_time_greeting, get_random_quote,colorize_sol,get_fear_greed_index,colorize_greed_index
from MarketManager import MarketManager
from SolanaRpcApi import SolanaRpcApi
from TradesManager import TradesManager
from SolanaUSDPrice import get_sol_price
from TradingDTOs import *
import os
import sys
from dotenv import load_dotenv
import asyncio
from colorama import init, Fore, Style
import random
from datetime import datetime
import time
import copy 


# Initialize colorama
init(autoreset=True)

load_dotenv()

# Trading Configuration
sol_buy_amount = Amount.sol_ui(.0001)
slippage = Amount.percent_ui(13)
priority_fee = Amount.sol_ui(.0001)
profit_limit = PnlOption(trigger_at_percent = Amount.percent_ui(600), allocation_percent = Amount.percent_ui(100))
stop_loss = PnlOption(trigger_at_percent = Amount.percent_ui(-15), allocation_percent = Amount.percent_ui(100))

def clear_terminal():
    """Clears the terminal output across platforms"""
    if platform.system().lower() == 'windows':
        os.system('cls')
    else:
        os.system('clear')

async def main():
    # Colorful startup banner
    print(Fore.CYAN + "=" * 50)
    print(Fore.YELLOW + "🚀 SOLANA TRADING BOT INITIALIZING 🚀".center(50))
    print(Fore.CYAN + "=" * 50)
    
    print(Fore.GREEN + "Starting main function")

    # Refresh intervals
    PRICE_REFRESH_INTERVAL = 300  # 5 minutes
    FEAR_GREED_REFRESH_INTERVAL = 1800  # 30 minutes


    
    # Last update timestamps
    last_price_update = time.time()
    last_fear_greed_update = 0


    # Previous values for detecting changes
    previous_sol_price = None
    previous_fear_greed = None
    previous_token_accounts_dict = None
    colorized_index = None
    classification = None
    sol_price = None
    # Load environment variables
    http_uri = os.getenv('http_rpc_uri')
    wss_uri = os.getenv('wss_rpc_uri')
    keys_hash = os.getenv('payer_hash')
    wallet_address = os.getenv('wallet_address')

    if keys_hash:
        print(Fore.MAGENTA + "✓ Keys hash is available")
        solana_rpc_api = SolanaRpcApi(http_uri, wss_uri, http_uri, wallet_address)
        print(Fore.BLUE + "✓ Connected to Solana RPC")
        
        # ✅ Initialize MarketManager BEFORE using it
        market_manager = MarketManager(solana_rpc_api)
        trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)

        # Print initial welcome messages
        # Separator
        print(Fore.CYAN + "=" * 50)
        
        # Dynamic greeting
        print(Fore.GREEN + f"{get_time_greeting()}, Mr Mason!")
        
        # Random quote of the day
        print(Fore.MAGENTA + f"Quote of the Day: {get_random_quote()}")

        # Fetch initial data
        sol_price = get_sol_price()
        sol_balance = market_manager.get_sol_balance(wallet_address)
        colorized_index, classification = get_fear_greed_index()
        
        # Set initial previous values
        previous_sol_price = sol_price
        previous_fear_greed = colorized_index
        #previous_token_accounts = solana_rpc_api.get_non_zero_token_accounts()

        # Print initial values
        print(f"💰 Initial SOL Price: ${sol_price:.2f} 🚀" if sol_price else "💔 SOL Price: Unable to fetch 🕵️")
        print(f"📊 Initial Market Mood: {colorized_index} ({classification})" if colorized_index else "🚫 Market Mood: Mysterious Signal Lost 🛸")

        # Separator
        print(Fore.CYAN + "=" * 50)

        # Initialize your "previous" variable as a dictionary
        previous_token_accounts_dict = None
        
        try:
            while True: 
                # Get current time               
                current_time = time.time()

                # ✅ Refresh SOL price every 5 minutes
                if current_time - last_price_update > PRICE_REFRESH_INTERVAL:
                    try:
                        new_sol_price = get_sol_price()
                        if new_sol_price != previous_sol_price:
                            previous_sol_price = new_sol_price
                            sol_price = new_sol_price
                            print(f"Updated SOL price: {sol_price}")
                    except Exception as e:
                        print(f"Error refreshing SOL price: {e}")
                    last_price_update = current_time

                

                # ✅ Refresh Fear & Greed Index every 30 minutes
                if current_time - last_fear_greed_update > FEAR_GREED_REFRESH_INTERVAL:
                    try:
                        new_index, new_classification = get_fear_greed_index()
                        if new_index != previous_fear_greed:
                            previous_fear_greed = new_index
                            colorized_index, classification = new_index, new_classification
                            print(f"Updated Fear & Greed: {colorized_index} - {classification}")
                    except Exception as e:
                        print(f"Error updating fear/greed: {e}")    
                    last_fear_greed_update = current_time 

                
                # ✅ Always refresh wallet balance & tokens inside the loop
                sol_balance = market_manager.get_sol_balance(wallet_address)
                token_accounts = solana_rpc_api.get_non_zero_token_accounts() 
                

                # Print dashboard
                print(Fore.YELLOW + "🚀 SOLANA TRADING BOT DASHBOARD 🚀".center(50))
                print(Fore.CYAN + "=" * 50)                
                colored_balance = colorize_sol(sol_balance)
                print(f"💰 Wallet Balance: {colored_balance} (${sol_balance * sol_price:.2f})" if sol_price else f"💰 Wallet Balance: {colored_balance} (USD price unavailable)")
                
                if token_accounts:
                    # If first time OR any changes compared to previous
                    if previous_token_accounts_dict is None or token_accounts != previous_token_accounts_dict:
                        print("🔹 Token Holdings:")

                        # Loop the list
                        for token_info in token_accounts:
                        # Each token_info is a dict with keys 'mint' and 'balance'
                            mint = token_info['mint']
                            balance = token_info['balance']
                            print(f"Holding {balance} of {mint}")

                        # Update previous_token_accounts_dict to match what we have now
                        previous_token_accounts_dict = copy.deepcopy(token_accounts)
   
                    else:
                        # No changes in token holdings
                        print("🛑 No token balance changes detected.")
                else:
                    # No token_accounts at all
                    if previous_token_accounts_dict is None or previous_token_accounts_dict != {}:
                        # This is the first time we've seen an empty dict or it's changed from non-empty
                        print("🌱 Your wallet might be empty now, but every epic journey begins with an empty canvas—get ready to paint your masterpiece! 🎨✨")
                        previous_token_accounts_dict = {}
                    else:
                        # It's still empty (no changes)
                        print("🛑 No token balance changes detected.")

                

                # ✅ Clear terminal only when data changes (Prevents flickering)
                if (
                    sol_price != previous_sol_price or
                    colorized_index != previous_fear_greed or
                    (previous_token_accounts_dict is not None and [tuple(sorted(d.items())) for d in token_accounts] != [tuple(sorted(d.items())) for d in previous_token_accounts_dict])
                ):
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
                    order = Order(Order_Type.BUY, token_address, sol_buy_amount, slippage, priority_fee)
                    tx_signature = trades_manager.execute_order(order, True)
                    print(f"Buy order executed. Transaction signature: {tx_signature}")

                    # Wait for 2 seconds to allow on-chain state to update
                    await asyncio.sleep(2)

                    # Fetch token details
                    token_info = market_manager.get_token_info(token_address)
                    transaction_info = trades_manager.get_order_transaction(tx_signature)

                    # Check if transaction info is valid and tokens were bought
                    if transaction_info and transaction_info.token_diff > 0:
                        # Calculate price per token
                        temp_calc = abs(transaction_info.sol_diff / transaction_info.token_diff)
                        base_token_price = Amount.sol_ui(temp_calc / 1E9)  # Convert from lamports to SOL
                        # Calculate the amount of tokens bought
                        tokens_bought = Amount.tokens_ui(transaction_info.token_diff, token_info.decimals_scale_factor)
                        
                        print(f"Tokens Bought: {tokens_bought.ToUiValue()} {token_address}")
                        print(f"Purchase Price: {base_token_price.ToUiValue()} SOL per token")
                    else:
                        print("Transaction info not found or no tokens were bought.")

                elif choice == '2':
                    try:
                        token_address = input("Enter a token address to sell: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    token_info = market_manager.get_token_info(token_address)
                    wallet_balance = trades_manager.get_account_balance(token_address)
                    
                    print(f"Current wallet balance for {token_address}: {wallet_balance}")

                    try:
                        percentage_to_sell = float(input("Enter the percentage of tokens to sell (0-100): "))
                    except (KeyboardInterrupt, EOFError):
                        print("\nReturning to main menu...")
                        continue
                    tokens_to_sell = wallet_balance.value * (percentage_to_sell / 100)

                    order = Order(Order_Type.SELL, token_address, Amount.tokens_ui(tokens_to_sell, token_info.decimals_scale_factor), slippage, priority_fee)
                    tx_signature = trades_manager.execute_order(order, True)
                    print(f"Sell order executed for {tokens_to_sell} tokens. Transaction signature: {tx_signature}")

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
