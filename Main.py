from MarketManager import MarketManager
from SolanaRpcApi import SolanaRpcApi
from TradesManager import TradesManager
from TradingDTOs import *
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

sol_buy_amount = Amount.sol_ui(.001)
slippage = Amount.percent_ui(13)
priority_fee = Amount.sol_ui(.0001)
profit_limit = PnlOption(trigger_at_percent = Amount.percent_ui(600), allocation_percent = Amount.percent_ui(100))
stop_loss = PnlOption(trigger_at_percent = Amount.percent_ui(-80), allocation_percent = Amount.percent_ui(100))

async def main():
    print("Starting main function")
    http_uri = os.getenv('http_rpc_uri')
    wss_uri = os.getenv('wss_rpc_uri')
    keys_hash = os.getenv('payer_hash')
    wallet_address = os.getenv('wallet_address')
    if keys_hash:
        print("Keys hash is available")
        solana_rpc_api = SolanaRpcApi(http_uri, wss_uri)
        print("Connected to Solana RPC")
        market_manager = MarketManager(solana_rpc_api)
        trades_manager = TradesManager(keys_hash, solana_rpc_api, market_manager)

        while True:
            sol_balance = market_manager.get_sol_balance(wallet_address)
            print(f"Wallet balance (SOL): {sol_balance:.4f}")
            print("\nChoose an option:")
            print("1. Buy a token")
            print("2. Sell a token")
            print("3. Get wallet balance")
            print("4. Execute order with limits and stops")
            choice = input("Enter your choice (1-4): ")

            if choice == '1':
                token_address = input("Enter a token address to buy: ")
                order = Order(Order_Type.BUY, token_address, sol_buy_amount, slippage, priority_fee)
                tx_signature = trades_manager.execute_order(order, True)
                print(f"Buy order executed. Transaction signature: {tx_signature}")

            elif choice == '2':
                token_address = input("Enter a token address to sell: ")
                token_info = market_manager.get_token_info(token_address)
                wallet_balance = trades_manager.get_account_balance(token_address)
                print(f"Current wallet balance for {token_address}: {wallet_balance}")

                percentage_to_sell = float(input("Enter the percentage of tokens to sell (0-100): "))
                tokens_to_sell = wallet_balance.value * (percentage_to_sell / 100)

                order = Order(Order_Type.SELL, token_address, Amount.tokens_ui(tokens_to_sell, token_info.decimals_scale_factor), slippage, priority_fee)
                tx_signature = trades_manager.execute_order(order, True)
                print(f"Sell order executed for {tokens_to_sell} tokens. Transaction signature: {tx_signature}")

            elif choice == '3':
                contract_address = input("Enter the contract address to check balance: ")
                balance = trades_manager.get_account_balance(contract_address)
                print(f"Wallet balance: {balance}")

            elif choice == '4':
                token_address = input("Enter a token address to trade: ")
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

            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

asyncio.run(main())