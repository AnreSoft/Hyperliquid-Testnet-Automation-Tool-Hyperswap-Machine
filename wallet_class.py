import random
import requests
from config import *
import asyncio
from web3 import Web3
from web3.exceptions import TransactionNotFound
import time
import logging
import os
import json


def web3_init(proxy):
    """
    Initializes a Web3 instance with an optional proxy.

    Args:
        proxy (str): Proxy URL in the format "http://user:pass@ip:port".

    Returns:
        Web3: A Web3 instance connected to the specified RPC URL.
    """
    session = requests.Session()
    if proxy is not None:
        proxy = {"http": proxy, "https": proxy}
        session.proxies = proxy
    web3 = Web3(Web3.HTTPProvider(RPC_URL, session=session))
    return web3


class Wallet:
    def __init__(self, private_key, address, ref_address, abi_router, abi_factory, proxy=None):
        """
        Initializes a Wallet instance.

        Args:
            private_key (str): The private key of the wallet.
            address (str): The wallet address.
            ref_address (str): The referral address (optional).
            abi_router (list): ABI of the router contract.
            abi_factory (list): ABI of the factory contract.
            proxy (str): Proxy URL (optional).
        """
        self.private_key = private_key
        self.address = Web3.to_checksum_address(address)
        self.ref_address = Web3.to_checksum_address(ref_address) if ref_address else None
        self.web3 = web3_init(proxy)  # Initialize Web3
        self.router_contract = self.web3.eth.contract(address=HYPERSWAP_CONTRACT_ADDRESS, abi=abi_router)
        self.factory_contract = self.web3.eth.contract(address=HYPERSWAP_FACTORY_ADDRESS, abi=abi_factory)

    async def get_native_balance(self):
        """
        Retrieves the balance of the native token (HYPE/ETH) for the wallet.

        Returns:
            float: Balance in ETH (HYPE).
        """
        try:
            raw_balance = await asyncio.to_thread(self.web3.eth.get_balance, self.address)
            balance = raw_balance / 10 ** 18
            return balance
        except Exception as e:
            logging.error(f"Error retrieving native balance: {e}")
            return None

    async def get_token_balance(self, token_name, token_address):
        """
        Retrieves the balance of a specific token for the wallet.

        Args:
            token_name (str): The name of the token.
            token_address (str): The contract address of the token.

        Returns:
            float: Token balance in a human-readable format.
        """
        try:
            abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }
            ]

            token_contract = self.web3.eth.contract(address=token_address, abi=abi)
            raw_balance = await asyncio.to_thread(token_contract.functions.balanceOf(self.address).call)
            decimals = await self.get_token_decimals(token_address)

            if decimals is None:
                logging.warning(f"Skipping token {token_name} due to missing decimals.")
                return None

            balance = await self.normalize_amount(raw_balance, decimals)
            return balance

        except Exception as e:
            logging.error(f"Error retrieving balance for token {token_name}: {e}")
            return None

    async def get_all_balances(self):
        """
        Retrieves the balances of all tokens in the TOKENS dictionary and saves them to a JSON file.
        """
        balances = {}

        hype_balance = await self.get_native_balance()
        if hype_balance is not None:
            balances["HYPE"] = hype_balance

        for token_name, token_address in TOKENS.items():
            balance = await self.get_token_balance(token_name, token_address)
            if balance is not None:
                balances[token_name] = balance

        os.makedirs("balances", exist_ok=True)
        file_path = f"balances/{self.address}.json"

        try:
            with open(file_path, "w") as file:
                json.dump(balances, file, indent=4)
            logging.info(f"Balances saved successfully to {file_path}")
        except Exception as e:
            logging.error(f"Error saving balances to file: {e}")

    async def wait_for_transaction_receipt(self, tx_hash, timeout=300, retries=3):
        """
        Asynchronously waits for a transaction receipt with retries.

        Args:
            tx_hash (str): The transaction hash.
            timeout (int): Maximum time to wait in seconds.
            retries (int): Number of retry attempts.

        Returns:
            dict: The transaction receipt.

        Raises:
            TransactionNotFound: If the transaction is not found after retries.
        """
        for attempt in range(retries):
            try:
                start_time = time.time()
                while True:
                    receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt is not None:
                        return receipt
                    if time.time() - start_time > timeout:
                        raise TransactionNotFound(f"Transaction {tx_hash.hex()} not found in {timeout} seconds.")
                    await asyncio.sleep(5)  # Check every 5 seconds
            except TransactionNotFound as e:
                if attempt == retries - 1:
                    logging.error(f"Transaction {tx_hash.hex()} not found after {retries} attempts.")
                    raise e
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
                await asyncio.sleep(10)  # Wait before retrying

    async def check_balance(self, token_address):
        """
        Asynchronously checks the token balance of the wallet.

        Args:
            token_address (str): The token contract address.

        Returns:
            float: The normalized token balance.
        """
        token_contract = self.web3.eth.contract(address=token_address, abi=[
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ])

        balance = await asyncio.to_thread(token_contract.functions.balanceOf(self.address).call)
        decimal = await self.get_token_decimals(token_address)
        balance = await self.normalize_amount(balance, decimal)

        logging.info(f"Wallet {self.address} | Balance of {token_address}: {balance}")
        return balance

    async def check_allowance(self, token_address, owner, spender):
        """
        Asynchronously checks the token allowance for a spender.

        Args:
            token_address (str): The token contract address.
            owner (str): The owner's address.
            spender (str): The spender's address.

        Returns:
            int: The allowance amount.
        """
        token_contract = self.web3.eth.contract(address=token_address, abi=[
            {
                "constant": True,
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ])

        allowance = await asyncio.to_thread(token_contract.functions.allowance(owner, spender).call)
        logging.info(f"Wallet {self.address} | Allowance for {spender}: {allowance}")
        return allowance

    async def swap_weth_to_token(self, token_out, amount_in, amount_out_min):
        """
        Swaps WETH for a specified token.

        Args:
            token_out (str): The symbol of the output token.
            amount_in (float): The amount of WETH to swap.
            amount_out_min (float): The minimum amount of output tokens to receive.

        Returns:
            dict: The transaction receipt, or None if the transaction fails.
        """
        logging.info(f"Wallet {self.address} | Starting swap: {amount_in} WETH -> {token_out}")

        token_in_address = TOKENS["WETH"]
        token_out_address = TOKENS[token_out]

        path = [token_in_address, token_out_address]
        recipient = self.address
        referrer = self.ref_address if self.ref_address else self.address

        nonce = self.web3.eth.get_transaction_count(recipient)
        deadline = int(self.web3.eth.get_block("latest")["timestamp"] + 300)

        try:
            transaction = self.router_contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                Web3.to_wei(amount_out_min, "ether"),
                path,
                recipient,
                referrer,
                deadline
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'value': Web3.to_wei(amount_in, "ether"),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Transaction sent: {tx_hash.hex()}")

            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Transaction confirmed in block {receipt['blockNumber']}")
            return receipt
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during swap: {e}")
            return None

    async def swap_token_to_weth(self, token_in, amount_in, amount_out_min):
        """
        Swaps a specified token for WETH.

        Args:
            token_in (str): The symbol of the input token.
            amount_in (float): The amount of input tokens to swap.
            amount_out_min (float): The minimum amount of WETH to receive.

        Returns:
            dict: The transaction receipt, or None if the transaction fails.
        """
        logging.info(f"Wallet {self.address} | Starting swap: {amount_in} {token_in} -> WETH")

        token_in_address = TOKENS[token_in]
        weth_address = TOKENS["WETH"]
        path = [token_in_address, weth_address]

        recipient = self.address
        referrer = self.ref_address if self.ref_address else self.address

        try:
            # Approve the token for the router contract
            token_contract = self.web3.eth.contract(address=token_in_address, abi=[
                {
                    "constant": False,
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ])

            nonce = self.web3.eth.get_transaction_count(recipient)
            gas_price = int(self.web3.eth.gas_price * 1.2)

            approve_txn = token_contract.functions.approve(
                HYPERSWAP_CONTRACT_ADDRESS,
                Web3.to_wei(amount_in, "ether")
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_approve_txn = self.web3.eth.account.sign_transaction(approve_txn, private_key=self.private_key)
            approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Approve transaction sent: {approve_tx_hash.hex()}")

            await self.wait_for_transaction_receipt(approve_tx_hash)
            logging.info(f"Wallet {self.address} | Approve transaction confirmed")

            # Perform the swap
            nonce = self.web3.eth.get_transaction_count(recipient)
            deadline = int(self.web3.eth.get_block("latest")["timestamp"] + 600)

            transaction = self.router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                Web3.to_wei(amount_in, "ether"),
                Web3.to_wei(amount_out_min, "ether"),
                path,
                recipient,
                referrer,
                deadline
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Swap transaction sent: {tx_hash.hex()}")

            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Swap transaction confirmed in block {receipt['blockNumber']}")
            return receipt
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during swap: {e}")
            return None

    async def swap_token_to_token(self, token_in, token_out, amount_in, amount_out_min):
        """
        Swaps one token for another.

        Args:
            token_in (str): The symbol of the input token.
            token_out (str): The symbol of the output token.
            amount_in (float): The amount of input tokens to swap.
            amount_out_min (float): The minimum amount of output tokens to receive.

        Returns:
            dict: The transaction receipt, or None if the transaction fails.
        """
        logging.info(f"Wallet {self.address} | Starting swap: {amount_in} {token_in} -> {token_out}")

        if token_in not in TOKENS or token_out not in TOKENS:
            raise ValueError("Invalid token symbol. Please use valid tokens from the TOKENS dictionary.")

        token_in_address = TOKENS[token_in]
        token_out_address = TOKENS[token_out]

        recipient = self.address
        referrer = self.ref_address if self.ref_address else self.address

        try:
            # Approve the token for the router contract
            token_contract = self.web3.eth.contract(address=token_in_address, abi=[
                {
                    "constant": False,
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ])

            nonce = self.web3.eth.get_transaction_count(recipient)
            gas_price = int(self.web3.eth.gas_price * 1.5)

            approve_txn = token_contract.functions.approve(
                HYPERSWAP_CONTRACT_ADDRESS,
                2 ** 256 - 1  # Approve maximum value
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_approve_txn = self.web3.eth.account.sign_transaction(approve_txn, private_key=self.private_key)
            approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Approve transaction sent: {approve_tx_hash.hex()}")

            await self.wait_for_transaction_receipt(approve_tx_hash)
            logging.info(f"Wallet {self.address} | Approve transaction confirmed")

            # Perform the swap
            nonce = self.web3.eth.get_transaction_count(recipient)
            path = [Web3.to_checksum_address(token_in_address), Web3.to_checksum_address(token_out_address)]
            deadline = int(self.web3.eth.get_block("latest")["timestamp"] + 600)

            transaction = self.router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                Web3.to_wei(amount_in, "ether"),
                Web3.to_wei(amount_out_min, "ether"),
                path,
                recipient,
                referrer,
                deadline
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Swap transaction sent: {tx_hash.hex()}")

            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Swap transaction confirmed in block {receipt['blockNumber']}")
            return receipt
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during swap: {e}")
            return None

    async def swap(self, token_in, token_out, amount_in, amount_out_min):
        """
        Executes a swap between two tokens or between a token and WETH.

        Args:
            token_in (str): The symbol of the input token.
            token_out (str): The symbol of the output token.
            amount_in (float): The amount of input tokens to swap.
            amount_out_min (float): The minimum amount of output tokens to receive.
        """
        try:
            if token_in == "WETH":
                balance = await self.get_native_balance()
            else:
                balance = await self.check_balance(TOKENS[token_in])


            if balance <= amount_in:
                amount_in = balance * 0.9
            if SWAP_PERCENTAGE:
                amount_in = amount_in * balance

            if token_in == "WETH":
                await self.swap_weth_to_token(token_out, amount_in, amount_out_min)
            elif token_out == "WETH":
                await self.swap_token_to_weth(token_in, amount_in, amount_out_min)
            else:
                await self.swap_token_to_token(token_in, token_out, amount_in, amount_out_min)
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during swap execution: {e}")

    async def wrap_eth(self, amount_in_eth):
        """
        Asynchronously wraps ETH into WETH by interacting with the WETH contract.

        Args:
            amount_in_eth (float): The amount of ETH to wrap into WETH.

        Returns:
            dict or None: The transaction receipt if successful, otherwise None.
        """
        logging.info(f"Wallet {self.address} | Starting wrap_eth: {amount_in_eth} ETH -> WETH")

        try:
            weth_address = TOKENS["WETH"]
            recipient = self.address
            nonce = self.web3.eth.get_transaction_count(recipient)
            deadline = int(self.web3.eth.get_block("latest")["timestamp"] + 300)

            weth_contract = self.web3.eth.contract(address=weth_address, abi=[
                {
                    "constant": False,
                    "inputs": [],
                    "name": "deposit",
                    "outputs": [],
                    "payable": True,
                    "stateMutability": "payable",
                    "type": "function"
                }
            ])

            gas_price = int(self.web3.eth.gas_price * 1.2)

            transaction = weth_contract.functions.deposit().build_transaction({
                'chainId': self.web3.eth.chain_id,
                'value': Web3.to_wei(amount_in_eth, "ether"),
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Wrap ETH transaction sent: {tx_hash.hex()}")

            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Wrap ETH transaction confirmed in block {receipt['blockNumber']}")
            return receipt
        except TransactionNotFound:
            logging.error(
                f"Wallet {self.address} | Wrap ETH transaction not found. It might have been dropped or replaced.")
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during wrap_eth execution: {e}")
        return None

    async def unwrap_eth(self, amount_in_weth):
        """
        Asynchronously unwraps WETH into ETH by interacting with the WETH contract.

        Args:
            amount_in_weth (float): The amount of WETH to unwrap into ETH.

        Returns:
            dict or None: The transaction receipt if successful, otherwise None.
        """
        logging.info(f"Wallet {self.address} | Starting unwrap_eth: {amount_in_weth} WETH -> ETH")

        try:
            weth_address = TOKENS["WETH"]
            recipient = self.address
            nonce = self.web3.eth.get_transaction_count(recipient)

            weth_contract = self.web3.eth.contract(address=weth_address, abi=[
                {
                    "constant": False,
                    "inputs": [{"name": "wad", "type": "uint256"}],
                    "name": "withdraw",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ])

            gas_price = int(self.web3.eth.gas_price * 1.2)

            transaction = weth_contract.functions.withdraw(
                Web3.to_wei(amount_in_weth, "ether")
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Unwrap WETH transaction sent: {tx_hash.hex()}")

            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Unwrap WETH transaction confirmed in block {receipt['blockNumber']}")
            return receipt
        except TransactionNotFound:
            logging.error(
                f"Wallet {self.address} | Unwrap WETH transaction not found. It might have been dropped or replaced.")
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during unwrap_eth execution: {e}")
        return None

    async def add_liquidity(self, token_a, token_b, amount_a):
        """
        Asynchronous method to add liquidity to a pool.

        Args:
            token_a (str): Name of token A (e.g., "WETH").
            token_b (str): Name of token B (e.g., "HSPX").
            amount_a (float): Amount of token A to add to the pool.
        """
        logging.info(f"Wallet {self.address} | Starting add_liquidity: {amount_a} {token_a} + {token_b}")

        try:
            # Retrieve token addresses from configuration
            token_a_address = TOKENS[token_a]
            token_b_address = TOKENS[token_b]

            # Check if a pool exists for the token pair
            pool_address = await self.check_pool_exists(token_a, token_b)
            if pool_address is None:
                logging.info(f"Wallet {self.address} | Pool for {token_a}/{token_b} does not exist. Creating pool...")
                await self.create_pool(token_a, token_b)
                pool_address = await self.check_pool_exists(token_a, token_b)
                if pool_address is None:
                    logging.error(f"Wallet {self.address} | Failed to create pool.")
                    return None

            # Calculate the optimal amount of token B based on the current exchange rate
            amount_b = await self.calculate_optimal_amount(token_a, token_b, amount_a)

            recipient = self.address
            referrer = self.ref_address if self.ref_address else self.address
            nonce = self.web3.eth.get_transaction_count(recipient)
            deadline = int(self.web3.eth.get_block("latest")["timestamp"] + 600)

            # Approving token A
            logging.info(f"Wallet {self.address} | Approving token A ({token_a})...")
            await self.approve_token(token_a_address, amount_a, nonce)
            nonce += 1

            # Approving token B
            logging.info(f"Wallet {self.address} | Approving token B ({token_b})...")
            await self.approve_token(token_b_address, amount_b, nonce)
            nonce += 1

            # Adding liquidity
            logging.info(f"Wallet {self.address} | Adding liquidity for {token_a}/{token_b}...")
            transaction = self.router_contract.functions.addLiquidity(
                token_a_address,
                token_b_address,
                Web3.to_wei(amount_a, "ether"),
                Web3.to_wei(amount_b, "ether"),
                0,  # Minimum token A amount
                0,  # Minimum token B amount
                recipient,
                deadline
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 300000,
                'gasPrice': int(self.web3.eth.gas_price * 1.2),
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Add liquidity transaction sent: {tx_hash.hex()}")

            # Waiting for transaction confirmation
            receipt = await self.wait_for_transaction_receipt(tx_hash)
            logging.info(
                f"Wallet {self.address} | Add liquidity transaction confirmed in block {receipt['blockNumber']}")

            # Checking LP token balance
            lp_token_balance = await self.check_lp_token_balance(pool_address)
            logging.info(f"Wallet {self.address} | LP token balance after adding liquidity: {lp_token_balance}")

            return receipt
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during add_liquidity: {e}")
            return None

    async def approve_token(self, token_address, amount, nonce):
        """
        Approves the spending of a token by the smart contract.

        Args:
            token_address (str): The contract address of the token to approve.
            amount (float): The amount of tokens to approve.
            nonce (int): The transaction nonce.
        """
        try:
            token_contract = self.web3.eth.contract(address=token_address, abi=[
                {
                    "constant": False,
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ])

            transaction = token_contract.functions.approve(
                HYPERSWAP_CONTRACT_ADDRESS,
                Web3.to_wei(amount, "ether")
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,
                'gasPrice': int(self.web3.eth.gas_price * 1.2),
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Wallet {self.address} | Approve transaction sent: {tx_hash.hex()}")

            await self.wait_for_transaction_receipt(tx_hash)
            logging.info(f"Wallet {self.address} | Approve transaction confirmed")
        except Exception as e:
            logging.error(f"Wallet {self.address} | Error during token approval: {e}")

    async def check_pool_exists(self, token_a, token_b):
        """
        Checks if a liquidity pool exists for the given token pair.

        Args:
            token_a (str): Name of token A (e.g., "WETH").
            token_b (str): Name of token B (e.g., "HSPX").

        Returns:
            str: Pool address if it exists, otherwise None.
        """
        try:
            token_a_address = TOKENS[token_a]
            token_b_address = TOKENS[token_b]

            pool_address = await asyncio.to_thread(
                self.factory_contract.functions.getPair(token_a_address, token_b_address).call
            )

            if pool_address == "0x0000000000000000000000000000000000000000":
                logging.warning(f"Pool for {token_a}/{token_b} does not exist.")
                return None

            logging.info(f"Pool for {token_a}/{token_b} exists at {pool_address}.")
            return pool_address

        except Exception as e:
            logging.error(f"Error checking pool existence for {token_a}/{token_b}: {e}")
            return None

    async def create_pool(self, token_a, token_b):
        """
        Creates a liquidity pool for the given token pair if it does not exist.

        Args:
            token_a (str): Name of token A (e.g., "WETH").
            token_b (str): Name of token B (e.g., "HSPX").
        """
        try:
            token_a_address = TOKENS[token_a]
            token_b_address = TOKENS[token_b]

            nonce = self.web3.eth.get_transaction_count(self.address)
            gas_price = int(self.web3.eth.gas_price * 1.2)

            create_pool_txn = self.factory_contract.functions.createPair(token_a_address,
                                                                         token_b_address).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            signed_txn = self.web3.eth.account.sign_transaction(create_pool_txn, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Create pool transaction sent: {tx_hash.hex()}")

            try:
                receipt = await self.wait_for_transaction_receipt(tx_hash)
                logging.info(f"Pool created in block {receipt['blockNumber']}")
            except TransactionNotFound:
                logging.error("Create pool transaction not found. It might have been dropped or replaced.")
                return None

        except Exception as e:
            logging.error(f"Error creating pool for {token_a}/{token_b}: {e}")
            return None

    async def normalize_amount(self, amount, decimals):
        """
        Converts token amount from smallest units (e.g., Wei) to a normal format.

        Args:
            amount (int): Token amount in smallest units.
            decimals (int): Number of decimal places for the token.

        Returns:
            float: Token amount in normal format.
        """
        try:
            return amount / 10 ** decimals
        except Exception as e:
            logging.error(f"Error normalizing amount: {e}")
            return None

    async def get_token_decimals(self, token_address):
        """
        Retrieves the number of decimal places for a token.

        Args:
            token_address (str): Token contract address.

        Returns:
            int: Number of decimal places.
        """
        try:
            abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]

            token_contract = self.web3.eth.contract(address=token_address, abi=abi)
            decimals = await asyncio.to_thread(token_contract.functions.decimals().call)
            return decimals

        except Exception as e:
            logging.error(f"Error retrieving decimals for token {token_address}: {e}")
            return None

    async def get_all_pairs(self):
        """
        Retrieves all liquidity pairs from the Hyperswap factory.

        Returns:
            list: List of pair addresses.
        """
        try:
            pair_count = await asyncio.to_thread(self.factory_contract.functions.allPairsLength().call)
            logging.info(f"Total pairs: {pair_count}")

            pairs = []
            for i in range(pair_count):
                pair_address = await asyncio.to_thread(self.factory_contract.functions.allPairs(i).call)
                pairs.append(pair_address)
                logging.info(f"Pair {i + 1}: {pair_address}")

            return pairs

        except Exception as e:
            logging.error(f"Error retrieving all pairs: {e}")
            return []

    async def check_lp_token_balance(self, pool_address):
        """
        Retrieves the user's LP token balance and calculates their share in the pool.

        Args:
            pool_address (str): Address of the liquidity pool.

        Returns:
            dict: A dictionary containing the user's share, token0 balance, and token1 balance.
        """
        try:
            lp_token_contract = self.web3.eth.contract(address=pool_address, abi=[
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}],
                 "type": "function"},
                {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf",
                 "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "getReserves",
                 "outputs": [{"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"},
                             {"name": "blockTimestampLast", "type": "uint32"}], "type": "function"}
            ])

            user_lp_balance = await asyncio.to_thread(lp_token_contract.functions.balanceOf(self.address).call)
            total_lp_supply = await asyncio.to_thread(lp_token_contract.functions.totalSupply().call)
            reserves = await asyncio.to_thread(lp_token_contract.functions.getReserves().call)

            if total_lp_supply > 0:
                user_share = user_lp_balance / total_lp_supply
                user_token0 = reserves[0] * user_share
                user_token1 = reserves[1] * user_share
                logging.info(f"User share: {user_share:.2%}")
                logging.info(f"Token 0: {user_token0}, Token 1: {user_token1}")
                return {"share": user_share, "token0": user_token0, "token1": user_token1}
            else:
                logging.warning("No liquidity in the pool.")
                return {"share": 0, "token0": 0, "token1": 0}

        except Exception as e:
            logging.error(f"Error checking LP token balance for pool {pool_address}: {e}")
            return None

    async def execute_route(self, route):
        """
        Executes a route for the wallet.

        Args:
            route (dict): A dictionary containing a "steps" key with a list of steps.

        Raises:
            ValueError: If the route does not contain the "steps" key or an unknown action is encountered.
        """
        try:
            if "steps" not in route:
                logging.error("Route must contain 'steps' key.")
                raise ValueError("Route must contain 'steps' key.")

            for step in route["steps"]:
                action = step.get("action")
                params = step.get("params", {})
                delay = random.uniform(DELAY_STEP[0], DELAY_STEP[1])

                try:
                    if action == "swap":
                        await self.swap(**params)
                    elif action == "wrap":
                        await self.wrap_eth(**params)
                    elif action == "unwrap":
                        await self.unwrap_eth(**params)
                    elif action == "add_liquidity":
                        await self.add_liquidity(**params)
                    else:
                        logging.error(f"Unknown action: {action}")
                        raise ValueError(f"Unknown action: {action}")
                    await self.get_all_balances()
                    await asyncio.sleep(delay)
                except Exception as step_error:
                    logging.error(f"Error executing step {action}: {step_error}")
                    continue  # Skip to the next step instead of failing the entire route

        except Exception as e:
            logging.error(f"Error executing route: {e}")
            raise