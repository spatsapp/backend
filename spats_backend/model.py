import math
from typing import Any
from enum import Enum
from datetime import datetime

from pydantic import BaseModel

from .suid import SuidInput
from .support import Decimal


def dump_model(model):
    return model.model_dump(exclude_unset=True, by_alias=True)

def get_symbolic_type(material):
    return SymbolicName.asset if material == MaterialName.thing else SymbolicName.combo


class SymbolicName(str, Enum):
    asset = "asset"
    combo = "combo"

class MaterialName(str, Enum):
    thing = "thing"
    group = "group"


class Parameter(BaseModel):
    required: bool | None = False
    unique: bool | None = False
    default: Any | None = None

class ParameterBoolean(Parameter):
    default: bool

class ParameterString(Parameter):
    default: str
    min_len: int | None = -math.inf
    max_len: int | None = math.inf

class ParameterInteger(Parameter):
    default: int
    min_val: int | None = -math.inf
    max_val: int | None = math.inf

class ParameterDecimal(Parameter):
    default: Decimal
    min_val: Decimal | None = None
    max_val: Decimal | None = None
    precision: int | None = 2

class ParameterDate(Parameter):
    default: datetime
    min_val: datetime | None = None
    max_val: datetime | None = None
    format: str | None = "%Y-%m-%d"

class ParameterList(Parameter):
    default: list | None = []
    type: str | None = "String"
    ordered: bool | None = False

class ParameterReference(Parameter):
    default: str

Parameters = ParameterBoolean | ParameterString | ParameterInteger | ParameterDecimal | ParameterDate | ParameterList | ParameterReference

class Attr(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    inherited: bool | None = None
    origin: str | None = None
    parameters: dict[str, Parameters] | None = None


class SymbolicCreate(BaseModel):
    name: str
    id: SuidInput | None = None
    inherit: str | None = None
    primary: str | None = None
    secondary: str | None = None
    tertiary: list[str] | None = None
    order: list[str] | None = None
    fields: dict[str, Attr] | None = None

class FieldUpdates(BaseModel):
    name: str | None = None
    fields: dict[str, Attr] | None = None
    order: list[str] | None = None
    primary: str | None = None
    secondary: str | None = None
    tertiary: list[str] | None = None

class SymbolicUpdate(BaseModel):
    id: SuidInput
    update: FieldUpdates | None = {}
    rename: dict[str, str] | None = {}
    unset: list[str] | None = []

class SymbolicDelete(BaseModel):
    ids: list[SuidInput]

class MaterialCreate(BaseModel):
    pass

class MaterialUpdate(BaseModel):
    id: SuidInput

class MaterialDelete(BaseModel):
    ids: list[SuidInput]
