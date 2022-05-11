# run tests on the project

"""
REQUESTING - GET

/money

/block/latest
/block?H=<hash>

/source/list
/source/miner/list

/ping
/ping/miner


SENDING - POST

/block/new    data=<block> [source=<source>]
/source/new

# for miners
/transaction/new    data=<transaction>

"""


from client import Wallet
from miner import MinerNode

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from threading import Thread
from time import sleep
from random import choice, randint

def print_chain(node):
	current_blockchain_node = node.ledger.current_node
	while True:
		print(current_blockchain_node.hash)
		if current_blockchain_node.hash == "0": break
		current_blockchain_node = current_blockchain_node.prev_node

def Exit():
	m1.stop()
	exit()


w = Wallet()
w.create_account("brady")

m1 = MinerNode(w.get_addr("brady"), "http://164.104.90.180:8000", port=8000)
m1.start()



"""
sleep(3)

print(m1.available_transactions.lookup)

m2.mine_iteration()
sleep(1)

print("ready")

print(m1.ledger.money)
print(m2.ledger.money)

print(m1.available_transactions.lookup)
"""


"""
bm = BlockchainManager()

w = Wallet()
w.create_account("brady")
w.create_account("finn")

m = SimpleMiner(w.get_addr("brady"))

bm.add_block(m.mine_block(bm.get_prev_block_hash()))
bm.add_block(m.mine_block(bm.get_prev_block_hash()))
bm.add_block(m.mine_block(bm.get_prev_block_hash()))

t = w.create_transaction("brady", w.get_addr("finn"), 50, 3)
t2 = w.create_transaction("brady", w.get_addr("finn"), 50, 3)
m.queue_transaction(t)
m.queue_transaction(t2)
bm.add_block(m.mine_block(bm.get_prev_block_hash()))

#m.queue_transaction(t2)
bm.add_block(m.mine_block(bm.get_prev_block_hash()))

print(bm.ledger.money)


"""
"""
w = Wallet()
w.create_account("brady")
w.create_account("finn")
w.create_account("ryan")

m1 = SimpleMiner(w.get_addr("brady"))

for i,j in w.accounts.items():
	print(i, j[0])

nodes = [SavableActiveNode("http://localhost:{}".format(i), port=i) for i in range(8000,8005)]

for i in nodes:
	i.start()

for i in nodes:
	for j in nodes:
		if i != j:
			i.broadcast_self_addr(j.web_addr)

sleep(3)

print("starting mine")
for i in range(500):
	block = m1.mine_block(nodes[0].get_prev_block_hash())
	block_str = block.convert_to_str()
	nodes[0].add_block(block)
	if i%10 == 0:
		nodes[0].widely_broadcast_block(block_str)

print("ending mine")

sleep(3)

for i in nodes:
	print(len(i.sources), i.ledger.money)
"""

#Exit()

#block = m3.mine_block(block.hash)
#n3.add_block(block)
#n3.widely_broadcast_block(block.convert_to_str())


"""
while True:
	sleep(5)
	print("\n"*10)
	print("n1", n1.ledger.money)
	print("n2", n2.ledger.money)
	print("n3", n3.ledger.money)
"""

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