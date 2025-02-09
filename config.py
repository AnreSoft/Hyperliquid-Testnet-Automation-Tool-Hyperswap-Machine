'''=============================================
===============MAIN CONFIGURATION===============
============================================='''


'''============USER CONFIGURATION============'''

WALLETS_PATH = "data/wallets.txt" # Path to the file containing wallet data (address;private_key;ref_address)
PROXY_PATH = "data/proxy.txt" # Path to the file containing proxy data (one proxy per line)
ROUTES_PATH = "data/routes.json" # Path to the JSON file containing routes (list of actions to execute)

DELAY_STEP = (100, 200) # Minimum and maximum delay (in seconds) between steps, chosen randomly using `random.uniform`
ROUTES_COUNT = 1 # Number of routes each wallet will execute. If set to `None`, the software will run indefinitely.

# If `True`, swap amounts in routes should be specified as percentages (0 to 1) of the current token balance.
# If `False`, swap amounts are treated as absolute values. If the balance is insufficient, the swap will use 90% of the available token balance.
SWAP_PERCENTAGE = True



'''============APP CONFIGURATION============'''
#Docs: https://docs.hyperswap.exchange/hyperswap

# RPC URL for connecting to the Hyperliquid testnet EVM
RPC_URL = "https://api.hyperliquid-testnet.xyz/evm"

# Address of the Hyperswap contract
HYPERSWAP_CONTRACT_ADDRESS = "0x85aA63EB2ab9BaAA74eAd7e7f82A571d74901853"

# Address of the Hyperswap factory contract
HYPERSWAP_FACTORY_ADDRESS = "0xA028411927E2015A363014881a4404C636218fb1"

# Dictionary of token addresses on the Hyperliquid testnet
TOKENS = {
    "WETH": "0xADcb2f358Eae6492F61A5F87eb8893d09391d160",
    "HSPX": "0xD8c23394e2d55AA6dB9E5bb1305df54A1F83D122",
    "xHSPX": "0x91483330b5953895757b65683d1272d86d6430B3",
    "PURR": "0xC003D79B8a489703b1753711E3ae9fFDFC8d1a82",
    "JEFF": "0xbF7C8201519EC22512EB1405Db19C427DF64fC91",
    "CATBAL": "0x26272928f2395452090143Cf347aa85f78cDa3E8",
    "HFUN": "0x37adB2550b965851593832a6444763eeB3e1d1Ec",
    "POINTS": "0xFe1E6dAC7601724768C5d84Eb8E1b2f6F1314BDe",
    "stHYPE": "0xe2FbC9cB335A65201FcDE55323aE0F4E8A96A616",
    "USDC": "0x24ac48bf01fd6CB1C3836D08b3EdC70a9C4380cA",
    "KEY": "0x8D7527f1ECc271486E319908E62DADd033288f31"
}