import os
import platform
from colorama import Fore
from utility import colorize_sol


def clear_terminal():
    """Clears the terminal output across platforms"""
    if platform.system().lower() == 'windows':
        os.system('cls')
    else:
        os.system('clear')

def print_startup_banner():
    """Prints the startup banner"""
    print(Fore.CYAN + "=" * 50)
    print(Fore.YELLOW + "🚀 SOLANA TRADING BOT INITIALIZING 🚀".center(50))
    print(Fore.CYAN + "=" * 50)
    print(Fore.GREEN + "Starting main function")

def print_separator():
    """Prints a cyan separator line for visual clarity in the terminal."""
    print(Fore.CYAN + "=" * 50)

def print_dashboard_header():
    """Prints the dashboard header"""
    print(Fore.YELLOW + "🚀 SOLANA TRADING BOT DASHBOARD 🚀".center(50))
    print(Fore.CYAN + "=" * 50)

def print_quote_of_the_day(quote):
    """Prints a random trading quote"""
    print(Fore.MAGENTA + f"Quote of the Day: {quote}")

def print_fear_greed_index(colorized_index, classification):
    """Prints the Fear & Greed Index"""
    if colorized_index:
        print(f"📊 Initial Market Mood: {colorized_index} ({classification})")
    else:
        print("🚫 Market Mood: Mysterious Signal Lost 🛸")

def print_initial_sol_price(sol_price):
    """Prints the initial SOL price in a formatted way."""
    if sol_price:
        print(f"💰 Initial SOL Price: ${sol_price:.2f} 🚀")
    else:
        print("💔 SOL Price: Unable to fetch 🕵️")

def print_wallet_balance(sol_balance, sol_price):
    """Prints the wallet balance in a formatted way, including USD equivalent if available."""
    colored_balance = colorize_sol(sol_balance)
    
    if sol_price:
        print(f"💰 Wallet Balance: {colored_balance} (${sol_balance * sol_price:.2f})")
    else:
        print(f"💰 Wallet Balance: {colored_balance} (USD price unavailable)")


def should_clear_terminal(sol_price, previous_sol_price, colorized_index, previous_fear_greed, token_accounts, previous_token_accounts_dict):
    """
    Determines whether the terminal should be cleared to prevent unnecessary flickering.

    Args:
        sol_price (float): Current SOL price.
        previous_sol_price (float): Previous SOL price.
        colorized_index (str): Current Fear & Greed Index (colorized).
        previous_fear_greed (str): Previous Fear & Greed Index.
        token_accounts (list): List of token balances.
        previous_token_accounts_dict (list): Previous token balances.

    Returns:
        bool: True if the terminal should be cleared, False otherwise.
    """
    # Check if SOL price or Fear & Greed index changed
    if sol_price != previous_sol_price or colorized_index != previous_fear_greed:
        return True

    # Check if token holdings have changed
    if previous_token_accounts_dict is not None:
        if [tuple(sorted(d.items())) for d in token_accounts] != [tuple(sorted(d.items())) for d in previous_token_accounts_dict]:
            return True
    
    return False
