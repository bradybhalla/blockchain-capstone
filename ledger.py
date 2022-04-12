from signature import *

def pub_to_addr(key):
	return hash_base64(key)[:20]

class Transaction:
	def __init__(self, from_addr, to_addr, amount, unique_id):
		self.from_addr = from_addr
		self.to_addr = to_addr
		self.amount = amount

		self.unique_id = unique_id

		self.pub_key = None
		self.sig = None

	def to_str(self):
		vals = [self.from_addr, self.to_addr, self.amount, self.unique_id]
		return " // ".join([str(i) for i in vals])

	def __str__(self):
		return self.to_str()

	def approve(self, sig, pub_key):
		self.pub_key = pub_key
		self.sig = sig


class Ledger:
	def __init__(self):
		self._sig_algorithm = ECDSA()
		self._past_ids = set()
		self._money = {}

		self._sudo = self.create_account()
		self._money[self._sudo[0]] = 0

	def is_valid(self, t):
		# money must be available
		if t.from_addr not in self._money:
			return False
		elif t.amount > self._money[t.from_addr] and t.from_addr != self._sudo[0]:
			return False

		# unique id must not be in past_ids
		if t.unique_id in self._past_ids:
			return False

		# public key must match from_addr
		if pub_to_addr(t.pub_key) != t.from_addr:
			return False

		# sig must be valid
		return self._sig_algorithm.verify(hash_int(t), t.sig, t.pub_key)

	def add_transaction(self, t):
		if self.is_valid(t):
			self._past_ids.add(t.unique_id)

			self._money[t.from_addr] -= t.amount
			if t.to_addr not in self._money:
				self._money[t.to_addr] = 0
			self._money[t.to_addr] += t.amount

			return True

		return False

	def create_account(self):
		pub, priv = self._sig_algorithm.keygen()
		addr = pub_to_addr(pub)
		return (addr, pub, priv)

	def create_signed_transaction(self, account, to_addr, amount):
		addr, pub, priv = account
		t = Transaction(addr, to_addr, amount, randint(1, 2**256))
		H = hash_int(t)
		t.approve(self._sig_algorithm.sign(H, priv), pub)
		return t


if __name__ == "__main__":
	L = Ledger()
	brady = L.create_account()
	t = L.create_signed_transaction(L._sudo, brady[0], 1)
	t2 = L.create_signed_transaction(brady, "bobby", 2)

	print(L.add_transaction(t))
	print(L.add_transaction(t2))
	print(L._money)


