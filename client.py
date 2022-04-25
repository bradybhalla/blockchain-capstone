# classes for client use: creating accounts, mining blocks, running nodes
# TODO this will be broken into other files later

from utils import *
from signature import CompressedECDSA
from transaction import Transaction
from blockchain import Block, BlockchainManager, AddBlockException

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
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
		super().__init__()
		self.blocks = {}
		self.sources = []

		self.webserver = HTTPServer(("localhost", 8000), self._create_handler_class())
		self.server_thread = Thread(target=self.webserver.serve_forever)

	def _create_handler_class(node_obj):
		class NodeRequestHandler(BaseHTTPRequestHandler):
			def log_message(self, format, *args):
				return

			def _set_headers(self):
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()

			def do_GET(self):
				parsed_url = urlparse(self.path)
				path = parsed_url.path.strip("/").split("/")
				query = parse_qs(parsed_url.query)
				query = {i:j[0] for i,j in query.items()}

				self._set_headers()
				node_obj.handle_get(path, query, self.wfile)

			def do_POST(self):
				parsed_url = urlparse(self.path)
				path = parsed_url.path.strip("/").split("/")

				content_length = int(self.headers['Content-Length'])
				data = self.rfile.read(content_length).decode("utf-8")
				data = {i:j[0] for i,j in parse_qs(data).items()}

				self._set_headers()
				node_obj.handle_post(path, data, self.wfile)

		return NodeRequestHandler

	def handle_get(self, path, query, wfile):
		# block requests
		if path == ["block", "latest"]:
			try:
				wfile.write(self.blocks[self.ledger.current_node.hash].encode())
			except KeyError:
				wfile.write("NO BLOCKS RECORDED".encode())
		elif path == ["block"]:
			try:
				wfile.write(self.blocks[query["H"]].encode())
			except KeyError:
				wfile.write("BLOCK NOT FOUND".encode())

		# source requests
		elif path == ["source", "list"]:
			wfile.write("\n".join(self.sources).encode())

		# ping request
		elif path == ["ping"]:
			wfile.write("RUNNING".encode())

		else:
			wfile.write("INVALID REQUEST".encode())

	def handle_post(self, path, query, wfile):
		# new block
		if path == ["block", "new"]:
			try:
				block = Block.convert_from_str(query["data"])
				self.add_block(block)
				self.blocks[block.hash] = query["data"]
				wfile.write("SUCCESS".encode())
			except AddBlockException as e:
				wfile.write(str(e).upper().encode())
			except:
				wfile.write("INVALID REQUEST".encode())

		# new source
		elif path == ["source", "new"]:
			try:
				source = query["data"]
				Thread(target=self.test_source, args=(source,)).start()

				wfile.write("SOURCE RECEIVED".encode())
			except:
				wfile.write("INVALID REQUEST".encode())

		else:
			wfile.write("INVALID REQUEST".encode())

	def start_server(self):
		self.server_thread.start()
	def stop_server(self):
		self.webserver.shutdown()
		self.server_thread.join()

	# add source to list if it is running
	def test_source(self, source):
		if source in self.sources:
			return

		try:
			with urlopen(Request(source + "/ping")) as res:
				if res.read().decode() == "RUNNING":
					self.sources.append(source)
		except:
			return