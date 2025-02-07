import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.api import Client

def main():
    load_dotenv()
    http_uri = os.getenv("http_rpc_uri", "https://api.mainnet-beta.solana.com")
    wallet_address = os.getenv("wallet_address", "")  # Your base58 pubkey string
    
    if not wallet_address:
        raise ValueError("Please set 'wallet_address' in .env")

    wallet_pubkey = Pubkey.from_string(wallet_address)
    client = Client(http_uri)

    # Fetch transaction signatures for the given pubkey
    signatures_resp = client.get_signatures_for_address(wallet_pubkey)
    signatures = signatures_resp.value

    if not signatures:
        print("No transactions found for this wallet.")
        return

    total = len(signatures)
    success_count = 0

    # Check each transaction's meta.err
    for tx_info in signatures:
        tx_sig = tx_info.signature
        tx_details_resp = client.get_transaction(tx_sig, "json")
        if (tx_details_resp.value 
                and tx_details_resp.value.transaction 
                and tx_details_resp.value.transaction.meta 
                and tx_details_resp.value.transaction.meta.err is None):
            success_count += 1

    win_rate = (success_count / total) * 100
    print(f"Total TXs: {total}, Successful TXs: {success_count}, Win Rate: {win_rate:.2f}%")

if __name__ == "__main__":
    main()
