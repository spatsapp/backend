# import logging
from os import environ
from typing import Annotated

from environs import Env
from pydantic import BaseModel, MongoDsn, AfterValidator, IPvAnyAddress

def level_validator(value: str) -> str:
    if value.lower() not in ["debug", "info", "warning", "error", "critical"]:
        return ValueError(f"{value} is not a valid log level.")
    return value.lower()    

LogLevel = Annotated[str, AfterValidator(level_validator)]


def port_validator(value: str) -> int:
    port = int(value)
    if 0 < port < 65536:
        return port
    raise ValueError("Port is outside of valid range")

Port = Annotated[int, AfterValidator(port_validator)]

class ConfigModel(BaseModel):
    mongo_uri: MongoDsn | None = "mongodb://localhost:27017/spats"
    debug: bool | None = False
    port: Port | None = 8000
    host: IPvAnyAddress | None = "0.0.0.0"
    workers: int | None = 1
    log_level: LogLevel | None = "info"


class Config:
    def __init__(self, filename="backend.cfg"):
        dot_config = Env(prefix="SPATSBACK_")
        dot_config.read_env(filename)
        tmp_config = {
            **({"mongo_uri": dot} if (dot := dot_config("MONGO_URI", None)) else {}),
            **({"debug": dot} if (dot := dot_config("DEBUG", None)) else {}),
            **({"log_level": dot} if (dot := dot_config("LOG_LEVEL", None)) else {}),
            **self._port(dot_config),
            **self._host(dot_config),
            **self._workers(dot_config)
        }

        self.data = ConfigModel(**tmp_config)

    def _workers(self, config):
        dot = config("WORKERS", None)
        uvicorn = environ.get("WEB_CONCURRENCY")
        if dot or uvicorn:
            return {"workers": dot or uvicorn}
        return {}
    
    def _port(self, config):
        dot = config("PORT", None)
        uvicorn = environ.get("UVICORN_PORT")
        if dot or uvicorn:
            return {"port": dot or uvicorn}
        return {}

    def _host(self, config):
        dot = config("HOST", None)
        uvicorn = environ.get("UVICORN_HOST")
        if dot or uvicorn:
            return {"host": dot or uvicorn}
        return {}

    def __getattr__(self, key):
        return getattr(self.data, key)