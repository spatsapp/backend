"""Flask API Backend for SPATS"""
from types import SimpleNamespace
from fastapi import FastAPI
from .database import Database
from .model import SymbolicName, MaterialName
from .routes.material import MaterialRoutes
from .routes.symbolic import SymbolicRoutes
from .routes.misc import ExtraRoutes, GeneralRoutes, ImageRoutes
from .config import Config

class Backend:
    def __init__(self, config_file="backend.cfg"):
        self.config = Config(config_file)

        self.db = Database(uri=str(self.config.mongo_uri))

        self.routers = SimpleNamespace(**{
            "asset": SymbolicRoutes(self.db, "asset"),
            "combo": SymbolicRoutes(self.db, "combo"),
            "thing": MaterialRoutes(self.db, "thing"),
            "group": MaterialRoutes(self.db, "group"),
            "image": ImageRoutes(self.db),
            "extra": ExtraRoutes(self.db),
            "other": GeneralRoutes(self.db),
        })

        self.tags_metadata = [
            self.routers.other.metadata,
            self.routers.asset.metadata[SymbolicName.asset],
            self.routers.combo.metadata[SymbolicName.combo],
            self.routers.thing.metadata[MaterialName.thing],
            self.routers.group.metadata[MaterialName.group],
            self.routers.image.metadata,
            self.routers.extra.metadata,
        ]

        self.app = FastAPI(openapi_tags=self.tags_metadata)

        self.app.include_router(self.routers.asset())
        self.app.include_router(self.routers.combo())
        self.app.include_router(self.routers.thing())
        self.app.include_router(self.routers.group())
        self.app.include_router(self.routers.image())
        self.app.include_router(self.routers.extra())
        self.app.include_router(self.routers.other())
