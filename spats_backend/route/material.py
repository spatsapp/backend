"""Flask API Backend for SPATS"""
from fastapi import APIRouter, Request

from ..model import MaterialName, SymbolicName, MaterialDelete, MaterialUpdate, MaterialCreate, get_symbolic_type


class MaterialRoutes:
    metadata = {
        MaterialName.thing: {
            "name": "Thing",
            "description": "View and manipulate Things."
        },
        MaterialName.group: {
            "name": "Group",
            "description": "View and manipulate Groups."
        }
    }

    def __init__(self, database, _type):
        self.db = database
        self._type = _type

    def __call__(self):
        router = APIRouter(tags=[self._type.title()], prefix=f"/{self._type}")
        
        router.add_api_route("/all",                     endpoint=self.all,           methods=["get"])
        router.add_api_route("/create",                  endpoint=self.create,        methods=["post"])
        router.add_api_route("/update",                  endpoint=self.update,        methods=["put"])
        router.add_api_route("/update",                  endpoint=self.update,        methods=["post"], include_in_schema=False)
        router.add_api_route("/delete",                  endpoint=self.delete,        methods=["delete"])
        router.add_api_route("/all/{page}",              endpoint=self.all_page,      methods=["get"])
        router.add_api_route("/{symbolic}/{_id}",        endpoint=self.symbolic,      methods=["get"])
        router.add_api_route("/{symbolic}/{_id}/{page}", endpoint=self.symbolic_page, methods=["get"])
        router.add_api_route("/{_id}",                   endpoint=self.get,           methods=["get"])
        
        return router


    def all(self):
        """List all things"""
        return self.db.material_all(self._type, get_symbolic_type(self._type))

    def all_page(self, page: int):
        """List all things"""
        return self.db.material_all(self._type, get_symbolic_type(self._type), page=page)

    def symbolic(self, symbolic: SymbolicName, _id: str):
        """Get all things for specific asset type"""
        return self.db.material_all(self._type, symbolic, _id)

    def symbolic_page(self, symbolic: SymbolicName, _id: str, page: int):
        """Get all things for specific asset type"""
        return self.db.material_all(self._type, symbolic, _id, page=page)

    def get(self, _id: str):
        """Get info for specific thing"""
        return self.db.material_get(self._type, get_symbolic_type(self._type), _id)

    # def create(self, data: MaterialCreate):
    def create(self, request: Request):
        """Create new thing"""
        data = request.json()
        return self.db.material_create(self._type, data)

    def update(self, data: MaterialUpdate):
        """Update thing"""
        return self.db.material_update(self._type, data)

    def delete(self, data: MaterialDelete):
        """Delete thing"""
        return self.db.material_delete(self._type, data)
