import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.api import Client

load_dotenv()

HTTP_RPC_URI = os.getenv("http_rpc_uri", "https://api.mainnet-beta.solana.com")
WALLET_ADDRESS = os.getenv("wallet_address", "")  # base58-encoded public key

if not WALLET_ADDRESS:
    raise ValueError("Please set 'wallet_address' in your .env file")

# Initialize the RPC client and wallet pubkey
client = Client(HTTP_RPC_URI)
wallet_pubkey = Pubkey.from_string(WALLET_ADDRESS)

def fetch_all_transactions(pubkey):
    """
    Fetch all transaction signatures for the given public key.
    Uses pagination (the 'before' parameter) to retrieve all pages.
    """
    all_signatures = []
    before_sig = None

    while True:
        # You can adjust 'limit' up to 1,000 to reduce the number of requests
        response = client.get_signatures_for_address(pubkey, before=before_sig, limit=1000)
        batch = response.value

        if not batch:
            break

        all_signatures.extend(batch)
        before_sig = batch[-1].signature  # the last signature from this batch

    return all_signatures

def main():
    # 1. Fetch all transaction signatures
    tx_signatures = fetch_all_transactions(wallet_pubkey)
    print(f"Found {len(tx_signatures)} transactions for {WALLET_ADDRESS}")

    # 2. (Optional) Fetch full transaction details for each signature
    #    and do something (e.g., check "profit") with the data.
    # for tx_info in tx_signatures:
    #     signature = tx_info.signature
    #     tx_details = client.get_transaction(signature, "json")
    #     # Parse 'tx_details.value.transaction.meta' or logs, etc., to see
    #     # if there was a profit or loss in the wallet.

if __name__ == "__main__":
    main()
