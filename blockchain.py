from utils import *
from ledger import Transaction, Ledger

# block of transactions
class Block:
	def __init__(self, transactions, miner, prev_block_hash, nonce):
		self.transactions = transactions
		self.miner = miner
		self.prev_block_hash = prev_block_hash
		self.nonce = nonce

		self.hash = self.calc_hash()

	def calc_hash(self):
		# TODO: maybe implement merkle root later
		transactions_hash = hash_base64(" ".join(t.hash for i in self.transactions))
		data_hash = hash_base64(self.prev_block_hash + transactions_hash + self.miner)
		return hash_base64(data_hash + str(self.nonce))

# block parsed for use in the blockchain graph
# stores only necessary information instead of full data of each transaction
# also tracks previous and next nodes
class BlockchainNode:
	# verify block before creating BlockchainNode
	def __init__(self, block, prev_node):
		self.hash = block.hash
		self.prev_node = prev_node
		self.next_nodes = []
		self.height = self.prev_node.height + 1

		self.net_ledger = {}
		self.transaction_hashes = set()

		self.net_ledger[block.miner] = calc_miner_reward(self.height)
		for t in block.transactions:
			if t.from_addr not in self.net_ledger:
				self.net_ledger[t.from_addr] = 0
			if t.to_addr not in self.net_ledger:
				self.net_ledger[t.to_addr] = 0

			self.net_ledger[t.from_addr] -= t.amount + t.miner_fee
			self.net_ledger[t.to_addr] += t.amount
			self.net_ledger[block.miner] += t.miner_fee

			self.transaction_hashes.add(t.hash)


	def create_action(self, undo=True):
		return LedgerStateAction(self, undo)

# starting node for the blockchain
class Block0(BlockchainNode):
	def __init__(self):
		self.height = 0
		self.hash = "0"

	def create_action(self, undo=True):
		raise NotImplementedError("Can't create action for the first node")

# actions that act on LedgerState
# undo or redo blocks when navigating the blockchain
class LedgerStateAction:
	def __init__(self, node, undo):
		self.node = node
		self.undo = False
	def execute(self, ledger, reverse=False):
		undo = self.undo if not reverse else not self.undo
		if not undo:
			ledger.past_transactions.update(self.node.transaction_hashes)
			for addr in self.node.net_ledger:
				if addr not in ledger.money:
					ledger.money[addr] = 0
				ledger.money[addr] += self.node.net_ledger[addr]
			ledger.current_node = self.node
		else:
			ledger.past_transactions.difference_update(self.node.transaction_hashes)
			for addr in self.node.net_ledger:
				ledger.money[addr] -= self.node.net_ledger[addr]
			ledger.current_node = self.node.prev_node

class LedgerState(Ledger):
	def __init__(self, current_node):
		super().__init__()
		self.current_node = current_node

	def update(self, actions, reverse=False):
		if reverse:
			actions = reversed(actions)

		for a in actions:
			a.execute(self, reverse)

class BlockchainManager:
	def __init__(self):
		self.past_blocks = set()
		self.ledger = LedgerState(Block0())

	def add_block(self, block):
		if not proof_of_work_verify(block.hash):
			raise Exception("Proof of work failed")

		if block.hash in self.past_blocks:
			raise Exception("Block already exists")

		# find prev_block, update LedgerState
		to_check = []
		paths = {}
		# breadth first search OR search max height first, use a queue


		# verify transactions
		# add new block
		# add block hash to past blocks
		# un-update LedgerState if max_height >= new blocks height
	def create_block(info):
		pass

if __name__ == "__main__":
	L = LedgerState(Block0())

	t = Transaction("brady", "billy", 10, 10, 1)
	t2 = Transaction("billy", "brady", 10, 2, 1)
	B = Block([t, t2], "jeff", L.current_node.hash, "50")
	node = BlockchainNode(B, L.current_node)

	t3 = Transaction("brady", "billy", 10, 10, 1)
	t4 = Transaction("billy", "brady", 10, 2, 1)
	B2 = Block([t3, t4], "jeff", node.hash, "50")
	node2 = BlockchainNode(B2, node)
