from utils import *
from elliptic import *
from abc import ABCMeta, abstractmethod

class DigitalSignature(metaclass=ABCMeta):
	# generate params if needed
	def __init__(self):
		pass

	# return (public, private)
	@abstractmethod
	def keygen(self):
		pass

	@abstractmethod
	def sign(self, H, priv):
		pass

	@abstractmethod
	def verify(self, H, sig, pub):
		pass

class RSA(DigitalSignature):
	def __init__(self):
		self.prime_bits = 1024

	def keygen(self):
		p = gen_prime(self.prime_bits)
		q = gen_prime(self.prime_bits)

		N = p*q

		e = 2**16 + 1
		d = mod_inv(e, (p-1)*(q-1))

		return ((e, N), (d, N))

	def sign(self, H, priv):
		return pow(H, priv[0], priv[1])

	def verify(self, H, sig, pub):
		H_1 = pow(sig, pub[0], pub[1])
		return H == H_1

class DSA(DigitalSignature):
	def __init__(self):
		L,N = 1024,160

		self.q = gen_prime(N)
		self.p = randint(2**(L-N-1), 2**(L-N) - 1)*self.q + 1
		while not is_prob_prime(self.p):
			self.p = randint(2**(L-N-1), 2**(L-N) - 1)*self.q + 1
		self.g = pow(2, (self.p-1)//self.q, self.p)

	def keygen(self):
		priv = randint(2, self.q-1)
		pub = pow(self.g, priv, self.p)
		return (pub, priv)

	def sign(self, H, priv):
		k = randint(1, self.q-1)
		S1 = pow(self.g, k, self.p)%self.q
		S2 = (H + priv*S1)*mod_inv(k, self.q)%self.q
		return (S1, S2)

	def verify(self, H, sig, pub):
		S1, S2 = sig
		S2_inv = mod_inv(S2, self.q)
		V1 = H*S2_inv%self.q
		V2 = S1*S2_inv%self.q
		return pow(self.g, V1, self.p)*pow(pub, V2, self.p)%self.p%self.q == S1

# uses secp256k1 curve (bitcoin curve)
# public key is compressed
class ECDSA(DigitalSignature):
	def __init__(self):
		# define curve
		self.curve = EllipticCurveFF(2**256 - 2**32 - 977, 0, 7)

		# get generator point
		self.G = self.curve.uncompress(0xF37CCCFDF3B97758AB40C52B9D0E160E0537F9B65B9C51B2B3E502B62DF02F30)

		# (prime) order of generator point
		self.n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

	def keygen(self):
		priv = randint(0,self.n-1)
		pub = self.curve.compress(self.curve.mult(self.G, priv))
		return (pub, priv)

	def sign(self, H, priv):
		k = randint(0,self.n-1)
		S1 = self.curve.mult(self.G, k).x%self.n
		S2 = mod_inv(k, self.n)*(H + S1*priv)%self.n
		return (S1, S2)

	def verify(self, H, sig, pub):
		S1, S2 = sig
		S2_inv = mod_inv(S2, self.n)
		V = self.curve.mult(self.G, H*S2_inv%self.n)
		V = self.curve.add(V, self.curve.mult(self.curve.uncompress(pub), S1*S2_inv%self.n))
		return V.x%self.n == S1