from typing import Any
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .suid import SuidInput

class SymbolicName(str, Enum):
    asset = "asset"
    combo = "combo"

class MaterialName(str, Enum):
    thing = "thing"
    group = "group"


class Parameters(BaseModel):
    model_config = ConfigDict(extra='ignore')
    required: bool
    unique: bool
    default: Any

class Attr(BaseModel):
    name: str
    type: str
    description: str
    inherited: bool
    origin: str
    parameters: Parameters

class SymbolicData(BaseModel):
    _id: SuidInput | None = None
    inherit: bool | None = None
    origin: str | None = None
    name: str | None = None
    primary: str | None = None
    secondary: str | None = None
    tertiary: list[str] | None = None
    order: list[str] | None = None
    type_list: list[str] | None = None
    fields: dict[str, Attr] | None = None

class SymbolicChanges(BaseModel):
    name: str | None = None
    fields: dict[str, dict] | None = {}
    order: list[str] | None = []
    primary: str | None = None
    secondary: str | None = None
    tertiary: list[str] | None = None


class SymbolicUpdate(BaseModel):
    _id: SuidInput
    update: SymbolicChanges | None = {}
    unset: dict | None = {} # list[str]
    rename: dict | None = {} # tuples[str, str]


class SymbolicCreate(BaseModel):
    _id: SuidInput | None = None
    inherit: str | None = None
    name: str | None = None
    primary: str | None = None
    secondary: str | None = None
    tertiary: list[str] | None = None
    order: list[str] | None = None
    fields: dict[str, Attr] | None = None

class SymbolicDelete(BaseModel):
    _ids: list[SuidInput]

