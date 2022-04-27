# run tests on the project

from client import Wallet, SimpleMiner
from node import ActiveNode

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from threading import Thread
from time import sleep

def print_chain(node):
	current_blockchain_node = node.ledger.current_node
	while True:
		print(current_blockchain_node.hash)
		if current_blockchain_node.hash == "0": break
		current_blockchain_node = current_blockchain_node.prev_node

class Running:
	def __init__(self):
		self.running = True

def Exit():
	running.running = False
	ts = [Thread(target=i.stop) for i in [n1,n2,n3]]
	for i in ts:
		i.start()
	for i in ts:
		i.join()
	exit()

running = Running()

def mine(node, miner_addr, running):
	try:
		m = SimpleMiner(miner_addr)
		while running.running:
			with node.blockchain_lock:
				prev_hash = node.get_prev_block_hash()
			
			block = m.mine_block(prev_hash)
			print(miner_addr, "just mined a block")
			node.add_block(block)
			node.widely_broadcast_block(block.convert_to_str())
	except Exception as e:
		print("THREAD ERROR:", str(e))

w = Wallet()
w.create_account("brady")
w.create_account("finn")
w.create_account("ryan")

m1 = SimpleMiner(w.get_addr("brady"))
m2 = SimpleMiner(w.get_addr("finn"))
m3 = SimpleMiner(w.get_addr("ryan"))

for i,j in w.accounts.items():
	print(i, j[0])


n1 = ActiveNode("http://localhost:8000", port=8000)
n2 = ActiveNode("http://localhost:8001", port=8001)
n3 = ActiveNode("http://localhost:8002", port=8002)


n1.start()
n2.start()
n3.start()

n1.broadcast_self_addr(n2.web_addr)
#n1.broadcast_self_addr(n3.web_addr)

n2.broadcast_self_addr(n1.web_addr)
n2.broadcast_self_addr(n3.web_addr)

n3.broadcast_self_addr(n1.web_addr)
n3.broadcast_self_addr(n2.web_addr)

Thread(target=mine, args=(n1, w.get_addr("brady"), running)).start()
Thread(target=mine, args=(n2, w.get_addr("finn"), running)).start()
Thread(target=mine, args=(n3, w.get_addr("ryan"), running)).start()

"""
block = m1.mine_block("0")
n1.add_block(block)
n1.widely_broadcast_block(block.convert_to_str())

block = m3.mine_block(block.hash)
#n3.add_block(block)
#n3.widely_broadcast_block(block.convert_to_str())
"""


while True:
	sleep(5)
	print("\n"*10)
	print("n1", n1.ledger.money)
	print("n2", n2.ledger.money)
	print("n3", n3.ledger.money)


#n.stop()

#m.queue_transaction(w.create_transaction("brady", "<h1>BRAD MOMENT</h1>", 10, 0))
#block2 = m.mine_block(block.hash)
#n.widely_broadcast_block(block2.convert_to_str())

#print("go to http://localhost:8000/block/latest")





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