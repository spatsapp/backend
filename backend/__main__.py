from argparse import ArgumentParser

from uvicorn import run

from .app import Backend

parser = ArgumentParser(prog="SPATS Backend")
parser.add_argument("-c", "--config")

args = parser.parse_args()

backend = Backend(args.config or "backend.cfg")

app = backend.app
config = backend.config

run(app, host=config.host, port=config.port, log_level=config.log_level)