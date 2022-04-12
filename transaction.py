from signature import *

class Transaction:
	def __init__(self, from_addr, to_addr, amount):
		self.from_addr = from_addr
		self.to_addr = to_addr
		self.amount = amount

		self.unique_id = None

		self.pub_key = None
		self.sig = None

	def to_str(self):
		vals = [self.from_addr, self.to_addr, self.amount, self.unique_id]
		return " // ".join([str(i) for i in vals])

	def approve(self, unique_id, sig_algorithm, pub_key, priv_key):
		self.unique_id = unique_id
		H = self.to_str()

		self.pub_key = pub_key
		self.sig = sig_algorithm.sign(H, priv_key)


"""


TransactionManager
	- check if transactions are valid
		- keep track of past ids

Ledger
	- keep track of people's money

"""