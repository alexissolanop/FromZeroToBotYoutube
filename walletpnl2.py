import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.transaction import Transaction
import time  # Import the time module

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
    Fetch all transaction signatures.
    """
    all_signatures = []
    before_sig = None

    while True:
        response = client.get_signatures_for_address(pubkey, before=before_sig, limit=1000)
        batch = response.value

        if not batch:
            break

        all_signatures.extend(batch)
        before_sig = batch[-1].signature

    return all_signatures

def get_transaction_with_retry(signature, max_retries=5, backoff_factor=2):
    """Fetches a transaction with retries and exponential backoff."""
    for attempt in range(max_retries):
        try:
            # Use "jsonParsed" encoding and include the max_supported_transaction_version parameter
            tx_details_response = client.get_transaction(
                signature,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            return tx_details_response  # Return immediately if successful
        except Exception as e:
            wait_time = backoff_factor ** attempt  # Exponential backoff
            print(f"Error fetching transaction {signature} (attempt {attempt + 1}/{max_retries}): {e}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    print(f"Failed to fetch transaction {signature} after {max_retries} attempts.")
    return None  # Return None if all retries fail

def main():
    tx_signatures = fetch_all_transactions(wallet_pubkey)
    print(f"Found {len(tx_signatures)} transactions for {WALLET_ADDRESS}")

    for tx_info in tx_signatures:
        signature = tx_info.signature

        # Use the retry function to get transaction details
        tx_details_response = get_transaction_with_retry(signature)

        if tx_details_response is None or tx_details_response.value is None:
            # Transaction failed even after retries, skip it
            continue

        tx_details = tx_details_response.value

        # Check if metadata exists
        if tx_details and hasattr(tx_details, 'meta') and tx_details.meta:
            if hasattr(tx_details.meta, 'pre_balances') and tx_details.meta.pre_balances:
                pre_balances = tx_details.meta.pre_balances
                print(f"Tx {signature}: Pre-balances: {pre_balances}")
            else:
                print(f"Tx {signature}: No preBalances found.")

            if hasattr(tx_details.meta, 'post_balances') and tx_details.meta.post_balances:
                post_balances = tx_details.meta.post_balances
                print(f"Tx {signature}: Post-balances: {post_balances}")

                if len(pre_balances) > 0 and len(post_balances) > 0:
                    sol_change = post_balances[0] - pre_balances[0]
                    print(f"  SOL balance change: {sol_change / 10**9} SOL")
            else:
                print(f"Tx {signature}: No postBalances found.")
        else:
            print(f"Transaction {signature} meta is None or missing.")

if __name__ == "__main__":
    main()
