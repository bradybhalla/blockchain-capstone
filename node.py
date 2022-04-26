from blockchain import Block, BlockchainManager, AddBlockException

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from threading import Thread, Lock

from pickle import dump, load
from random import choice, sample
from time import sleep

# base node that pretty much only receives
class PassiveNode(BlockchainManager):
	def __init__(self, port=8000):
		super().__init__()

		self.blocks = {}
		self.sources = []

		self.blockchain_lock = Lock()
		self.sources_lock = Lock()

		self.port = port
		self.webserver = HTTPServer(("localhost", self.port), self._create_handler_class())
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
				with self.blockchain_lock:
					wfile.write(self.blocks[self.ledger.current_node.hash].encode())
			except KeyError:
				wfile.write("NO BLOCKS RECORDED".encode())
		elif path == ["block"]:
			try:
				with self.blockchain_lock:
					wfile.write(self.blocks[query["H"]].encode())
			except KeyError:
				wfile.write("BLOCK NOT FOUND".encode())

		# source requests
		elif path == ["source", "list"]:
			with self.sources_lock:
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
		self.webserver.server_close()
		self.server_thread.join()


	def request(self, web_addr, data={}):
		with urlopen(Request(web_addr + "?" + urlencode(data))) as res:
			return res.read().decode()

	def on_new_block(self, block_str):
		try:
			with self.blockchain_lock:
				block = Block.convert_from_str(block_str)
				self.add_block(block)
				self.blocks[block.hash] = block_str
			return True
		except AddBlockException as e:
			pass
		except:
			pass
		return False

	def on_new_source(self, source):
		with self.sources_lock:
			if source in self.sources:
				return False

		try:
			if self.request(source + "/ping") == "RUNNING":
				with self.sources_lock:
					self.sources.append(source)
				return True
		except:
			return False

# node that will ask for information it doesn't have
class ActiveNode(PassiveNode):
	def __init__(self, web_addr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.web_addr = web_addr
		self.background_threads = [
									Thread(target=self.poll_sources_background),
									Thread(target=self.poll_blocks_background),
									Thread(target=self.broadcast_addr_background)
								  ]
		self.running = False

	def start(self):
		self.running = True
		self.start_server()
		for t in self.background_threads:
			t.start()

	def stop(self):
		self.running = False
		self.stop_server()
		for t in self.background_threads:
			t.join()

	def send(self, web_addr, data):
		with urlopen(Request(web_addr, data=urlencode(data).encode())) as res:
			return res.read().decode()

	def pick_source(self, has_lock=False):
		if not has_lock:
			self.sources_lock.acquire()
		
		res = choice(self.sources)

		if not has_lock:
			self.sources_lock.release()

		return res

	def pick_sources(self, N, has_lock=False):
		if not has_lock:
			self.sources_lock.acquire()

		res = sample(self.sources, N)

		if not has_lock:
			self.sources_lock.release()

		return res

	def remove_source(self, source, has_lock=False):
		if not has_lock:
			self.sources_lock.acquire()

		if source in self.sources:
			self.sources.remove(source)

		if not has_lock:
			self.sources_lock.release()

	# waits [t] seconds, if self.running == False, it returns False and stops waiting
	def _wait_running(self, t):
		while t > 0:
			if not self.running:
				return False

			interval = min(t, 5)
			t -= interval
			sleep(interval)

		return self.running

	def poll_sources_background(self, interval=30):
		while True:

			# todo, pick a random source, get sources, incorporate them
			#print("polling for sources")

			# wait 30 seconds but stop if self.running == False
			if not self._wait_running(interval):
				break

	def poll_blocks_background(self, interval=10):
		while True:

			# todo, pick a random source, get latest block, incorporate it
			#print("polling for blocks")

			if not self._wait_running(interval):
				break

	def broadcast_addr_background(self, interval=30):
		while True:

			# todo, pick a random source, get latest block, incorporate it
			#print("broadcasting my address")

			if not self._wait_running(interval):
				break

	def broadcast_block(self, block_str, source):
		try:
			self.send(source + "/block/new", {"data":block_str})
		except:
			self.remove_source(source)

	# broadcast block to up to N random sources
	def widely_broadcast_block(self, block_str, N=20):
		with self.sources_lock:
			l = self.sources if len(self.sources) <= N else self.pick_sources(N, has_lock=True)

		for source in l:
			Thread(target=self.broadcast_block, args=(block_str, source)).start()

"""
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
"""