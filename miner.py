from utils import *
from transaction import Transaction
from blockchain import Block
from node import SavableActiveNode

from threading import Thread, Lock
from time import time
from heapq import heapify, heappop

from multiprocessing import Process, Value, Array, Queue
from ctypes import c_wchar_p

MAX_TRANSACTIONS_IN_BLOCK = 20

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


# locking order is alphabetical:
# 		blockchain_lock
#		sources_lock
#		transactions_lock
# (try to not have multiple locks at once though)

# a node that also mines new blocks and recieves transactions
# to mine into the blockchain
class MinerNode(SavableActiveNode):
	def __init__(self, miner_addr, num_processes, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.miner_addr = miner_addr
		self.known_miners.append(self.web_addr)

		self.available_transactions = TransactionPriorityStructure()
		self.transaction_lock = Lock()

		self.background_threads.append(Thread(target=self.mining_update_background))
		self.background_threads.append(Thread(target=self.new_block_handler_background))

		self.data_hash = Array("c", 44)
		self.block_data = ([], "", "")

		self.new_block_queue = Queue()
		self.mining = Value("b", False)

		self.mining_processes = [
			Process(
				target=MinerNode.mining_process,
				args=(self.data_hash, self.mining, self.new_block_queue, self.miner_addr)
			) for i in range(num_processes)
		]

	def start(self):
		SavableActiveNode.start(self)

		with self.mining.get_lock():
			self.mining.value = True

		for i in self.mining_processes:
			i.start()

	def stop(self):
		with self.mining.get_lock():
			self.mining.value = False

		SavableActiveNode.stop(self)

		for i in self.mining_processes:
			i.join()

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

	def get_verified_transactions(self, num):
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

	def _calculate_mining_data(self, num_transactions=MAX_TRANSACTIONS_IN_BLOCK):
		transactions = self.get_verified_transactions(num_transactions)
		prev_hash = self.get_prev_block_hash()

		with self.data_hash.get_lock():
			self.data_hash.value = self._block_data_hash(prev_hash, transactions, self.miner_addr).encode()

		self.block_data = (transactions, self.miner_addr, prev_hash)

	def mining_update_background(self, interval=60, num_transactions=MAX_TRANSACTIONS_IN_BLOCK):
		while True:

			self._calculate_mining_data(num_transactions)

			if not self._wait_running(interval):
				break

	def _on_passed_block(self, block_str):
		print("new block passed", block_str)
		print("current previous block", self.get_prev_block_hash())
		self.on_new_block(block_str)
		print("new_prev block", self.get_prev_block_hash())
		print()
		print()
		print()
		self._calculate_mining_data()

	def new_block_handler_background(self, interval=1):
		while True:
			try:
				data_hash, nonce = self.new_block_queue.get_nowait()

				transactions, miner, prev_block_hash = self.block_data

				if self._block_data_hash(prev_block_hash, transactions, miner) != data_hash:
					continue

				block = Block(transactions, miner, prev_block_hash, nonce).convert_to_str()

				Thread(target=self._on_passed_block, args=(block,)).start()
			except:
				pass

			if not self._wait_running(interval):
				break

	def mining_process(self_data_hash, self_mining, self_new_block_queue, self_miner_addr, hashes_at_a_time=10**5, hashes_before_exit_check=10**5):

		n = 0
		data_hash = ""

		while True:
			if n%hashes_at_a_time == 0:
				data_hash = self_data_hash.value.decode()
			if n%hashes_before_exit_check == 0:
				if not self_mining.value:
					break

			nonce = str(randint(1,2**256))
			if proof_of_work_verify(hash_base64(data_hash + nonce)):
				self_new_block_queue.put((data_hash, nonce))

			n += 1

	def get_save_info(self):
		return [self.past_blocks, self.ledger, self.blocks, self.sources, self.known_miners, self.port, self.web_addr, self.miner_addr, self.available_transactions]

	def create_node(info):
		past_blocks, ledger, blocks, sources, known_miners, port, web_addr, miner_addr, available_transactions = info
		node = MinerNode(miner_addr, web_addr, port=port)

		(node.past_blocks, node.ledger, node.blocks, node.sources, node.known_miners, node.available_transactions) = (past_blocks, ledger, blocks, sources, known_miners, available_transactions)

		return node