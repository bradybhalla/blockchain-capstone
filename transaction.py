# transaction and ledger classes
# basic units of blockchain

from utils import *
from signature import CompressedECDSA

# class for storing transaction information
class Transaction:
	def __init__(self, from_addr, to_addr, amount, miner_fee, unique_id):
		self.from_addr = from_addr
		self.to_addr = to_addr
		self.amount = int(amount)
		self.miner_fee = int(miner_fee)

		self.unique_id = unique_id

		self.hash = hash_base64(self)

		self.pub_key = None
		self.sig = None

	def __str__(self):
		vals = [self.from_addr, self.to_addr, self.amount, self.miner_fee, self.unique_id]
		return " // ".join([str(i) for i in vals])

	# adds the signature and public key of whoever is sending the transaction
	def approve(self, sig, pub_key):
		self.pub_key = pub_key
		self.sig = sig

	def convert_to_str(self):
		vals = [self.from_addr, self.to_addr, self.amount, self.miner_fee, self.unique_id, self.sig, self.pub_key]
		return " // ".join([str(i) for i in vals])

	def convert_from_str(s):
		from_addr, to_addr, amount, miner_fee, unique_id, sig, pub_key = s.split(" // ")
		res = Transaction(from_addr, to_addr, int(amount), int(miner_fee), unique_id)
		res.approve(sig, pub_key)
		return res

# ledger for storing and validating multiple transactions
# also tracks how much currency everyone has
class Ledger:
	def __init__(self):
		self.sig_algorithm = CompressedECDSA()
		self.past_transactions = set()
		self.money = {}

	# checks if a transaction is valid in the context of the ledger
	def is_valid(self, t):
		# hash must not be in past_transactions
		if t.hash in self.past_transactions:
			return False

		# money must be available
		if t.from_addr not in self.money:
			return False
		elif (t.amount + t.miner_fee) > self.money[t.from_addr] or t.amount < 0 or t.miner_fee < 0:
			return False

		# public key must match from_addr
		if pub_to_addr(t.pub_key) != t.from_addr:
			return False

		# sig must be valid
		return self.sig_algorithm.verify(base64_to_int(t.hash), t.sig, t.pub_key)

	# check if multiple transactions are valid
	def is_valid_multiple(self, ts):
		# can't spend money you don't have, even if you are getting it in the same block
		spending = {}
		transaction_hashes = set()

		for t in ts:

			if not self.is_valid(t):
				return False

			if t.from_addr not in spending:
				spending[t.from_addr] = 0
			spending[t.from_addr] += t.amount + t.miner_fee

			if spending[t.from_addr] > self.money[t.from_addr]:
				return False

			if t.hash in transaction_hashes:
				return False
			transaction_hashes.add(t.hash)

		return True
