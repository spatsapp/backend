"""Flask API Backend for SPATS"""
from fastapi import APIRouter

from ..model import SymbolicName, SymbolicCreate, SymbolicUpdate, SymbolicDelete


class SymbolicRoutes:
    metadata = {
        SymbolicName.asset: {
            "name": "Asset",
            "description": "View and manipulate Assets."
        },
        SymbolicName.combo: {
            "name": "Combo",
            "description": "View and manipulate Combos."
        }
    }

    def __init__(self, database, _type: SymbolicName):
        self.db = database
        self._type = _type

    def __call__(self):
        router = APIRouter(tags=[self._type.title()], prefix=f"/{self._type}")

        router.add_api_route("/all",    endpoint=self.all,    methods=["get"])
        router.add_api_route("/create", endpoint=self.create, methods=["post"])
        router.add_api_route("/update", endpoint=self.update, methods=["put"])
        router.add_api_route("/update", endpoint=self.update, methods=["post"], include_in_schema=False)
        router.add_api_route("/delete", endpoint=self.delete, methods=["delete"])
        router.add_api_route("/{_id}",  endpoint=self.get,    methods=["get"])

        return router


    def all(self):
        """List all asset types"""
        return self.db.symbolic_all(self._type)

    def get(self, _id: str):
        """List all asset types"""
        return self.db.symbolic_get(self._type, _id)

    async def create(self, data: SymbolicCreate):
        """Create new asset"""
        return self.db.symbolic_create(self._type, data)

    async def update(self, data: SymbolicUpdate):
        """Update asset"""
        return self.db.symbolic_update(self._type, data)

    def delete(self, data: SymbolicDelete):
        """Delete asset type"""
        return self.db.symbolic_delete(self._type, data)
