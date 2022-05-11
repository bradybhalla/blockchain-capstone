from blockchain import Block, BlockchainManager

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from threading import Thread, Lock

from abc import ABCMeta, abstractmethod
from pickle import dump, load
from random import choice, sample
from time import sleep

# todo: remove print statements

class ThreadingServer(ThreadingMixIn, HTTPServer):
	pass

# base node that pretty much only receives
class PassiveNode(BlockchainManager):
	def __init__(self, port=8000):
		super().__init__()

		self.blocks = {}
		self.sources = []
		self.known_miners = []

		self.blockchain_lock = Lock()
		self.sources_lock = Lock()

		self.port = port
		self.webserver = ThreadingServer(("0.0.0.0", self.port), self._create_handler_class())
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
		# display money
		if path == ["money"]:
			try:
				with self.blockchain_lock:
					wfile.write(str(self.ledger.money).encode())
			except:
				wfile.write("UH OH".encode())

		# block requests
		elif path == ["block", "latest"]:
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
		elif path == ["source", "miner", "list"]:
			with self.sources_lock:
				wfile.write("\n".join(self.known_miners).encode())

		# ping request
		elif path == ["ping"]:
			wfile.write("RUNNING".encode())
		elif path == ["ping", "miner"]:
			wfile.write("FALSE".encode())

		else:
			wfile.write("INVALID REQUEST".encode())

	def handle_post(self, path, query, wfile):
		# new block
		if path == ["block", "new"]:
			try:
				if "source" in query:
					Thread(target=self.on_new_source, args=(query["source"],)).start()
					Thread(target=self.on_new_block, args=(query["data"],), kwargs={"source":query["source"]}).start()
				else:
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

	def on_new_block(self, block_str, source=None):
		try:
			block = Block.convert_from_str(block_str)
			self.add_block(block, block_str = block_str, source=source)
		except:
			pass

	def add_block(self, block, block_str=None, has_lock=False, **kwargs):
		if not has_lock:
			self.blockchain_lock.acquire()

		try:
			BlockchainManager.add_block(self, block)
		except Exception as e:
			if not has_lock:
				self.blockchain_lock.release()
			raise e


		if block_str is None:
			block_str = block.convert_to_str()


		self.blocks[block.hash] = block_str


		if not has_lock:
			self.blockchain_lock.release()

	def ping_miner(self, source):
		try:
			if self.request(source + "/ping/miner") == "TRUE":
				with self.sources_lock:
					if source not in self.known_miners:
						self.known_miners.append(source)
		except:
			pass

	def on_new_source(self, source):
		with self.sources_lock:
			if source in self.sources:
				return False

		try:
			if self.request(source + "/ping") == "RUNNING":
				with self.sources_lock:
					if source in self.sources:
						return False
					self.sources.append(source)
				Thread(target=self.ping_miner, args=(source,)).start()
				return True
		except:
			return False

	def get_prev_block_hash(self, has_lock=False):
		if not has_lock:
			self.blockchain_lock.acquire()

		res = BlockchainManager.get_prev_block_hash(self)

		if not has_lock:
			self.blockchain_lock.release()

		return res

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
		
		if len(self.sources) == 0:
			res = None
		else:
			res = choice(self.sources)

		if not has_lock:
			self.sources_lock.release()

		return res

	def pick_sources(self, N, has_lock=False):
		if not has_lock:
			self.sources_lock.acquire()

		if len(self.sources) <= N:
			res = self.sources[:]
		else:
			res = sample(self.sources, N)

		if not has_lock:
			self.sources_lock.release()

		return res

	def remove_source(self, source, has_lock=False):
		print("removing", source)
		if not has_lock:
			self.sources_lock.acquire()

		if source in self.sources:
			self.sources.remove(source)
		if source in self.known_miners:
			self.known_miners.remove(source)

		if not has_lock:
			self.sources_lock.release()


	def find_block(self, H, starting_source=None, max_sources=10):
		source = starting_source if starting_source is not None else self.pick_source()

		try:
			block_str = self.request(source + "/block", {"H": H})

			if block_str == "BLOCK NOT FOUND":
				if max_sources > 1:
					return self.find_block(H, max_sources=max_sources-1)
				return None, None

			block = Block.convert_from_str(block_str)
			return block, block_str
		except Exception as e:
			print(262, e)
			self.remove_source(source)
			if max_sources > 1:
				return self.find_block(H, max_sources=max_sources-1)
			return None, None

	def add_block(self, block, block_str=None, source=None, **kwargs):
		stack = [(block, block_str)]

		while True:
			block_needed = stack[-1][0].prev_block_hash

			with self.blockchain_lock:
				if block_needed in self.blocks or block_needed == "0":
					break

			found_block, found_block_str = self.find_block(block_needed, starting_source=source)

			if found_block is None:
				print("could not find a block, canceling operation")
				return

			stack.append((found_block, found_block_str))

		while len(stack) > 0:
			block, block_str = stack.pop()

			with self.blockchain_lock:
				if block.hash not in self.blocks:
					PassiveNode.add_block(self, block, block_str=block_str, has_lock=True)


	# waits [t] seconds, if self.running == False, it returns False and stops waiting
	def _wait_running(self, t):
		while t > 0:
			if not self.running:
				return False

			interval = min(t, 5)
			t -= interval
			sleep(interval)

		return self.running


	def _poll_source_list(self, source):
		try:
			source_list = self.request(source + "/source/list").split("\n")
			for s in source_list:
				if not self.running:
					return
				self.on_new_source(s)
		except Exception as e:
			print(301, str(e))
			self.remove_source(source)

	def poll_sources_background(self, interval=120, num_sources=10):
		while True:

			sources_to_check = self.pick_sources(num_sources)
			for s in sources_to_check:
				Thread(target=self._poll_source_list, args=(s,)).start()

			# wait [interval] seconds but stop if self.running == False
			if not self._wait_running(interval):
				break

	def _poll_latest_block(self, source):
		try:
			block_str = self.request(source + "/block/latest")
			if block_str == "NO BLOCKS RECORDED":
				return
			self.on_new_block(block_str, source=source)
		except Exception as e:
			print(321, str(e))
			self.remove_source(source)

	def poll_blocks_background(self, interval=120, num_sources=10):
		while True:

			sources_to_check = self.pick_sources(num_sources)
			for s in sources_to_check:
				Thread(target=self._poll_latest_block, args=(s,)).start()

			if not self._wait_running(interval):
				break

	def broadcast_self_addr(self, source):
		try:
			self.send(source + "/source/new", {"data":self.web_addr})
		except Exception as e:
			print(339, str(e))
			self.remove_source(source)

	def broadcast_addr_background(self, interval=120, num_sources=10):
		while True:

			sources_to_check = self.pick_sources(num_sources)
			for s in sources_to_check:
				Thread(target=self.broadcast_self_addr, args=(s,)).start()


			if not self._wait_running(interval):
				break

	def on_new_source(self, source):
		if source == self.web_addr:
			return False

		return PassiveNode.on_new_source(self, source)

	def on_new_block(self, block_str, source=None):
		try:
			block = Block.convert_from_str(block_str)

			with self.blockchain_lock:
				if block.hash in self.blocks:
					return

			self.add_block(block, block_str = block_str, source=source)
		except:
			return

		with self.blockchain_lock:
			if self.get_prev_block_hash(has_lock=True) not in self.blocks:
				print("this is bad")
				return
			if self.blocks[self.get_prev_block_hash(has_lock=True)] != block_str:
				return

		self.widely_broadcast_block(block_str, orig_source=source)

	def broadcast_block(self, block_str, source, orig_source=None):
		try:
			if orig_source is None:
				self.send(source + "/block/new", {"data":block_str, "source":self.web_addr})
			else:
				self.send(source + "/block/new", {"data":block_str, "source":orig_source})
		except Exception as e:
			print(382, e)
			self.remove_source(source)

	# broadcast block to up to N random sources
	def widely_broadcast_block(self, block_str, N=20, orig_source=None):
		print("WIDELY BROADCASTING BLOCK")
		l = self.pick_sources(N)

		for source in l:
			Thread(target=self.broadcast_block, args=(block_str, source), kwargs={"orig_source":orig_source}).start()


class SavableNode(metaclass=ABCMeta):
	@abstractmethod
	def get_save_info(self):
		pass

	@abstractmethod
	def create_node(info):
		pass

	def save(self, filename):
		info = self.get_save_info()

		with open(filename, "wb") as f:
			dump(info, f)

	def load(node_type, filename):
		with open(filename, "rb") as f:
			info = load(f)

		return node_type.create_node(info)

class SavableActiveNode(ActiveNode, SavableNode):
	def get_save_info(self):
		return [self.past_blocks, self.ledger, self.blocks, self.sources, self.port, self.web_addr]

	def create_node(info):
		past_blocks, ledger, blocks, sources, port, web_addr = info
		node = SavableActiveNode(web_addr, port=port)

		(node.past_blocks, node.ledger, node.blocks, node.sources) = (past_blocks, ledger, blocks, sources)

		return node

	def get_up_to_date(self, sources):
		for s in sources:
			Thread(target=self.on_new_source, args=(s,)).start()
			Thread(target=self._poll_source_list, args=(s,)).start()
			Thread(target=self._poll_latest_block, args=(s,)).start()
			Thread(target=self.broadcast_self_addr, args=(s,)).start()
	