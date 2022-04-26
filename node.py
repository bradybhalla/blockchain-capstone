from blockchain import Block, BlockchainManager, AddBlockException

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from threading import Thread, Lock

from pickle import dump, load

class BaseNode(BlockchainManager):
	def __init__(self, web_addr):
		super().__init__()

		self.blocks = {}
		self.sources = []

		self.blockchain_lock = Lock()

		self.web_addr = web_addr
		self.webserver = HTTPServer(self.web_addr, self._create_handler_class())
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
		with self.blockchain_lock:
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
		with self.blockchain_lock:
			# new block
			if path == ["block", "new"]:
				try:
					Thread(target=self.on_new_block, args=(query["data"],)).start()

					wfile.write("BLOCK RECIEVED".encode())

				except:
					wfile.write("INVALID REQUEST".encode())

			# new source
			elif path == ["source", "new"]:
				try:
					source = query["data"]
					Thread(target=self.on_new_source, args=(source,)).start()

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

	def on_new_block(self, block_str):
		try:
			block = Block.convert_from_str(block_str)
			self.add_block(block)
			self.blocks[block.hash] = block_str
		except AddBlockException as e:
			pass
		except:
			pass

	def on_new_source(self, source):
		if source in self.sources:
			return

		try:
			with urlopen(Request(source + "/ping")) as res:
				if res.read().decode() == "RUNNING":
					self.sources.append(source)
		except:
			return

	def send(web_addr, data):
		with urlopen(Request(web_addr, data=urlencode(data).encode())) as res:
			return res.read().decode()

	def request(web_addr, data):
		with urlopen(Request(web_addr + "?" + urlencode(data).encode())) as res:
			return res.read().decode()

class SavableNode(BaseNode):
	def save(self, filename):
		with open(filename, "wb") as f:
			dump(self, f)

	def load(filename):
		with open(filename, "rb") as f:
			node = load(f)

		node.back_online()

		return node

	def back_online(self):
		pass