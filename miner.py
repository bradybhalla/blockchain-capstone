from utils import *
from transaction import Transaction
from blockchain import Block
from node import SavableActiveNode

from threading import Thread, Lock
from time import time
from heapq import heapify, heappop

# not very efficient but works
# need to rethink if you suddenly have thousands of transactions
class TransactionPriorityStructure:

	def __init__(self):
		self.lookup = {}

	def add(self, t):
		if t.hash not in self.lookup:
			self.lookup[t.hash] = (t, time())

	def remove(self, t_hash):
		if t_hash in self.lookup:
			del self.lookup[t_hash]

	def gen_decreasing(self):
		ts = [(-self.lookup[i][0].miner_fee, self.lookup[i][1], i) for i in self.lookup.keys()]
		heapify(ts)

		while len(ts) > 0:
			yield self.lookup[heappop(ts)[2]][0]


# look at multiprocessing

# locking order is alphabetical:
# 		blockchain_lock
#		sources_lock
#		transactions_lock
# (try to not have multiple locks at once though)

class MinerNode(SavableActiveNode):
	def __init__(self, miner_addr, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.miner_addr = miner_addr
		self.known_miners.append(self.web_addr)

		self.available_transactions = TransactionPriorityStructure()
		self.transaction_lock = Lock()

	def add_block(self, block, **kwargs):
		SavableActiveNode.add_block(self, block, **kwargs)

		if self.get_prev_block_hash() == block.hash:
			with self.transaction_lock:
				for t in block.transactions:
					self.available_transactions.remove(t.hash)


	def handle_get(self, path, query, wfile):
		if path == ["ping", "miner"]:
			wfile.write("TRUE".encode())
		else:
			SavableActiveNode.handle_get(self, path, query, wfile)

	def handle_post(self, path, query, wfile):
		if path == ["transaction", "new"]:
			try:
				Thread(target=self.on_new_transaction, args=(query["data"],)).start()
				wfile.write("BLOCK RECIEVED".encode())
			except:
				wfile.write("INVALID REQUEST".encode())
		else:
			SavableActiveNode.handle_post(self, path, query, wfile)

	def _block_data_hash(self, prev_block_hash, transactions, miner):
		transactions_hash = hash_base64(" ".join(t.hash for t in transactions))
		return hash_base64(prev_block_hash + transactions_hash + self.miner_addr)

	def on_new_transaction(self, transaction_str):
		try:
			transaction = Transaction.convert_from_str(transaction_str)

			with self.blockchain_lock:
				valid = self.ledger.is_valid(transaction)

			if valid:
				with self.transaction_lock:
					self.available_transactions.add(transaction)

		except:
			return

	def get_verified_transactions(self, num = 20):
		res = []

		with self.blockchain_lock:
			with self.transaction_lock:
				# close to the is_valid_multiple method of transaction.Ledger
				spending = {}
				transaction_hashes = set()

				for t in self.available_transactions.gen_decreasing():

					if not self.ledger.is_valid(t):
						self.available_transactions.remove(t.hash)
						continue

					if t.from_addr not in spending:
						spending[t.from_addr] = 0

					if spending[t.from_addr] + t.amount + t.miner_fee > self.ledger.money[t.from_addr]:
						self.available_transactions.remove(t.hash)
						continue

					if t.hash in transaction_hashes:
						self.available_transactions.remove(t.hash)
						continue

					spending[t.from_addr] += t.amount + t.miner_fee
					transaction_hashes.add(t.hash)

					res.append(t)
					if len(res) >= num:
						break

		return res

	def mine_attempt(self, hashes=10**7, transactions=None, prev_hash=None, data_hash=None):
		if transactions is None:
			transactions = self.get_verified_transactions()

		if prev_hash is None:
			prev_hash = self.get_prev_block_hash()

		if data_hash is None:
			data_hash = self._block_data_hash(prev_hash, transactions, self.miner_addr)
			
		found = False
		for _ in range(hashes):
			nonce = str(randint(1,2**256))

			if proof_of_work_verify(hash_base64(data_hash + nonce)):
				found = True
				break

		if found:
			res = Block(transactions, self.miner_addr, prev_hash, nonce)
			return res
		else:
			return None

	def mine_iteration(self):
		b = self.mine_attempt()
		if b is not None:
			self.on_new_block(b.convert_to_str())

	def get_save_info(self):
		return [self.past_blocks, self.ledger, self.blocks, self.sources, self.known_miners, self.port, self.web_addr, self.miner_addr, self.available_transactions]

	def create_node(info):
		past_blocks, ledger, blocks, sources, known_miners, port, web_addr, miner_addr, available_transactions = info
		node = MinerNode(miner_addr, web_addr, port=port)

		(node.past_blocks, node.ledger, node.blocks, node.sources, node.known_miners, node.available_transactions) = (past_blocks, ledger, blocks, sources, known_miners, available_transactions)

		return node