from datetime import datetime
import random

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
    return random.choice(TRADING_QUOTES)
