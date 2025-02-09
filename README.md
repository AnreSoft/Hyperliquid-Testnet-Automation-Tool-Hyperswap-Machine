![image](https://github.com/user-attachments/assets/2a27dc1c-4b9c-4cab-a861-15f32c645cb3)
# Hyperliquid Testnet Automation Tool (Hyperswap Machine)

This repository contains software for automating transactions in the **Hyperliquid** testnet. The tool allows you to perform all activities in **Hyperswap**, offering flexible settings and detailed documentation, making it a convenient tool for implementing your ideas.

## About the Hyperliquid Testnet

Currently, the Hyperliquid testnet is in a **"closed testing phase"**. This means that information about it is hardly being announced, and even Hyperliquid itself is not actively promoting it. However, this is a great opportunity for the most dedicated users to start testing earlier than others. The sooner you start making transactions on the Hyperliquid network, the better!

### 100% Rewards in the Testnet
By participating in the testnet, you can earn **100% rewards** for your activities. It’s worth noting that in November 2024, Hyperliquid distributed the largest airdrop in history. This is an excellent chance to test the network's functionality earlier than others and receive guaranteed rewards for it.

## Features of the Software

The software is designed to automate transactions in the Hyperliquid testnet and supports the following functions:

- **Swap HYPE to any supported token**
- **Swap token to token**
- **Swap token to HYPE**
- **Swap HYPE to stHYPE (staking)**
- **WRAP/UNWRAP HYPE**
- **Add liquidity to a pool**
- **Logging of all processes**

### Key Features
1. Asynchronous operation
2. Support for multiple wallets
3. Ability to use proxies
4. Flexible configuration settings
5. Comprehensive logging
   ![image](https://github.com/user-attachments/assets/a6390b48-0b2a-4faf-8acc-bc4601fe413e)
6. Save balances of all tokens for all wallets after completing all steps
   ![image](https://github.com/user-attachments/assets/7fc25b23-a56e-4626-9d47-bd0ea0844ec3)


---

## Getting Started

### If You Don’t Have a Hyperliquid Account

If you want to participate in the Hyperliquid testnet but don’t have an active account yet, follow these steps:

1. **Go to the Hyperliquid DEX**:
   - Open the [Hyperliquid DEX](https://app.hyperliquid.xyz/).
   - Connect your wallet (e.g., MetaMask).

2. **Make a Deposit**:
   - Deposit **20 USDC** on the **Arbitrum One** network.

3. **Buy Coins**:
   - We recommend buying the **HYPE** coin.
   - Stake the purchased HYPE.

Now you’re ready to participate in the Hyperliquid testnet!

---

### If You Already Have a Hyperliquid Account

If you already have a Hyperliquid account, follow these steps to start testing **HyperEVM**:

1. **Go to the Testnet DEX**:
   - Open the [Hyperliquid Testnet DEX](https://app.hyperliquid-testnet.xyz/).
   - Connect your wallet.

2. **Get Test Tokens**:
   - Go to the **Faucet** tab.
   - Claim **1000 test USDC**.
     
  ![Capture1](https://github.com/user-attachments/assets/ff7061d1-04ae-412d-b4ab-3992fc2d02a1)

3. **Buy HYPE**:
   - On the **Trade** tab, select the **HYPE/USD** pair.
   - Buy HYPE at the market price (use all your USDC).

4. **Send HYPE to the Test Address**:
   - Click **Send** next to your HYPE balance.
     ![Capture2](https://github.com/user-attachments/assets/b327ab5c-56a7-4f15-910a-afffd9d49099)
   - Send all your HYPE to the address:  
     `0x2222222222222222222222222222222222222222`.  
     This is necessary for the tokens to appear in your testnet balance.

5. **Review the Documentation**:
   - For a deeper understanding of how HyperEVM works, check out the [official documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/evm).

6. **Go to Hyperswap**:
   - Open the [Hyperswap Testnet](https://testnet.hyperswap.exchange/).
   - Connect your wallet.
   - Ensure your HYPE balance is displayed.

7. **Prepare to Run the Software**:
   - You can manually interact with the platform to familiarize yourself with its features.
   - After that, you’re ready to run the software for transaction automation.

---

## Configuration

Customize the software to your needs using the following parameters:

- **WALLETS_PATH = "data/wallets.txt"** – a file containing wallets in the format: `address;private_key;ref_address`.
- **PROXY_PATH = "data/proxy.txt"** – a file containing proxies in the format: `http://login:pass@ip:port`.
- **ROUTES_PATH = "data/routes.json"** – a file with custom routes. See `data/routes_example.json` for a detailed description.
- **DELAY_STEP = (20, 200)** – the minimum and maximum delay between route steps.
- **STEP_COUNT = 3** – the number of routes to execute. If set to `None`, the software runs indefinitely.
- **SWAP_PERCENTAGE = True** – if `True`, the balance in `routes` is specified as a percentage (0 to 1). If `False`, the value is specified in absolute terms. If the wallet balance doesn’t match the specified value, the software uses 90% of the available balance for the swap.

---

## How to Run

1. Create a new project.
2. Install dependencies using:
```bash
   pip install -r requirements.txt
   ```
3. Configure the settings and routes.
4. Run the software:
```bash 
   python main.py
```
---

## Additional Resources

- **Hyperliquid DEX**: [https://app.hyperliquid.xyz/](https://app.hyperliquid.xyz/)
- **Hyperliquid Testnet DEX**: [https://app.hyperliquid-testnet.xyz/](https://app.hyperliquid-testnet.xyz/)
- **Hyperliquid Documentation**: [https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/evm](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/evm)
- **Hyperswap Testnet**: [https://testnet.hyperswap.exchange/](https://testnet.hyperswap.exchange/)
- **HyperEVM Block Explorer**: [https://testnet.purrsec.com/](https://testnet.purrsec.com/)
- **Faucet 1**: [https://app.hypurr.fi/](https://app.hypurr.fi/)
- **Faucet 2**: [https://testnet.hyperlend.finance/](https://testnet.hyperlend.finance/)

---

## Conclusion

Use this software to automate transactions in the Hyperliquid testnet. The earlier you start, the higher your chances of earning rewards! Stay tuned for updates, as we’re already working on automating other projects on HyperEVM.

If you have any questions or suggestions, feel free to create an [issue](https://github.com/AnreSoft/Hyperliquid-Testnet-Automation-Tool-Hyperswap-Machine/issues) in this repository.
