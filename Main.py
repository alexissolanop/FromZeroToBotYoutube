from utility import get_time_greeting, get_random_quote
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

# Initialize colorama
init(autoreset=True)

load_dotenv()


sol_buy_amount = Amount.sol_ui(.0001)
slippage = Amount.percent_ui(13)
priority_fee = Amount.sol_ui(.0001)
profit_limit = PnlOption(trigger_at_percent = Amount.percent_ui(600), allocation_percent = Amount.percent_ui(100))
stop_loss = PnlOption(trigger_at_percent = Amount.percent_ui(-15), allocation_percent = Amount.percent_ui(100))

async def main():
    # Colorful startup banner
    print(Fore.CYAN + "=" * 50)
    print(Fore.YELLOW + "🚀 SOLANA TRADING BOT INITIALIZING 🚀".center(50))
    print(Fore.CYAN + "=" * 50)
    
    print(Fore.GREEN + "Starting main function")
    http_uri = os.getenv('http_rpc_uri')
    wss_uri = os.getenv('wss_rpc_uri')
    keys_hash = os.getenv('payer_hash')
    wallet_address = os.getenv('wallet_address')
    if keys_hash:
        print(Fore.MAGENTA + "✓ Keys hash is available")
        solana_rpc_api = SolanaRpcApi(http_uri, wss_uri, http_uri, wallet_address)
        print(Fore.BLUE + "✓ Connected to Solana RPC")
        
        # Separator
        print(Fore.CYAN + "=" * 50)
        
        # Dynamic greeting
        print(Fore.GREEN + f"{get_time_greeting()}, Mr Mason!")
        
        # Random quote of the day
        print(Fore.MAGENTA + f"Quote of the Day: {get_random_quote()}")
        
        market_manager = MarketManager(solana_rpc_api)
        trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)

        try:
            while True:
                # Get SOL price
                sol_price = get_sol_price()
                
                # Get Wallet SOL balance
                sol_balance = market_manager.get_sol_balance(wallet_address)

                # Print SOL price if available
                if sol_price is not None:
                    print(f"Current SOL/USD Price: ${sol_price:.2f}")
                else:
                    print("Current SOL/USD Price: Unable to fetch")
                
                # Print SOL balance with USD value if price is available
                if sol_price is not None:
                    print(f"Wallet balance (SOL): {sol_balance:.4f} (${sol_balance * sol_price:.2f})")
                else:
                    print(f"Wallet balance (SOL): {sol_balance:.4f} (USD price unavailable)")
                
                

                # Get non-zero token accounts
                token_accounts = solana_rpc_api.get_non_zero_token_accounts()
                if token_accounts:
                    for token, amount in token_accounts.items():
                        print(f"Holding {amount} of {token}")
                else:
                    print("Your wallet might be empty now, but every epic journey begins with an empty canvas—get ready to paint your masterpiece!")
                
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
                        print("\nProgram interrupted. Exiting...")
                        break
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
                        print("\nProgram interrupted. Exiting...")
                        break
                    token_info = market_manager.get_token_info(token_address)
                    wallet_balance = trades_manager.get_account_balance(token_address)
                    print(f"Current wallet balance for {token_address}: {wallet_balance}")

                    try:
                        percentage_to_sell = float(input("Enter the percentage of tokens to sell (0-100): "))
                    except (KeyboardInterrupt, EOFError):
                        print("\nProgram interrupted. Exiting...")
                        break
                    tokens_to_sell = wallet_balance.value * (percentage_to_sell / 100)

                    order = Order(Order_Type.SELL, token_address, Amount.tokens_ui(tokens_to_sell, token_info.decimals_scale_factor), slippage, priority_fee)
                    tx_signature = trades_manager.execute_order(order, True)
                    print(f"Sell order executed for {tokens_to_sell} tokens. Transaction signature: {tx_signature}")

                elif choice == '3':
                    try:
                        contract_address = input("Enter the contract address to check balance: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nProgram interrupted. Exiting...")
                        break
                    balance = trades_manager.get_account_balance(contract_address)
                    print(f"Wallet balance: {balance}")

                elif choice == '4':
                    try:
                        token_address = input("Enter a token address to trade: ")
                    except (KeyboardInterrupt, EOFError):
                        print("\nProgram interrupted. Exiting...")
                        break
                    order = Order(Order_Type.BUY, token_address, sol_buy_amount, slippage, priority_fee)
                    tx_signature = trades_manager.execute_order(order, True)
                    token_info = market_manager.get_token_info(token_address)
                    transaction_info = trades_manager.get_order_transaction(tx_signature)

                    if transaction_info and transaction_info.token_diff > 0:
                        temp_calc = abs(transaction_info.sol_diff/transaction_info.token_diff)   
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
