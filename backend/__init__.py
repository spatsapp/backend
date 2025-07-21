"""Flask API Backend for SPATS"""
from fastapi import FastAPI
from .database import Database
from .model import SymbolicName, MaterialName
from .route.material import MaterialRoutes
from .route.symbolic import SymbolicRoutes
from .route.misc import ExtraRoutes, GeneralRoutes, ImageRoutes

db = Database()

asset = SymbolicRoutes(db, "asset")
combo = SymbolicRoutes(db, "combo")
thing = MaterialRoutes(db, "thing")
group = MaterialRoutes(db, "group")
image = ImageRoutes(db)
extra = ExtraRoutes(db)
other = GeneralRoutes(db)

tags_metadata = [
    other.metadata,
    asset.metadata[SymbolicName.asset],
    combo.metadata[SymbolicName.combo],
    thing.metadata[MaterialName.thing],
    group.metadata[MaterialName.group],
    image.metadata,
    extra.metadata,
]
app = FastAPI(openapi_tags=tags_metadata)
# app.config.from_pyfile("backend.cfg")
# csrf = CSRFProtect()
# csrf.init_app(app)

app.include_router(asset())
app.include_router(combo())
app.include_router(thing())
app.include_router(group())
app.include_router(image())
app.include_router(extra())
app.include_router(other())
