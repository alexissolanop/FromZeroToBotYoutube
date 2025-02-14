import os
import time
import asyncio
import logging

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

from aiohttp import ClientSession, ClientResponseError, ClientTimeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from solders.pubkey import Pubkey
from solders.transaction_status import EncodedTransactionWithStatusMeta
from solana.rpc.async_api import AsyncClient
from solana.rpc.core import RPCException
from solana.rpc.commitment import Confirmed


# ------------------------------------------------------------------------------
# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Load environment variables
load_dotenv()
RPC_URL = os.getenv("http_rpc_uri")
if not RPC_URL:
    raise ValueError("Please set 'http_rpc_uri' in your .env or hardcode it.")

WALLET_ADDRESS = os.getenv("wallet_address")
if not WALLET_ADDRESS:
    raise ValueError("Please set 'wallet_address' in your .env or hardcode it.")

SLEEP_ON_429 = int(os.getenv("SLEEP_ON_429", "30")) # Default to 30
CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT", "10")) # Default to 10

# ------------------------------------------------------------------------------
# Example DEX Program IDs
DEX_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium",
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Orca",
    "JUP6LkMFYHzfv2uY2FU5kh8USw4HcHUuGxvmfSUMvx5Y": "Jupiter",
    "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K":  "Meteora",
}
# ------------------------------------------------------------------------------


@dataclass
class TransactionInfo:
    """Simple container for transaction metadata."""
    signature: str
    slot: Optional[int]
    block_time: Optional[int]
    dex_program: str            # e.g. "Raydium" if recognized
    logs: List[str] = field(default_factory=list)
    account_keys: List[str] = field(default_factory=list)


class SingleWalletAnalyzer:
    def __init__(self, rpc_url: str, concurrency_limit: int = 10):
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        self.session: Optional[ClientSession] = None
        self.concurrency_limit = concurrency_limit
        self.sem = asyncio.Semaphore(concurrency_limit)


    async def start_session(self):
        """Initialize aiohttp ClientSession if not already created."""
        if not self.session or self.session.closed:
            self.session = ClientSession(timeout=ClientTimeout(total=10))  # Add timeout
            self.client._provider._session = self.session

    async def close_session(self):
        """Close the aiohttp session if it exists."""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((RPCException, ClientResponseError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _make_rpc_request(self, method: str, *args, **kwargs) -> Any:
        """
        Generic wrapper to call Solana's RPC with Tenacity-based retries.
        Handles 429 rate-limit by sleeping & re-raising for exponential backoff.
        """
        await self.start_session()
        try:
            if method == "get_signatures_for_address":
                resp = await self.client.get_signatures_for_address(*args, **kwargs)
            elif method == "get_transaction":
                resp = await self.client.get_transaction(*args, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # If no response or an explicit 'error', raise to trigger retry
            if not resp:
                raise RPCException(f"Null response from RPC for method: {method}")

            if hasattr(resp, "error") and resp.error is not None:
                raise RPCException(f"RPC Error: {resp.error} for method {method}")

            return resp.value
        except ClientResponseError as cre:
            if cre.status == 429:
                logger.error(f"Got 429 Too Many Requests - sleeping {SLEEP_ON_429}s then re-raising for backoff... Method: {method}")
                time.sleep(SLEEP_ON_429)
            raise
        except Exception as e:
            logger.exception(f"RPC request error for method {method}: {e}")
            raise

    async def fetch_signatures(self, wallet_address: str, limit: int = 50, before: Optional[str] = None):
        """
        Fetch up to 'limit' signatures for the specified wallet, with optional pagination.
        """
        pubkey = Pubkey.from_string(wallet_address)
        resp_value = await self._make_rpc_request(
            "get_signatures_for_address",
            pubkey,
            limit=limit,
            before=before,  # Add 'before' for pagination
            commitment=Confirmed,
        )
        if not resp_value:
            return []
        return resp_value  # It's a list of signature info objects


    async def _fetch_single_transaction(self, sig_info):
        """Helper function to fetch a single transaction with concurrency control."""
        async with self.sem:
            sig = sig_info.signature
            return await self._make_rpc_request(
                    "get_transaction",
                    sig,
                    encoding="jsonParsed",
                    max_supported_transaction_version=0,
                )

    def _parse_single_transaction(
        self,
        tx_data: EncodedTransactionWithStatusMeta,
        sig_str: str,
        slot: Optional[int],
        block_time: Optional[int],
    ) -> Optional[TransactionInfo]:
        """
        Decode the transaction from 'jsonParsed', extract account keys & logs,
        detect if a known DEX is involved.
        """
        try:
            # 'tx_data.transaction' should already be a dictionary if we used "jsonParsed"
            if not tx_data.transaction or not isinstance(tx_data.transaction, dict):
                logger.warning(f"Transaction is not a dict. Possibly 'base64'? Skipping. Signature={sig_str}")
                return None

            transaction_dict = tx_data.transaction
            message_dict = transaction_dict.get("message", {})
            account_keys = message_dict.get("accountKeys", [])

            # Extract logs from tx_data.meta
            logs = tx_data.meta.log_messages if tx_data.meta and tx_data.meta.log_messages else []

            # Simple DEX detection
            dex_program_name = next((name for program_id, name in DEX_PROGRAMS.items() if program_id in account_keys), "")

            return TransactionInfo(
                signature=sig_str,
                slot=slot,
                block_time=block_time,
                dex_program=dex_program_name,
                logs=logs,
                account_keys=account_keys,
            )

        except Exception as e:
            logger.exception(f"Error parsing transaction {sig_str}: {e}")
            return None



    async def fetch_and_parse_transactions(self, wallet_address: str, limit: int = 50) -> List[TransactionInfo]:
        """
        1) Get up to `limit` signatures, with pagination support
        2) fetch each transaction (with `encoding="jsonParsed"`),
        3) parse it for account keys, logs, and DEX detection.
        """
        all_sig_infos = []
        last_signature = None  # For pagination

        while True:
            sig_infos = await self.fetch_signatures(wallet_address, limit=limit, before=last_signature)
            logger.info(f"Fetched {len(sig_infos)} signature(s) for {wallet_address}.")

            if not sig_infos:
                break  # No more signatures

            all_sig_infos.extend(sig_infos)
            last_signature = sig_infos[-1].signature  # Get the oldest signature for the next batch

            if len(sig_infos) < limit:  # We got fewer than requested, likely the last batch
                break
            if len(all_sig_infos) >= limit: # In case limit is larger than RPC limit
                break


        # Limit the total signatures fetched to the user requested limit
        all_sig_infos = all_sig_infos[:limit]


        tasks = [self._fetch_single_transaction(sig_info) for sig_info in all_sig_infos]
        raw_txs = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[TransactionInfo] = []


        for sig_info, tx_data in zip(all_sig_infos, raw_txs):
            signature_str = sig_info.signature
            slot = sig_info.slot
            block_time = sig_info.block_time

            if isinstance(tx_data, Exception):
                logger.error(f"Error fetching transaction {signature_str}: {tx_data}")
                continue
            if not tx_data:
                continue

            parsed = self._parse_single_transaction(tx_data, signature_str, slot, block_time)
            if parsed:
                results.append(parsed)

        return results




async def main():
    analyzer = SingleWalletAnalyzer(RPC_URL, CONCURRENCY_LIMIT)
    try:
        # Fetch & parse up to 50 transactions, with pagination
        limit = 50
        logger.info(f"Analyzing wallet {WALLET_ADDRESS} with limit={limit} at RPC={RPC_URL}")
        tx_infos = await analyzer.fetch_and_parse_transactions(WALLET_ADDRESS, limit=limit)

        print(f"\n=== Summary for Wallet {WALLET_ADDRESS} ===")
        print(f"Parsed {len(tx_infos)} transaction(s).")

        # Count how many have a recognized DEX program
        dex_count = sum(1 for tx in tx_infos if tx.dex_program)
        print(f"{dex_count} transaction(s) with recognized DEX program.\n")

        # Print some details
        for idx, txi in enumerate(tx_infos, start=1):
            print(f"{idx:2d}. Sig={txi.signature}, Slot={txi.slot}, Time={txi.block_time}, DEX={txi.dex_program}")
            if txi.dex_program:
                print(f"     => Logs: {txi.logs}")
                print(f"     => Keys: {txi.account_keys}")

    finally:
        await analyzer.close_session()


if __name__ == "__main__":
    asyncio.run(main())