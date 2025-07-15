"""Flask API Backend for SPATS"""
from functools import partial

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import RedirectResponse
import starlette.status as status

from .database import Database
from .model import SymbolicName, SymbolicCreate, SymbolicUpdate, SymbolicDelete, SymbolicData, MaterialName


def _symbolic_type(material):
    return "asset" if material == "thing" else "combo"


db = Database()


def rootToDocs():
    """Redirects to the docs"""
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)

def search_docs(request: Request):
    """Search for docs"""
    json = request.json()
    res = db.search(json)
    return res

def download():
    """Downlaod database as a json"""
    res = db.download()
    return res

def upload(request: Request):
    """Upload json to load data into database"""
    json = request.json()
    res = db.upload(json)
    return res

def updates():
    """Upload json to load data into database"""
    # pylint: disable=protected-access
    return db._updates()



def symbolic_all(symbolic: SymbolicName):
    """List all asset types"""
    docs = db.symbolic_all(symbolic)
    return docs

def symbolic_get(symbolic: SymbolicName, _id: str):
    """List all asset types"""
    doc = db.symbolic_get(symbolic, _id)
    return doc

# def symbolic_create(symbolic: SymbolicName, request: SymbolicCreate):
async def symbolic_create(symbolic: SymbolicName, request: Request):
    """Create new asset"""
    json = await request.json()
    print(json)
    res = db.symbolic_create(symbolic, json)
    return res

# def symbolic_update(symbolic: SymbolicName, request: SymbolicUpdate):
async def symbolic_update(symbolic: SymbolicName, request: Request):
    """Update asset"""
    json = await request.json()
    print(json)
    res = db.symbolic_update(symbolic, json)
    return res

def symbolic_delete(symbolic: SymbolicName, request: SymbolicDelete):
    """Delete asset type"""
    json = request.json()
    res = db.symbolic_delete(symbolic, json)
    return res


def material_all(material: MaterialName):
    """List all things"""
    docs = db.material_all(material, _symbolic_type(material))
    return docs


def material_all_page(material: MaterialName, page: int):
    """List all things"""
    docs = db.material_all(material, _symbolic_type(material), page=page)
    return docs

def material_symbolic(material: MaterialName, symbolic: SymbolicName, _id: str):
    """Get all things for specific asset type"""
    docs = db.material_all(material, symbolic, _id)
    return docs

def material_symbolic_page(material: MaterialName, symbolic: SymbolicName, _id: str, page: int):
    """Get all things for specific asset type"""
    docs = db.material_all(material, symbolic, _id, page=page)
    return docs

def material_get(material: MaterialName, _id: str):
    """Get info for specific thing"""
    doc = db.material_get(material, _symbolic_type(material), _id)
    return doc

def material_create(material: MaterialName, request: Request):
    """Create new thing"""
    json = request.json()
    res = db.material_create(material, json)
    return res

def material_update(material: MaterialName, request: Request):
    """Update thing"""
    json = request.json()
    res = db.material_update(material, json)
    return res

def material_delete(material: MaterialName, request: Request):
    """Delete thing"""
    json = request.json()
    res = db.material_delete(material, json)
    return res


def image_get(_id: str):
    """Get specific image"""
    res = db.image_get(_id)
    return res

def image_get_info(_id: str):
    """Get info on image"""
    res = db.image_get_info(_id)
    return res

def image_create(request: Request):
    """Create new image"""
    files = request.files.getlist("files")
    res = db.image_create(files)
    return res

def image_update(request: Request):
    """Update image"""
    json = request.json()
    res = db.image_update(json)
    return res

def image_delete(request: Request):
    """Delete image"""
    json = request.json()
    res = db.image_delete(json)
    return res


def extra_get(_id: str):
    """Get extra"""
    res = db.extra_get(_id)
    return res

def extra_get_info(_id: str):
    """Get info about extra"""
    res = db.extra_get_info(_id)
    return res

def extra_create(request: Request):
    """Create extra"""
    files = request.files.getlist("files")
    res = db.extra_create(files)
    return res

def extra_update(request: Request):
    """Update extra"""
    json = request.json()
    res = db.extra_update(json)
    return res

def extra_delete(request: Request):
    """Delete extra"""
    json = request.json()
    res = db.extra_delete(json)
    return res


tags_metadata = [
    {"name": "General", "description": "Various endpoints for other things."},
    {"name": "Asset"  , "description": "View and manipulate Assets."},
    {"name": "Combo"  , "description": "View and manipulate Combos."},
    {"name": "Thing"  , "description": "View and manipulate Things."},
    {"name": "Group"  , "description": "View and manipulate Groups."},
    {"name": "Image"  , "description": "View and manipulate Images."},
    {"name": "Extra"  , "description": "View and manipulate Extras."},
]
app = FastAPI(openapi_tags=tags_metadata)
# app.config.from_pyfile("backend.cfg")
# csrf = CSRFProtect()
# csrf.init_app(app)

asset = APIRouter(tags=["Asset"], prefix="/asset")
combo = APIRouter(tags=["Combo"], prefix="/combo")
thing = APIRouter(tags=["Thing"], prefix="/thing")
group = APIRouter(tags=["Group"], prefix="/group")
image = APIRouter(tags=["Image"], prefix="/image")
extra = APIRouter(tags=["Extra"], prefix="/extra")
other = APIRouter(tags=["General"])

asset.add_api_route("/all",    endpoint=partial(symbolic_all, "asset"), methods=["get"])
asset.add_api_route("/create", endpoint=partial(symbolic_create, "asset"), methods=["post"])
asset.add_api_route("/update", endpoint=partial(symbolic_update, "asset"), methods=["put", "post"])
asset.add_api_route("/delete", endpoint=partial(symbolic_delete, "asset"), methods=["delete"])
asset.add_api_route("/{_id}",  endpoint=partial(symbolic_get, "asset"), methods=["get"])

combo.add_api_route("/all",    endpoint=partial(symbolic_all, "combo"), methods=["get"])
combo.add_api_route("/create", endpoint=partial(symbolic_create, "combo"), methods=["post"])
combo.add_api_route("/update", endpoint=partial(symbolic_update, "combo"), methods=["put", "post"])
combo.add_api_route("/delete", endpoint=partial(symbolic_delete, "combo"), methods=["delete"])
combo.add_api_route("/{_id}",  endpoint=partial(symbolic_get, "combo"), methods=["get"])

thing.add_api_route("/all",                     endpoint=partial(material_all, "thing"),           methods=["get"])
thing.add_api_route("/create",                  endpoint=partial(material_create, "thing"),        methods=["post"])
thing.add_api_route("/update",                  endpoint=partial(material_update, "thing"),        methods=["put"])
thing.add_api_route("/delete",                  endpoint=partial(material_delete, "thing"),        methods=["delete"])
thing.add_api_route("/all/{page}",              endpoint=partial(material_all_page, "thing"),      methods=["get"])
thing.add_api_route("/{symbolic}/{_id}",        endpoint=partial(material_symbolic, "thing"),      methods=["get"])
thing.add_api_route("/{symbolic}/{_id}/{page}", endpoint=partial(material_symbolic_page, "thing"), methods=["get"])
thing.add_api_route("/{_id}",                   endpoint=partial(material_get, "thing"),           methods=["get"])

group.add_api_route("/all",                     endpoint=partial(material_all, "group"),           methods=["get"])
group.add_api_route("/create",                  endpoint=partial(material_create, "group"),        methods=["post"])
group.add_api_route("/update",                  endpoint=partial(material_update, "group"),        methods=["put"])
group.add_api_route("/delete",                  endpoint=partial(material_delete, "group"),        methods=["delete"])
group.add_api_route("/all/{page}",              endpoint=partial(material_all_page, "group"),      methods=["get"])
group.add_api_route("/{symbolic}/{_id}",        endpoint=partial(material_symbolic, "group"),      methods=["get"])
group.add_api_route("/{symbolic}/{_id}/{page}", endpoint=partial(material_symbolic_page, "group"), methods=["get"])
group.add_api_route("/{_id}",                   endpoint=partial(material_get, "group"),           methods=["get"])

image.add_api_route("/{_id}",      endpoint=image_get,      methods=["get"])
image.add_api_route("/{_id}/info", endpoint=image_get_info, methods=["get"])
image.add_api_route("/create",     endpoint=image_create,   methods=["post"])
image.add_api_route("/update",     endpoint=image_update,   methods=["put"])
image.add_api_route("/delete",     endpoint=image_delete,   methods=["delete"])

extra.add_api_route("/{_id}",      endpoint=extra_get,      methods=["get"])
extra.add_api_route("/{_id}/info", endpoint=extra_get_info, methods=["get"])
extra.add_api_route("/create",     endpoint=extra_create,   methods=["post"])
extra.add_api_route("/update",     endpoint=extra_update,   methods=["put"])
extra.add_api_route("/delete",     endpoint=extra_delete,   methods=["delete"])

other.add_api_route("/",         endpoint=rootToDocs,  methods=["get"])
other.add_api_route("/search",   endpoint=search_docs, methods=["get"])
other.add_api_route("/download", endpoint=download,    methods=["get"])
other.add_api_route("/upload",   endpoint=upload,      methods=["post"])
other.add_api_route("/updates",  endpoint=updates,     methods=["put"])


app.include_router(asset)
app.include_router(combo)
app.include_router(thing)
app.include_router(group)
app.include_router(image)
app.include_router(extra)
app.include_router(other)
