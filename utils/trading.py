import asyncio
from TradingDTOs import Order, Order_Type, Amount
from config.config import MAX_FEE_RETRIES

async def buy_token(trades_manager, market_manager, token_address, sol_buy_amount, slippage, priority_fee):
    """
    Executes a buy order exactly as it appears in `main.py`.

    Args:
        trades_manager (TradesManager): The trades manager instance.
        market_manager (MarketManager): The market manager instance.
        sol_buy_amount (Amount): Amount of SOL to use for buying.
        slippage (Amount): Slippage tolerance.
        priority_fee (Amount): Priority fee for transaction.

    Returns:
        None
    """

    try:
        order = Order(Order_Type.BUY, token_address, sol_buy_amount, slippage, priority_fee)
        
        # Call sync method WITHOUT `await`
        tx_signature = trades_manager.execute_order(order, True)
        
        if not tx_signature:
            print("Buy order failed; no transaction signature returned.")
            return  # or use `continue` if inside a loop

        print(f"Buy order executed. Transaction signature: {tx_signature}")

        # Wait for 2 seconds to allow on-chain state to update
        await asyncio.sleep(2)  # This is fine, as you *are* in an async context presumably

        # Now fetch the token details
        # If these calls are also synchronous in your code, remove `await`.
        # If they're truly async, keep them. Adjust as needed:
        token_info = market_manager.get_token_info(token_address)
        # print(vars(token_info))

        transaction_info = trades_manager.get_order_transaction(tx_signature)

        # Check if transaction info is valid and tokens were bought
        if (MAX_FEE_RETRIES
            and transaction_info.token_diff
            and transaction_info.token_diff > 0):

            temp_calc = abs(transaction_info.sol_diff / transaction_info.token_diff)
            base_token_price = Amount.sol_ui(temp_calc)  # Convert from lamports to SOL
            tokens_bought = Amount.tokens_ui(transaction_info.token_diff, token_info.decimals_scale_factor)

            print(f"Tokens Bought: {tokens_bought.ToUiValue()} {token_address}")
            print(f"Purchase Price: {base_token_price.ToUiValue()} SOL per token")
        else:
            print("Transaction info not found or no tokens were bought.")
    except Exception as e:
        print(f"An error occurred: {e}")

async def sell_token(trades_manager, market_manager, token_address, slippage, priority_fee):
    """
    Executes a sell order for the given token address.

    Args:
        trades_manager (TradesManager): The trades manager instance.
        market_manager (MarketManager): The market manager instance.
        token_address (str): The token contract address.
        slippage (Amount): Slippage tolerance.
        priority_fee (Amount): Priority fee for transaction.

    Returns:
        None
    """
    try:
        token_info = market_manager.get_token_info(token_address)
        wallet_balance = trades_manager.get_account_balance(token_address)

        print(f"Current wallet balance for {token_address}: {wallet_balance}")

        try:
            percentage_to_sell = float(input("Enter the percentage of tokens to sell (0-100): "))
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            return

        tokens_to_sell = wallet_balance.value * (percentage_to_sell / 100)

        order = Order(Order_Type.SELL, token_address, Amount.tokens_ui(tokens_to_sell, token_info.decimals_scale_factor), slippage, priority_fee)
        tx_signature = trades_manager.execute_order(order, True)

        print(f"Sell order executed for {tokens_to_sell} tokens. Transaction signature: {tx_signature}")

    except Exception as e:
        print(f"An error occurred during the sell order: {e}")
