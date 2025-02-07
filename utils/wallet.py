import copy

def update_and_print_token_holdings(token_accounts, previous_token_accounts_dict):
    """
    Prints token holdings and updates the previous token state.
    
    Args:
        token_accounts (list): List of token balances (each item is a dict with 'mint' and 'balance').
        previous_token_accounts_dict (list): Previously stored token balances.

    Returns:
        list: Updated `previous_token_accounts_dict`
    """
    if token_accounts:
        # If first time OR any changes compared to previous state
        if previous_token_accounts_dict is None or token_accounts != previous_token_accounts_dict:
            print("🔹 Token Holdings:")
            
            # Loop through token accounts and print balances
            for token_info in token_accounts:
                mint = token_info['mint']
                balance = token_info['balance']
                print(f"Holding {balance} of {mint}")

            # Update previous_token_accounts_dict to match what we have now
            return copy.deepcopy(token_accounts)
        else:
            print("🛑 No token balance changes detected.")
    else:
        # No token accounts at all
        if previous_token_accounts_dict is None or previous_token_accounts_dict != {}:
            print("🌱 Your wallet might be empty now, but every epic journey begins with an empty canvas—get ready to paint your masterpiece! 🎨✨")
            return []
        else:
            print("🛑 No token balance changes detected.")
    
    return previous_token_accounts_dict  # Return the previous state unchanged
