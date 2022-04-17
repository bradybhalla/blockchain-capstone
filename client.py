"""
	def create_account(self):
		pub, priv = self.sig_algorithm.keygen()
		addr = pub_to_addr(pub)
		return (addr, pub, priv)

	# for repeat transactions, change unique_id
	def create_signed_transaction(self, account, to_addr, amount, unique_id=1):
		addr, pub, priv = account
		t = Transaction(addr, to_addr, amount, unique_id)
		H = hash_int(t)
		t.approve(self.sig_algorithm.sign(H, priv), pub)
		return t
"""