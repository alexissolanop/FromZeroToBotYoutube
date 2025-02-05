from jsonrpcclient import request, parse, Ok, Error
import os
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solana.rpc.commitment import Confirmed, Processed, Finalized
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID
from solders.transaction import VersionedTransaction
from solana.rpc.types import TokenAccountOpts
from TradingDTOs import SwapTransactionInfo
import requests


class SolanaRpcApi:

    def __init__(self, rpc_uri, wss_uri, http_uri, wallet_address, endpoint=None):
        load_dotenv()
        self.rpc_uri = rpc_uri
        self.wss_uri = wss_uri
        self.client = Client(http_uri)
        self.wallet_address = wallet_address
        self.wallet_pubkey = Pubkey.from_string(wallet_address)
        self.TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    
    def run_rpc_method(self, request_name: str, params):
        json_request = request(request_name, params=params)
        response = requests.post(self.rpc_uri, json=json_request)

        parsed = parse(response.json())

        if isinstance(parsed, Error): 
            return None
        else:
            return parsed

    def get_transaction(self, tx_signature: str):
        response = self.run_rpc_method("getTransaction", [tx_signature,
                                        {'encoding': 'jsonParsed', 'maxSupportedTransactionVersion':0 }])
        
        if response:
            return response.result

    def get_account_balance(self, account_address: str)->float:
        response = self.run_rpc_method("getBalance", [ account_address ])
        
        if response:
            return response.result['value']
        else:
            return None

    def send_transaction(self, transaction: VersionedTransaction, maxTries=0):
        transaction_bytes = bytes(transaction)

        return self.client.send_raw_transaction(transaction_bytes, opts=TxOpts(skip_confirmation=True,
                                                                               skip_preflight = True,
                                                                            #preflight_commitment=Processed,
                                                                            max_retries=maxTries))
    
    def get_token_account_balance(self, associated_token_address: str):
        response = self.run_rpc_method("getTokenAccountBalance", [ associated_token_address ])
        
        if response:
            return response.result['value']['uiAmount']
        else:
            return None
        
    def get_non_zero_token_accounts(self):
        """
        Returns a list of dictionaries, each containing 'mint' and 'balance'
        for tokens held by the wallet with a non-zero balance.
        """
        opts = TokenAccountOpts(program_id=self.TOKEN_PROGRAM_ID)
        response = self.client.get_token_accounts_by_owner_json_parsed(self.wallet_pubkey, opts)
        token_accounts = []
        if response.value:
            for token_account in response.value:
                account_info = token_account.account.data.parsed["info"]
                token_balance = account_info["tokenAmount"]["uiAmount"]
                if token_balance and token_balance > 0:
                    mint_address = account_info["mint"]
                    token_accounts.append({
                        "mint": mint_address,
                        "balance": token_balance
                    })
        return token_accounts

    def get_associated_token_account_address(owner_address: str, mint_address: str)->str:
        mint_address_pk = Pubkey.from_string(mint_address)        
        owner_address_pk = Pubkey.from_string(owner_address)

        # Calculate the associated token address
        seeds = [bytes(owner_address_pk), bytes(TOKEN_PROGRAM_ID), bytes(mint_address_pk)]
        account_pubkey = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

        return str(account_pubkey)
    
    @staticmethod
    def parse_swap_transaction(owner_address: str, transaction_data: dict):
        accounts = transaction_data['transaction']['message']['accountKeys']

        pre_sol_balances = transaction_data['meta']['preBalances']
        post_sol_balances = transaction_data['meta']['postBalances']
        pre_token_balances = transaction_data['meta']['preTokenBalances']
        post_token_balances = transaction_data['meta']['postTokenBalances']

        transaction_info = SwapTransactionInfo()
        num_accounts = len(accounts)

        if num_accounts == len(pre_sol_balances) and num_accounts == len(post_sol_balances):
            account_found = False

            for i in range(num_accounts):
                if owner_address == accounts[i]['pubkey']:
                    transaction_info.payer_address = owner_address
                    transaction_info.sol_diff = post_sol_balances[i]-pre_sol_balances[i]
                    account_found = True
                    break
            
            if account_found:
                account_found = False

                pre_token_balance = SolanaRpcApi._extract_token_balance(owner_address, pre_token_balances)
                post_token_balance = SolanaRpcApi._extract_token_balance(owner_address, post_token_balances)

                if pre_token_balance:
                    pre_token_amount = pre_token_balance['uiTokenAmount']['uiAmount']
                else:
                    pre_token_amount = 0
                
                if post_token_balance:
                    post_token_amount = post_token_balance['uiTokenAmount']['uiAmount']
                else:
                    post_token_amount = 0

                transaction_info.transaction_signature = transaction_data['transaction']['signatures'][0]
                transaction_info.token_address = post_token_balance['mint']

                token_account_index = post_token_balance['accountIndex']
                transaction_info.payer_token_account_address = accounts[token_account_index]['pubkey']
                transaction_info.payer_token_ui_balance = post_token_amount

                if pre_token_amount and post_token_amount:
                    transaction_info.token_diff = post_token_amount-pre_token_amount
                elif pre_token_amount:
                    transaction_info.token_diff = -pre_token_amount
                else:
                    transaction_info.token_diff = post_token_amount

                return transaction_info

    @staticmethod
    def _extract_token_balance(owner_address: str, token_balance_dict: dict):   
        for token_balance in token_balance_dict:
            if owner_address == token_balance['owner']:
                return token_balance

    @staticmethod
    def get_account_subscribe_request(account_address: str):
         return {
                "jsonrpc": "2.0",
                "id": 420,
                "method": "accountSubscribe",
                "params": [
                account_address, # pubkey of account we want to subscribe to
                {
                    "encoding": "jsonParsed", # base58, base64, base65+zstd, jsonParsed
                    "commitment": "confirmed", # defaults to finalized if unset
                }
            ]
        }           
    
    #Creates a transaction sub request
    @staticmethod
    def get_signature_request(signature: str):
        return  {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "signatureSubscribe",
                "params": [
                signature, # pubkey of account we want to subscribe to #TODO put in constructor
                {
                    "commitment": "confirmed",
                    "enableReceivedNotification": False
                }
            ]
        }
