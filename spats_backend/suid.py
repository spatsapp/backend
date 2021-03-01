from shortuuid import ShortUUID

class Suid:
	# https://pypi.org/project/shortuuid/
	def __init__(self, length=7, alphabet="abcdfghijklnoqrstuwxyz"):
		self.alphabet = alphabet
		self.length = length
		self.short_uuid = ShortUUID(alphabet=self.alphabet)

	def generate(self):
		return self.short_uuid.random(length=self.length)

	def validate(self, value):
		return len(value) == self.length and all([char in self.alphabet for char in value])

if __name__ == '__main__':
	suid = Suid()