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
		self.next_nodes = []

	def create_action(self, undo=True):
		raise NotImplementedError("Can't create action for the first node")

# actions that act on LedgerState
# undo or redo blocks when navigating the blockchain
class LedgerStateAction:
	def __init__(self, node, undo):
		self.node = node
		self.undo = undo
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
		self.max_height = current_node.height

	def update(self, actions, reverse=False):
		if reverse:
			actions = reversed(actions)

		for a in actions:
			a.execute(self, reverse)

class BlockchainManager:
	def __init__(self):
		self.starting_block = Block0()
		self.past_blocks = set(self.starting_block.hash) # hashes of past blocks
		self.ledger = LedgerState(self.starting_block)

	def _find_node(self, target_hash, current_path=None, visited=None):
		current_node = self.ledger.current_node

		current_path = []
		visited = set([self.ledger.current_node.hash])

		if current_node.hash == target_hash:
			return current_node, current_path

		while current_node.hash != self.starting_block.hash:
			visited.add(current_node.prev_node.hash)
			current_path.append(LedgerStateAction(current_node, True))
			current_node = current_node.prev_node

			if len(set([n.hash for n in current_node.next_nodes]) - visited) > 0:
				res = self._search_forward(current_node, target_hash, current_path[:], visited)
				if res is not None:
					return res

			if current_node.hash == target_hash:
				return current_node, current_path

		raise Exception("Could not find node")

	def _search_forward(self, current_node, target_hash, current_path, visited):
		while True:
			if current_node.hash == target_hash:
				return current_node, current_path

			if len(set([n.hash for n in current_node.next_nodes]) - visited) == 0:
				return None

			next_node = None
			for n in current_node.next_nodes:
				if n.hash not in visited:
					visited.add(n.hash)
					if next_node is None:
						next_node = n
					else:
						res = self._search_forward(n, target_hash, current_path + [LedgerStateAction(n, False)], visited)
						if res is not None:
							return res

			current_path.append(LedgerStateAction(next_node, False))
			current_node = next_node


	def _verify_block(self, block):
		# assumes ledger state is set up correctly
		pass

	def add_block(self, block):
		#if not proof_of_work_verify(block.hash):
		#	raise Exception("Proof of work failed")

		if block.hash in self.past_blocks:
			raise Exception("Block already exists")

		if block.prev_block_hash not in self.past_blocks:
			raise Exception("Previous block does not exist")

		prev_node, actions = self._find_node(block.prev_block_hash)

		self.ledger.update(actions)

		# TODO verify transactions
		
		new_node = BlockchainNode(block, prev_node)

		prev_node.next_nodes.append(new_node)

		self.past_blocks.add(new_node.hash)

		if self.ledger.max_height > new_node.height:
			self.ledger.update(actions, reverse=True)
		else:
			self.ledger.max_height = new_node.height
			self.ledger.update([LedgerStateAction(new_node, False)])

	def create_block(info):
		pass

class Blocks:
	def __init__(self, H, P):
		self.transactions = [Transaction(1, randint(1,5), randint(5,10), randint(1,3), randint(1,1000)) for i in range(5)]
		self.miner = randint(1,5)
		self.prev_block_hash = P
		self.nonce = 0

		self.hash = H

if __name__ == "__main__":
	blockchain = BlockchainManager()
	blockchain.ledger.money[1] = 1000

	blockchain.add_block(Blocks(1,"0"))
	blockchain.add_block(Blocks(2,"0"))
	blockchain.add_block(Blocks(3,2))
	blockchain.add_block(Blocks(4,3))
	blockchain.add_block(Blocks(5,4))
	blockchain.add_block(Blocks(6,"0"))
	blockchain.add_block(Blocks(7,1))
	blockchain.add_block(Blocks(8,4))
	blockchain.add_block(Blocks(9,3))
	blockchain.add_block(Blocks(10,9))
	blockchain.add_block(Blocks(11,10))
	blockchain.add_block(Blocks(12,9))
	blockchain.add_block(Blocks(13,4))

