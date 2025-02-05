from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
import os
from dotenv import load_dotenv

load_dotenv()
http_uri = os.getenv('http_rpc_uri')
# Initialize the Solana client
client = Client(http_uri)

# Replace with the wallet's public key you want to query (from your .env file)
wallet_address = os.getenv('wallet_address')
wallet_pubkey = Pubkey.from_string(wallet_address)

# Token Program ID for SPL Tokens
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

# Set up the options for the token account query
opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)

# Fetch token accounts in parsed JSON format
response = client.get_token_accounts_by_owner_json_parsed(wallet_pubkey, opts)

printed_any = False  # Flag to track if any token with non-zero balance is printed

if response.value:
    for token_account in response.value:
        account_info = token_account.account.data.parsed["info"]
        token_balance = account_info["tokenAmount"]["uiAmount"]
        # Check if token_balance exists and is greater than 0
        if token_balance and token_balance > 0:
            printed_any = True
            mint_address = account_info["mint"]
            print(f"Token Mint: {mint_address}")
            print(f"Token Balance: {token_balance}\n")

if not printed_any:
    print("No token accounts with non-zero balance found for this wallet.")
