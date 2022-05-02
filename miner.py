from utils import *
from node import SavableActiveNode

from threading import Lock

# look at multiprocessing

# locking order is alphabetical:
# 		blockchain_lock
#		sources_lock
#		transactions_lock
# (try to not have multiple locks at once though)

def Miner(SavableActiveNode):
	def __init__(self, miner_addr, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.miner_addr = miner_addr


		self.transactions = [] # binary search to insert
		self.transaction_lock = Lock()

	def _block_data_hash(self, prev_block_hash, transactions, miner):
		transactions_hash = hash_base64(" ".join(t.hash for t in transactions))
		return hash_base64(prev_block_hash + transactions_hash + self.miner_addr)

	def get_transactions(self, has_lock = False):
		if not has_lock:
			self.transaction_lock.acquire()

		res = [] # TODO: get transactions

		if not has_lock:
			self.transaction_lock.release()

		return res

	def verify_transactions(self, transactions):
		pass # TODO

	def mine(self, hashes=10000, transactions=None, prev_hash=None, data_hash=None):
		if transactions is None:
			transactions = self.get_transactions()

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

	def on_mine_success(self, block):
		pass