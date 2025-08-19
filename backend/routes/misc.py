"""Flask API Backend for SPATS"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import starlette.status as status

from ..model import Search


class GeneralRoutes:
    metadata = {
        "name": "General",
        "description": "Various endpoints for other things."
    }

    def __init__(self, database):
        self.db = database

    def __call__(self):
        router = APIRouter(tags=["General"])

        router.add_api_route("/",         endpoint=self.rootToDocs,  methods=["get"])
        router.add_api_route("/search",   endpoint=self.search,      methods=["get"])
        router.add_api_route("/download", endpoint=self.download,    methods=["get"])
        router.add_api_route("/upload",   endpoint=self.upload,      methods=["post"])
        router.add_api_route("/updates",  endpoint=self.updates,     methods=["put"])

        return router


    def rootToDocs(self):
        """Redirects to the docs"""
        return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)

    # def search(self, request: SearchForm):
    def search(self, request: Search):
        """Search for docs"""
        res = self.db.search(request)
        return res

    def download(self):
        """Downlaod database as a json"""
        res = self.db.download()
        return res

    async def upload(self, request: Request):
        """Upload json to load data into database"""
        json = await request.json()
        res = self.db.upload(json)
        return res

    def updates(self):
        """Upload json to load data into database"""
        # pylint: disable=protected-access
        return self.db._updates()


class ImageRoutes:
    metadata = {
        "name": "Image",
        "description": "View and manipulate Images."
    }

    def __init__(self, database):
        self.db = database

    def __call__(self):
        router = APIRouter(tags=["Image"], prefix="/image")

        router.add_api_route("/{_id}",      endpoint=self.get,      methods=["get"])
        router.add_api_route("/{_id}/info", endpoint=self.get_info, methods=["get"])
        router.add_api_route("/create",     endpoint=self.create,   methods=["post"])
        router.add_api_route("/update",     endpoint=self.update,   methods=["put"])
        router.add_api_route("/delete",     endpoint=self.delete,   methods=["delete"])

        return router


    def get(self, _id: str):
        """Get specific image"""
        res = self.db.image_get(_id)
        return res

    def get_info(self, _id: str):
        """Get info on image"""
        res = self.db.image_get_info(_id)
        return res

    def create(self, request: Request):
        """Create new image"""
        files = request.files.getlist("files")
        res = self.db.image_create(files)
        return res

    async def update(self, request: Request):
        """Update image"""
        json = await request.json()
        res = self.db.image_update(json)
        return res

    async def delete(self, request: Request):
        """Delete image"""
        json = await request.json()
        res = self.db.image_delete(json)
        return res


class ExtraRoutes:
    metadata = {
        "name": "Extra",
        "description": "View and manipulate Extras."
    }

    def __init__(self, database):
        self.db = database

    def __call__(self):
        router = APIRouter(tags=["Extra"], prefix="/extra")

        router.add_api_route("/{_id}",      endpoint=self.get,      methods=["get"])
        router.add_api_route("/{_id}/info", endpoint=self.get_info, methods=["get"])
        router.add_api_route("/create",     endpoint=self.create,   methods=["post"])
        router.add_api_route("/update",     endpoint=self.update,   methods=["put"])
        router.add_api_route("/delete",     endpoint=self.delete,   methods=["delete"])

        return router


    def get(self, _id: str):
        """Get extra"""
        res = self.db.extra_get(_id)
        return res

    def get_info(self, _id: str):
        """Get info about extra"""
        res = self.db.extra_get_info(_id)
        return res

    def create(self, request: Request):
        """Create extra"""
        files = request.files.getlist("files")
        res = self.db.extra_create(files)
        return res

    async def update(self, request: Request):
        """Update extra"""
        json = await request.json()
        res = self.db.extra_update(json)
        return res

    async def delete(self, request: Request):
        """Delete extra"""
        json = await request.json()
        res = self.db.extra_delete(json)
        return res

