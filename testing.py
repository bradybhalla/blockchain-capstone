# run tests on the project

from client import Wallet, SimpleMiner
from node import ActiveNode

from urllib.parse import urlencode
from urllib.request import Request, urlopen

w = Wallet()
w.create_account("brady")

m = SimpleMiner(w.get_addr("brady"))

n = ActiveNode("http://localhost:8000")
n.sources.append("http://localhost:8000")
n.sources.append("http://unbased.source")
n.sources.append("asdfasdf")
n.start()

block = m.mine_block("0")
n.widely_broadcast_block(block.convert_to_str())

m.queue_transaction(w.create_transaction("brady", "<h1>BRAD MOMENT</h1>", 10, 0))
block2 = m.mine_block(block.hash)
n.widely_broadcast_block(block2.convert_to_str())

print("go to http://localhost:8000/block/latest")





# send source example
"""
for d in ["http://localhost:8000", "http://google.com", "http://localhost:8000", "http://localhost:8000"]:
	data = urlencode({"data": d}).encode()
	with urlopen(Request("http://localhost:8000/source/new", data=data)) as res:
		pass
"""

#n.stop_server()

"""
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

# mine t into the blockchain
blockchain.add_block(miner.mine_block(blockchain.get_prev_block_hash()))

# send some money back
t2 = wallet.create_transaction("finn", wallet.get_addr("brady"), 5, 1)
miner.queue_transaction(t2)

# mine t2 into the blockchain
blockchain.add_block(miner.mine_block(blockchain.get_prev_block_hash()))

print(blockchain.ledger.money)
"""