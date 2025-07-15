"""ShortUUID wrapper"""
from shortuuid import ShortUUID
from typing import Annotated

from pydantic import AfterValidator, BaseModel

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

def _suid_valid(value: str) -> bool:
    if Suid().validate(value):
        return True
    raise ValueError(f'{value} is not a valid suid')

class SuidInput(BaseModel):
    value: Annotated[str, AfterValidator(_suid_valid)]