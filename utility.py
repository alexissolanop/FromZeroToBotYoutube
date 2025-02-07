import random
import os
import platform
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get CoinMarketCap API key from .env
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API")

# Load trading quotes
with open('FromZeroToBotYoutube/trading_quotes.txt', 'r') as f:
    TRADING_QUOTES = f.read().splitlines()

def get_time_greeting():
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"

def get_random_quote():
    """Returns a random trading quote."""
    return random.choice(TRADING_QUOTES)

def colorize_sol(sol_amount):
    """
    Returns a colorized string representation of SOL amount for terminal display.
    - 0 – 0.5 SOL → 🔴 Red
    - 0.5 – 1 SOL → 🟠 Orange
    - 1 – 3 SOL → 🟡 Yellow
    - 3 – 10 SOL → 🟢 Green
    - 10+ SOL → 🔵 Cyan (Best)
    """
    if sol_amount < 0.5:
        color = "\033[91m"  # Red
    elif sol_amount < 1:
        color = "\033[93m"  # Orange
    elif sol_amount < 3:
        color = "\033[33m"  # Yellow
    elif sol_amount < 10:
        color = "\033[92m"  # Green
    else:
        color = "\033[96m"  # Cyan (Best)

    reset = "\033[0m"  # Reset color
    return f"{color}{sol_amount:.5f} SOL{reset}"

def colorize_greed_index(index_value):
    """
    Colorizes the Fear and Greed Index for terminal display.
    - 0 – 24  → 🔴 Red (Extreme Fear)
    - 25 – 49 → 🟠 Orange (Fear)
    - 50 – 54 → 🟡 Yellow (Neutral)
    - 55 – 74 → 🟢 Green (Greed)
    - 75 – 100 → 🔵 Cyan (Extreme Greed)
    """
    if index_value <= 24:
        color = "\033[91m"  # Red
    elif index_value <= 49:
        color = "\033[93m"  # Orange
    elif index_value <= 54:
        color = "\033[33m"  # Yellow
    elif index_value <= 74:
        color = "\033[92m"  # Green
    else:
        color = "\033[96m"  # Cyan (Best)

    reset = "\033[0m"  # Reset color
    return f"{color}{index_value}{reset}"

def get_fear_greed_index():
    """
    Fetches the latest Fear and Greed Index value from CoinMarketCap API.
    Returns:
        tuple: (index_value, classification) or (None, None) if API fails.
    """
    url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"
    headers = {
        "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        data = response.json()

        if "data" in data and data["data"]:
            latest_entry = data["data"][0]
            index_value = latest_entry["value"]
            classification = latest_entry["value_classification"]
            return colorize_greed_index(index_value), classification
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Fear and Greed Index: {e}")
        return None, None

