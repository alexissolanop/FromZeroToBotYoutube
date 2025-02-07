import time
from SolanaUSDPrice import get_sol_price
from utility import get_fear_greed_index

def update_sol_price(sol_price, previous_sol_price, last_price_update, price_refresh_interval):
    """
    Updates the SOL price every defined interval.

    Args:
        sol_price (float): Current SOL price.
        previous_sol_price (float): Previous SOL price.
        last_price_update (float): Last timestamp when the price was updated.
        price_refresh_interval (int): Time interval (in seconds) for updates.

    Returns:
        tuple: (updated sol_price, updated last_price_update)
    """
    current_time = time.time()

    if current_time - last_price_update > price_refresh_interval:
        try:
            new_sol_price = get_sol_price()
            if new_sol_price != previous_sol_price:
                print(f"Updated SOL price: {new_sol_price}")
                return new_sol_price, current_time
        except Exception as e:
            print(f"Error refreshing SOL price: {e}")

    return sol_price, last_price_update

def update_fear_greed_index(previous_fear_greed, last_fear_greed_update, fear_greed_refresh_interval):
    """
    Updates the Fear & Greed Index every defined interval.

    Args:
        previous_fear_greed (str): Previous Fear & Greed Index.
        last_fear_greed_update (float): Last timestamp when the index was updated.
        fear_greed_refresh_interval (int): Time interval (in seconds) for updates.

    Returns:
        tuple: (updated colorized_index, updated classification, updated last_fear_greed_update)
    """
    current_time = time.time()

    if current_time - last_fear_greed_update > fear_greed_refresh_interval:
        try:
            new_index, new_classification = get_fear_greed_index()
            if new_index != previous_fear_greed:
                print(f"Updated Fear & Greed: {new_index} - {new_classification}")
                return new_index, new_classification, current_time
        except Exception as e:
            print(f"Error updating fear/greed: {e}")

    return previous_fear_greed, None, last_fear_greed_update
