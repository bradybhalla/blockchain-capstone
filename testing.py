# run tests on the project

from client import Wallet, SimpleMiner, Node

from urllib.parse import urlencode
from urllib.request import Request, urlopen

def send_block(b):
	data = urlencode({"data": b.convert_to_str()}).encode()
	with urlopen(Request("http://localhost:8000/block/new", data=data)) as res:
		print(res.read().decode())

w = Wallet()
w.create_account("brady")

m = SimpleMiner(w.get_addr("brady"))

n = Node()
n.start_server()

block = m.mine_block("0")
send_block(block)

m.queue_transaction(w.create_transaction("brady", "bradbahal", 10, 0))
block2 = m.mine_block(block.hash)
send_block(block2)

print("ready, go to http://localhost:8000/block/latest to see block2")

try:
	while True:
		pass
except:
	n.stop_server()



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