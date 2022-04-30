from utils import *
from node import SavableActiveNode

# look at multiprocessing

def Miner(SavableActiveNode):
	def __init__(self, miner_addr, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.miner_addr = miner_addr

	def _block_data_hash(self, transactions, miner, prev_block_hash):
		transactions_hash = hash_base64(" ".join(t.hash for t in transactions))
		return hash_base64(prev_block_hash + transactions_hash + miner)

	def get_transactions(self):
		pass

	def mine(self, hashes=10000):
		with self.blockchain_lock:
			data_hash = self._block_data_hash(self.get_transactions(), self.miner_addr, self.get_prev_block_hash())
			
		nonce = str(randint(1,2**256))
		while not proof_of_work_verify(hash_base64(data_hash + nonce)):
			nonce = str(randint(1,2**256))

		res = Block(self._queued_transactions, self.addr, prev_hash, nonce)

		self._queued_transactions = []

		return res

	def mine_success(self, block):
		pass