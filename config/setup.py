import os
from dotenv import load_dotenv
from colorama import init

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Read environment variables
http_uri = os.getenv('http_rpc_uri')
wss_uri = os.getenv('wss_rpc_uri')
keys_hash = os.getenv('payer_hash')
wallet_address = os.getenv('wallet_address')