from utils import *

# pretend this is immutable
# keep values between 0 and p-1
class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y
	def __repr__(self):
		if self is O:
			return "O"
		return str((self.x, self.y))

O = Point(-1, -1)

# elliptic curves over the integers mod p
# make sure 4A^3 + 27B^2 != 0
class EllipticCurveFF:
	def __init__(self, p, A, B):
		self.p = p
		self.A = A
		self.B = B

	def equals(self, p1, p2):
		return p1.x==p2.x and p1.y==p2.y

	def contains_point(self, point):
		if point is O:
			return True
		return pow(point.y, 2, self.p) == (pow(point.x, 3, self.p) + self.A*point.x%self.p + self.B)%self.p

	def add(self, point1, point2):
		if point1 is O:
			return point2
		if point2 is O:
			return point1
		if point1.x == point2.x and point1.y == -point2.y%self.p:
			return O

		# regular adding formula
		l = 0
		if point1.x != point2.x or point1.y != point2.y:
			l = (point2.y - point1.y)*mod_inv(point2.x - point1.x, self.p)%self.p
		else:
			l = (3*pow(point1.x, 2, self.p) + self.A)*mod_inv(2*point1.y, self.p)%self.p

		x3 = (pow(l,2,self.p) - point1.x - point2.x)%self.p
		return Point(x3, (l*(point1.x-x3)%self.p - point1.y)%self.p)

	# find point + point + ... + point (n times)
	def mult(self, point, num):
		res = O
		to_add = point
		while num > 0:
			add = num & 1
			if add:
				res = self.add(res, to_add)
			num >>= 1
			to_add = self.add(to_add, to_add)
		return res

	def find_point(self, x):
		a = (pow(x, 3, self.p) + self.A*x%self.p + self.B)%self.p
		is_square = pow(a, (self.p-1)>>1, self.p) == 1
		if not is_square:
			return None

		if self.p%4==1:
			raise ValueError("This method only works on an elliptic curve with p%4==3")

		return Point(x%self.p, pow(a, (self.p+1)>>2, self.p))

	# least significant bit is parity
	# other bits are x-value
	# make sure p%4==3 or uncompressing won't work
	def compress(self, point):
		parity = point.y%2
		return (point.x<<1) + parity

	def uncompress(self, compressed_value):
		parity = compressed_value & 1
		point = self.find_point(compressed_value >> 1)
		if not point.y%2 == parity:
			point.y = -point.y%self.p
		return point