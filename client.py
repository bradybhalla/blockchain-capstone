# classes for client use: creating accounts, mining blocks, running nodes
# TODO this will be broken into other files later

from utils import *
from signature import CompressedECDSA
from transaction import Transaction
from blockchain import Block, BlockchainManager

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

class Wallet:
	def __init__(self):
		self.sig_algorithm = CompressedECDSA()
		self.accounts = {}

	def create_account(self, name):
		pub, priv = self.sig_algorithm.keygen()
		addr = pub_to_addr(pub)
		self.accounts[name] = (addr, pub, priv)

	def create_transaction(self, account_name, to_addr, amount, miner_fee):
		addr, pub, priv = self.accounts[account_name]
		t = Transaction(addr, to_addr, amount, miner_fee, hash_base64(randint(1,2**20)))
		H = hash_int(t)
		t.approve(self.sig_algorithm.sign(H, priv), pub)
		return t

	def get_addr(self, name):
		return self.accounts[name][0]

# doesn't do any verification
class SimpleMiner:
	def __init__(self, addr):
		self.addr = addr
		self._queued_transactions = []

	def queue_transaction(self, t):
		self._queued_transactions.append(t)

	def mine_block(self, prev_hash):
		data_hash = self._block_data_hash(self._queued_transactions, self.addr, prev_hash)
		nonce = str(randint(1,2**256))
		while not proof_of_work_verify(hash_base64(data_hash + nonce)):
			nonce = str(randint(1,2**256))

		res = Block(self._queued_transactions, self.addr, prev_hash, nonce)

		self._queued_transactions = []

		return res

	def _block_data_hash(self, transactions, miner, prev_block_hash):
		transactions_hash = hash_base64(" ".join(t.hash for t in transactions))
		return hash_base64(prev_block_hash + transactions_hash + miner)

class Node(BlockchainManager):
	def __init__(self):
		self.blocks = {"/brad":""}
		self.source_nodes = set()

		self.webserver = HTTPServer(("localhost", 8000), self._create_handler_class())
		self.server_thread = Thread(target=self.webserver.serve_forever)

	def _create_handler_class(node_obj):
		class NodeRequestHandler(BaseHTTPRequestHandler):
			def do_GET(self):
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()

				try:
					self.wfile.write(bytes(node_obj.blocks[self.path].convert_to_str(), "utf-8"))
				except:
					self.wfile.write(bytes("BLOCK NOT FOUND", "utf-8"))
			def log_message(self, format, *args):
				return
		return NodeRequestHandler

	def start_server(self):
		self.server_thread.start()
	def stop_server(self):
		self.webserver.shutdown()
		self.server_thread.join()

	def ping_sources(self):
		pass
	def request_sources(self):
		pass

	def request_newest_block(self):
		pass
	def request_block(self, hash):
		pass