# blocks and blockchain
# also includes classes for simplifying blocks into "blockchain nodes"
# these can be turned into actions which allows the graph structure of the blockchain to work efficiently

from utils import *
from transaction import Transaction, Ledger

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
		transactions_hash = hash_base64(" ".join(t.hash for t in self.transactions))
		data_hash = hash_base64(self.prev_block_hash + transactions_hash + self.miner)
		return hash_base64(data_hash + self.nonce)

	def convert_to_str(self):
		res = "\n".join([self.prev_block_hash, self.miner, self.nonce] + [t.convert_to_str() for t in self.transactions])
		return res

	def convert_from_str(s):
		prev_block_hash, miner, nonce, *transactions = s.split("\n")
		transactions = [Transaction.convert_from_str(t) for t in transactions]
		return Block(transactions, miner, prev_block_hash, nonce)
		

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

class AddBlockException(Exception):
	pass

class BlockchainManager:
	def __init__(self):
		self.starting_block = Block0()
		self.past_blocks = set([self.starting_block.hash]) # hashes of past blocks
		self.ledger = LedgerState(self.starting_block)

	def _find_node(self, target_hash, current_path=None, visited=None):
		# assumes the ledger's current node doesn't have any next nodes
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
		# only for use in _find_node
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

	def add_block(self, block):
		# TODO add max block length??

		if not proof_of_work_verify(block.hash):
			raise AddBlockException("Proof of work failed")

		if block.hash in self.past_blocks:
			raise AddBlockException("Block already exists")

		if block.prev_block_hash not in self.past_blocks:
			raise AddBlockException("Previous block does not exist")

		prev_node, actions = self._find_node(block.prev_block_hash)
		self.ledger.update(actions)

		if not self.ledger.is_valid_multiple(block.transactions):
			raise AddBlockException("Invalid or repeat transactions in block")
		
		new_node = BlockchainNode(block, prev_node)
		prev_node.next_nodes.append(new_node)

		self.past_blocks.add(new_node.hash)

		# only reverse if the new block is strictly higher than the old block
		if self.ledger.max_height >= new_node.height:
			self.ledger.update(actions, reverse=True)
		else:
			self.ledger.max_height = new_node.height
			self.ledger.update([LedgerStateAction(new_node, False)])

	def get_prev_block_hash(self):
		return self.ledger.current_node.hash