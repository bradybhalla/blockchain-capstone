# classes for client use: creating accounts, mining blocks, running nodes
# TODO this will be broken into other files later

from utils import *
from signature import CompressedECDSA
from transaction import Transaction
from blockchain import Block

from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class Wallet:
	def __init__(self):
		self.sig_algorithm = CompressedECDSA()
		self.accounts = {}
		self.known_miners = []

	# create new account and calculate keys
	def create_account(self, name, password=None):
		if password is None:
			priv = None
		else:
			priv = pow(2, hash_int(password), self.sig_algorithm.n)
		pub, priv = self.sig_algorithm.keygen(priv=priv)
		addr = pub_to_addr(pub)
		self.accounts[name] = (addr, pub, priv)

	# create a transaction from an account to another account
	def create_transaction(self, account_name, to_addr, amount, miner_fee):
		addr, pub, priv = self.accounts[account_name]
		t = Transaction(addr, to_addr, amount, miner_fee, hash_base64(randint(1,2**20)))
		H = hash_int(t)
		t.approve(self.sig_algorithm.sign(H, priv), pub)
		return t

	def get_addr(self, name):
		return self.accounts[name][0]

	# send a transaction to a node
	def send_transaction(self, web_addr, t):
		try:
			with urlopen(Request(web_addr + "/transaction/new", data=urlencode({"data":t}).encode())) as res:
				return res.read().decode()
		except:
			if web_addr in self.known_miners:
				self.known_miners.remove(web_addr)

	# creates a new transaction and sends it to all nodes
	def transact(self, account_name, to_addr, amount, miner_fee):
		t = self.create_transaction(account_name, to_addr, amount, miner_fee).convert_to_str()
		for i in self.known_miners:
			Thread(target=self.send_transaction, args=(i, t)).start()

	# finds new miners from its current miners
	def add_miners(self, source):
		try:
			with urlopen(Request(source + "/source/miner/list")) as res:
				for i in res.read().decode().split("\n"):
					if i not in self.known_miners:
						self.known_miners.append(i)
		except:
			pass