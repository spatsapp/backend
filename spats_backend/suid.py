"""ShortUUID wrapper"""
from shortuuid import ShortUUID


class Suid:
    """ShortUUID wrapper"""

    # https://pypi.org/project/shortuuid/
    def __init__(self, length=7, alphabet="abcdfghijklnoqrstuwxyz"):
        self.alphabet = alphabet
        self.length = length
        self.short_uuid = ShortUUID(alphabet=self.alphabet)

    def generate(self):
        """Create new suid"""
        return self.short_uuid.random(length=self.length)

    def validate(self, value):
        """Validate suid is valid"""
        chars_in_alpha = [char in self.alphabet for char in value]
        return len(value) == self.length and all(chars_in_alpha)


if __name__ == "__main__":
    suid = Suid()
