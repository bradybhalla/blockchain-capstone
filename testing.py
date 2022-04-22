from client import Wallet, SimpleMiner
from blockchain import BlockchainManager

# initialize blockchain
blockchain = BlockchainManager()

# create accounts for brady and finn
wallet = Wallet()
wallet.create_account("brady")
wallet.create_account("finn")

# make a miner for brady
miner = SimpleMiner(wallet.get_addr("brady"))

# mine a block to get money
blockchain.add_block(miner.mine_block(blockchain.get_prev_block_hash()))

# send money from brady to finn
t = wallet.create_transaction("brady", wallet.get_addr("finn"), 10, 1)
miner.queue_transaction(t)

""" doesn't work because finn has to be confirmed as having the money first (in separate block)
# send some money back
t2 = wallet.create_transaction("finn", wallet.get_addr("brady"), 5, 1)
miner.queue_transaction(t2)
"""

# mine t into the blockchain
blockchain.add_block(miner.mine_block(blockchain.get_prev_block_hash()))

# send some money back
t2 = wallet.create_transaction("finn", wallet.get_addr("brady"), 5, 1)
miner.queue_transaction(t2)

# mine t2 into the blockchain
blockchain.add_block(miner.mine_block(blockchain.get_prev_block_hash()))

print(blockchain.ledger.money)