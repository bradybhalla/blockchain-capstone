from random import randint
from hashlib import sha256
from base64 import b64encode, b64decode

"""
GCD and modular arithmetic
"""

def gcd(a, b):
	if b==0: return a
	return gcd(b, a%b);

# returns (g, x, y)
# g = gcd(a,b)
# ax + by = g
def xgcd(a, b):
	if b==0:
		return (a, 1, 0)

	q, r = divmod(a, b)
	g, x_1, y_1 = xgcd(b, r)
	return (g, y_1, x_1 - q*y_1)

def mod_inv(a, n):
	g, x, y = xgcd(a, n)
	if g != 1:
		raise ValueError("{} and {} are not coprime".format(a, n))
	return x%n


"""
Primality testing
"""

# check if a is a witness for the compositeness of n
def is_fermat_witness(a, n):
	return pow(a,n,n)!=a

def is_mr_witness(a, n):
	g = gcd(a, n)
	if g != 1 and g != n:
		return True

	q = n-1
	k = 0
	while q%2==0:
		q >>= 1
		k += 1

	a = pow(a,q,n)
	if a==1:
		return False

	for i in range(0, k):
		if a == n-1:
			return False
		a = a*a%n

	return True

def is_prob_prime(n, prob_fail=1e-80):
	if n < 2:
		raise ValueError("Cannot perform primality test on integers less than 2")

	if n==2 or n==3 or n==5 or n==7 or n==11:
		return True

	if n%2==0 or n%3==0 or n%5==0 or n%7==0 or n%11==0:
		return False

	current_prob = 1
	while current_prob > prob_fail:
		a = randint(1, n-1)
		if is_mr_witness(a, n):
			return False
		current_prob *= 0.25
	return True


def gen_prime(bits):
	p = randint(2**(bits-1), 2**bits - 1)
	while not is_prob_prime(p):
		p = randint(2**(bits-1), 2**bits - 1)
	return p


"""
Hashing and converting
"""

def get_hash(s):
	return sha256(str(s).encode())

def hash_int(s):
	return int(get_hash(s).hexdigest(), 16)

def hash_base64(s):
	return b64encode(get_hash(s).digest()).decode()

def int_to_base64(num, num_bytes):
	h = hex(num)[2:]
	if num_bytes*2 - len(h) < 0:
		raise ValueError("{} needs more than {} bytes".format(num, num_bytes))
	h = "0"*(num_bytes*2 - len(h)) + h
	return b64encode(bytes.fromhex(h)).decode()

def base64_to_int(b64):
	return int(b64decode(b64).hex(), 16)