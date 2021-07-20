"""Interface for mongo database"""
# pylint: disable=too-many-lines

from collections.abc import MutableMapping
from os.path import splitext

from flask import current_app, request
from flask_pymongo import PyMongo
from gridfs import GridFS, NoFile
from pymongo.errors import PyMongoError
from werkzeug.wsgi import wrap_file

from .field_parser import FieldParser
from .suid import Suid


class Error(Exception):
    """Base class for module exceptions"""

    def __init__(self, message):
        super().__init__()
        self.message = message


class NoDocumentFound(Error):
    """No documents exist for requested type"""


class RequiredAttributeError(Error):
    """Required field not given"""


class UniqueAttributeError(Error):
    """Unique filed not unique"""


class InvalidSuidError(Error):
    """Suid is invalid"""


class InvalidSymbolicError(Error):
    """Symbolic id or name is invlaid"""


class TupleNoneCompare:
    """Compare Class than can be None or a valid tuple"""

    def __init__(self, x):
        self.x = x

    @staticmethod
    def _not_same(x, y):
        return (
            (x is None and y is not None)
            or (x is not None and y is None)
            or (not isinstance(x, type(y)))
        )

    def __len__(self):
        return len(self.x)

    def __getitem__(self, y):
        return self.x[y]

    def __lt__(self, y):
        x = self.x
        len_x = len(x)
        len_y = len(y)
        for i in range(max(len_x, len_y)):
            # pylint: disable=too-many-boolean-expressions
            if (
                self._not_same(x[i], y[i])
                or (len_x > i and len_y == i)
                or ((x[i] is not None or y[i] is not None) and (x[i] > y[i]))
            ):
                return False
            if (len_x == i and len_y > i) or (
                (x[i] is not None or y[i] is not None) and (x[i] < y[i])
            ):
                return True
        return False

    def __le__(self, y):
        return self.__lt__(y) or self.__eq__(y)

    def __eq__(self, y):
        x = self.x
        if (
            (len(x) != len(y))
            or self._not_same(x[0], y[0])
            or (x[0] != y[0])
            or self._not_same(x[1], y[1])
            or (x[1] != y[1])
        ):
            return False
        len_x = len(x)
        for i in range(2, len_x):
            if self._not_same(x[i], y[i]) or (x[i] != y[i]):
                return False
        return True

    def __ne__(self, y):
        return not self.__eq__(y)

    def __gt__(self, y):
        return not self.__lt__(y)

    def __ge__(self, y):
        return self.__gt__(y) or self.__eq__(y)


# pylint: disable=too-many-public-methods
class Database:
    """API interface for a Mongo database"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initalize the app"""
        self.app = app
        self.mongo = PyMongo()
        self.mongo.init_app(app)
        self.database = self.mongo.db
        self.image = GridFS(self.database, "image")
        self.extra = GridFS(self.database, "extra")

        self.suid = Suid()
        self.field_parser = FieldParser()

        self._init_database()

    def _init_database(self):
        try:
            self._get("asset", {"name": "Asset"})
        except NoDocumentFound:
            _id = self.suid.generate()
            self._insert(
                "asset",
                {
                    "_id": _id,
                    "name": "Asset",
                    "fields": {
                        "Combos": {
                            "description": "List of names of combos it's in",
                            "parameters": {"list_type": "reference"},
                            "type": "list",
                            "origin": _id,
                        },
                        "Name": {
                            "description": "What you call the thing",
                            "parameters": {"required": True},
                            "type": "string",
                            "origin": _id,
                        },
                        "Notes": {
                            "description": "Special notes that don't fit in any other attributes",
                            "parameters": {},
                            "type": "string",
                            "origin": _id,
                        },
                        "Pics": {
                            "description": "List of pics of the thing",
                            "parameters": {"list_type": "reference"},
                            "type": "list",
                            "origin": _id,
                        },
                    },
                    "order": ["Name", "Notes", "Pics", "Combos"],
                    "primary": "Name",
                    "secondary": None,
                    "tertiary": None,
                    "type_list": [_id],
                },
            )

        try:
            self._get("combo", {"name": "Combo"})
        except NoDocumentFound:
            _id = self.suid.generate()
            self._insert(
                "combo",
                {
                    "_id": _id,
                    "name": "Combo",
                    "fields": {
                        "Combos": {
                            "description": "List of names of combos it's in",
                            "parameters": {"list_type": "reference"},
                            "type": "list",
                            "origin": _id,
                        },
                        "Name": {
                            "description": "What you call the thing",
                            "parameters": {"required": True},
                            "type": "string",
                            "origin": _id,
                        },
                        "Notes": {
                            "description": "Special notes that don't fit in any other attributes",
                            "parameters": {},
                            "type": "string",
                            "origin": _id,
                        },
                        "Pics": {
                            "description": "List of pics of the thing",
                            "parameters": {"list_type": "reference"},
                            "type": "list",
                            "origin": _id,
                        },
                    },
                    "order": ["Name", "Notes", "Pics", "Combos"],
                    "primary": "Name",
                    "secondary": None,
                    "tertiary": None,
                    "type_list": [_id],
                },
            )

    @staticmethod
    def _error_json(error, document, **kwargs):
        if isinstance(error, Exception):
            msg = f"{error.__class__.__qualname__}: {error.message}"
        else:
            msg = str(error)
        doc = {
            "error": msg,
            "document": document,
        }
        for key, value in kwargs.items():
            doc[key] = value
        return doc

    @staticmethod
    def _to_list(json):
        if isinstance(json, dict):
            return [json] if json.keys() else []
        if isinstance(json, list):
            return json
        return []

    def _flatten(self, dic, parent_key="", sep=".", rename=False):
        # https://stackoverflow.com/a/6027615
        items = []
        for key, value in dic.items():
            new_key = parent_key + sep + key if parent_key else key
            if value and isinstance(value, MutableMapping):
                items.extend(
                    self._flatten(
                        value,
                        parent_key=new_key,
                        sep=sep,
                        rename=rename,
                    ).items()
                )
            else:
                if rename:
                    value = parent_key + sep + value if parent_key else value
                items.append((new_key, value))
        return dict(items)

    def _get(self, collection, filter_, error=True):
        doc = self.database[collection].find_one(filter_)
        if doc is None and error:
            raise NoDocumentFound(
                f'No document in collection "{collection}" matches filter: {filter_}'
            )
        return doc

    def _get_many(self, collection, filter_=None, error=True):
        filter_ = filter_ or {}
        docs = list(self.database[collection].find(filter_))
        if len(docs) == 0 and error:
            raise NoDocumentFound(
                f'No documents in collection "{collection}" matches filter: {filter_}'
            )
        return docs

    # pylint: disable=dangerous-default-value
    def _search(self, collection, filter_={}):
        return self.database[collection].find(filter_)

    def _insert(self, collection, document):
        return self.database[collection].insert_one(document)

    def _insert_many(self, collection, documents):
        return self.database[collection].insert_many(documents)

    def _update(
        self,
        collection,
        filter_,
        document,
        preflat=False,
    ):
        values = {}
        update = document.get("update", None)
        unset = document.get("unset", None)
        rename = document.get("rename", None)

        if preflat:
            if update:
                values["$set"] = update
            if unset:
                values["$unset"] = unset
        else:
            if update:
                values["$set"] = self._flatten(update)
            if unset:
                values["$unset"] = self._flatten(unset)
        res = self.database[collection].update_one(
            filter_,
            values,
            upsert=False,
        )

        if rename:
            _ = self.database[collection].update_one(
                filter_,
                {"$rename": rename if preflat else self._flatten(rename, rename=True)},
                upsert=False,
            )

        return res

    def _update_many(self, collection, filter_, update):
        flat_update = self._flatten(update)
        return self.database[collection].update_many(
            filter_,
            {"$set": flat_update},
            upsert=False,
        )

    def _delete(self, collection, filter_):
        return self.database[collection].delete_one(filter_)

    def _delete_many(self, collection, filter_):
        return self.database[collection].delete_many(filter_)

    @staticmethod
    def _merge_docs(inherit, child):
        if inherit == {}:
            return child
        for field in child["fields"].values():
            if field["name"] in inherit["fields"]:
                i_field = inherit["fields"][field["name"]]
                if (
                    field["type"] == i_field["type"]
                    and field["description"] == i_field["description"]
                    and field["parameters"] == i_field["parameters"]
                ):
                    field["inherited"] = True
                    field["origin"] = i_field["origin"]
                else:
                    field["inherited"] = False
                    field["origin"] = child["_id"]
            else:
                field["inherited"] = False
                field["origin"] = child["_id"]
        return child

    def _check_unique(self, value, name, origin, type_):
        try:
            existing_doc = self._get(
                type_, {"type_list": origin, f"fields.{name}": value}
            )
        except NoDocumentFound:
            return True
        else:
            return existing_doc is None

    def _name_or_id(self, value):
        if value.startswith("_"):
            return {"name": value[1:]}
        if self.suid.validate(value):
            return {"_id": value}
        raise InvalidSymbolicError(f'"{value}" is not a valid name or suid')

    def _verify(self, json, template, type_, unset=None):
        transformed = {}
        if unset is None:
            unset = {}
        fields = template["fields"]
        for name, field in fields.items():
            field_type = field["type"]
            params = field.get("parameters", {})
            required = params.get("required", False)
            unique = params.get("unique", False)
            if required and name not in json and unset and name in unset:
                raise RequiredAttributeError(
                    f'"{name}" required field when creating asset "{template["name"]}"'
                )
            if name not in json and "default" in params:
                transformed[name] = params["default"]
            elif name in json:
                transformed[name] = self.field_parser.parse(
                    field_type, json[name]["value"], params
                )
            if (
                unique
                and name in transformed
                and transformed[name] is not None
                and not self._check_unique(
                    transformed[name],
                    name,
                    field["origin"],
                    type_,
                )
            ):
                raise UniqueAttributeError(
                    f'"{name}" is a unique field and matches another document'
                )
        return transformed

    def _to_id_dic(self, json_list):
        res = {}
        for json in self._to_list(json_list):
            _id = json["_id"]
            del json["_id"]
            res[_id] = json
        return res

    def _symbolic_all(self, type_):
        try:
            docs = self._get_many(type_)
        except NoDocumentFound:
            docs = []
        return sorted(docs, key=lambda doc: doc.get("name"))

    def _symbolic_get(self, type_, value):
        res = {}
        try:
            doc = self._name_or_id(value)
            res[type_] = self._get(type_, doc)
        except NoDocumentFound:
            pass
        except InvalidSymbolicError as e:
            res["error"] = str(e)
            res["lookup"] = value
        return res

    def _symbolic_lookup(self, type_, value):
        try:
            doc = self._name_or_id(value)
            symbolic = self._get(type_, doc)
        except NoDocumentFound as e:
            raise InvalidSymbolicError(
                f'"{value}" does not exist as a {type_} type'
            ) from e
        return symbolic

    def _symbolic_name_check(self, type_, name):
        if name is None:
            raise InvalidSymbolicError(f"{type_} name cannot be empty")
        try:
            self._symbolic_lookup(type_, name)
        except InvalidSymbolicError:
            return True
        else:
            raise InvalidSymbolicError(f'"{name[1:]}" already exists as a {type_} name')

    def _symbolic_create(self, type_, json_list, ignore=False):
        created = []
        errors = []
        merged = False

        for json in self._to_list(json_list):
            json["_id"] = json.get("_id") or self.suid.generate()
            inherit = json.get("inherit")
            try:
                self._symbolic_name_check(type_, f'_{json.get("name")}')
                if inherit is None and json.get("name", "").lower() == type_:
                    symbolic = {}
                else:
                    symbolic = self._symbolic_lookup(type_, inherit)
            except (InvalidSymbolicError, PyMongoError) as e:
                errors.append(self._error_json(e, json))
            else:
                json = self._merge_docs(symbolic, json)
                json["type_list"] = symbolic.get("type_list", []) + [json["_id"]]
                merged = True
            finally:
                if ignore or merged:
                    res = self._insert(type_, json)
                    created.append(res.inserted_id)

        return {"created": created, "errored": errors}

    # pylint: disable=too-many-locals
    def _symbolic_update(self, type_, json_list):
        updated = 0
        errors = []

        for json in self._to_list(json_list):
            _id = json["_id"]
            update = json.get("update", {})
            if not self.suid.validate(_id):
                errors.append(
                    self._error_json(
                        f'"{_id}" is an invalid suid.',
                        json,
                        lookup=_id,
                    )
                )
                continue
            if "fields" in update:
                to_update = self._get(type_, {"_id": _id})
                for name, value in update["fields"].items():
                    if (
                        to_update["fields"].get(name, {}).get("inherited", False)
                        or "inherited" not in value
                    ):
                        value["inherited"] = False
                    if "parameters" not in value:
                        value["parameters"] = {}
                    if "origin" not in value:
                        value["origin"] = _id
            res = self._update(type_, {"_id": _id}, json)
            if not res.matched_count:
                errors.append(
                    self._error_json(
                        f'"{_id}" does not match any documents to update',
                        json,
                        lookup=_id,
                    )
                )
                continue
            updated += res.matched_count
            if "fields" in update or "rename" in json:
                children = [
                    child
                    for child in self._get_many(type_, {"type_list": _id})
                    if child["_id"] != _id
                ]
                for child in children:
                    child_update = {}
                    for name, value in update.get("fields", {}).items():
                        if child["fields"][name]["inherited"]:
                            child_update[name] = value
                    if child_update:
                        document = {
                            "update": {"fields": child_update} if child_update else {},
                            "rename": json.get("rename", {}),
                        }
                        child_res = self._update(type_, {"_id": child["_id"]}, document)
                        updated += child_res.matched_count

        return {"updated": updated, "errored": errors}

    def _symbolic_delete(self, type_, json_list):
        deleted = 0
        errors = []

        for _id in self._to_list(json_list):
            if not self.suid.validate(_id):
                errors.append(
                    {"message": f'"{_id}" is an invalid suid.', "lookup": _id}
                )
            res = self._delete(type_, {"_id": _id})
            if not res.deleted_count:
                errors.append(
                    {
                        "message": f'"{_id}" does not match any documents to delete',
                        "lookup": _id,
                    }
                )
            else:
                deleted += res.deleted_count

        return {"deleted": deleted, "errored": errors}

    def _material_decode(self, raw_res, symbolic_res):
        res = {"_id": raw_res["_id"], "type": raw_res["type"], "fields": {}}
        for key, value in raw_res["fields"].items():
            cur_symbolic = symbolic_res["fields"][key]
            field_type = cur_symbolic["type"]
            field_params = cur_symbolic["parameters"]
            res["fields"][key] = self.field_parser.decode(
                field_type, value, field_params
            )
        return res

    @staticmethod
    def _material_sort_key(symbolic_res):
        def helper(doc):
            symbolic = symbolic_res[doc["type"]]
            primary_key = symbolic.get("primary")
            secondary_key = symbolic.get("secondary")
            tertiary_keys = symbolic.get("tertiary", [])
            fields = doc["fields"]
            vals = [fields.get(primary_key), fields.get(secondary_key)]
            if tertiary_keys:
                vals.extend([fields.get(key) for key in tertiary_keys])
            return TupleNoneCompare(vals)

        return helper

    def _material_all(self, type_, symbolic_type, symbolic_lookup=None):
        material_res = []
        symbolic_res = {}
        res = {}

        try:
            if symbolic_lookup:
                doc = self._name_or_id(symbolic_lookup)
                symbolic_res = self._get(symbolic_type, doc)
                raw_res = self._get_many(type_, {"type_list": symbolic_res["_id"]})
            else:
                raw_res = self._get_many(type_)
                symbolic_ids = list({doc["type"] for doc in raw_res})
                symbolic_res = self._get_many(
                    symbolic_type, {"_id": {"$in": symbolic_ids}}
                )
        except NoDocumentFound:
            pass
        else:
            symbolic_res = self._to_id_dic(symbolic_res)
            raw_res.sort(key=self._material_sort_key(symbolic_res))
            for raw in raw_res:
                raw_type = raw["type"]
                symbolic_cur = symbolic_res[raw_type]
                decoded = self._material_decode(raw, symbolic_cur)
                material_res.append(decoded)

        res[symbolic_type] = symbolic_res
        res[type_] = material_res
        return res

    def _material_get(self, type_, symbolic_type, _id):
        material_res = {}
        symbolic_res = {}
        res = {}

        try:
            if not self.suid.validate(_id):
                raise InvalidSuidError(f'"{_id}" is an invalid suid')
            raw_res = self._get(type_, {"_id": _id})
        except NoDocumentFound:
            pass
        except InvalidSuidError as e:
            res["error"] = str(e)
            res["lookup"] = _id
        else:
            symbolic_res = self._get(symbolic_type, raw_res["type"])
            material_res = self._material_decode(raw_res, symbolic_res)
            symbolic_res = self._to_id_dic(symbolic_res)

        res[type_] = material_res
        res[symbolic_type] = symbolic_res
        return res

    def _material_create(self, type_, json_list):
        created = []
        errors = []

        for json in self._to_list(json_list):
            try:
                symbolic_doc = self._name_or_id(json.get("type", ""))
                template = self._get(
                    "asset" if type_ == "thing" else "combo",
                    symbolic_doc,
                )
            except (InvalidSymbolicError, PyMongoError) as e:
                errors.append(self._error_json(e, json))
            else:
                current = {}
                current["_id"] = json.get("_id") or self.suid.generate()
                current["type"] = template["_id"]
                current["type_list"] = template["type_list"]
                current["fields"] = self._verify(json["fields"], template, type_)
                res = self._insert(type_, current)
                created.append(res.inserted_id)

        return {"created": created, "errored": errors}

    def _material_update(self, type_, json_list):
        updated = 0
        errors = []

        for json in self._to_list(json_list):
            _id = json["_id"]
            if not self.suid.validate(_id):
                errors.append(
                    self._error_json(
                        f'"{_id}" is an invalid suid.',
                        json,
                        lookup=_id,
                    )
                )
                continue
            try:
                symbolic_doc = self._name_or_id(json.get("type", ""))
                template = self._get(
                    "asset" if type_ == "thing" else "combo",
                    symbolic_doc,
                )
            except (InvalidSymbolicError, NoDocumentFound) as e:
                errors.append(self._error_json(e, json))
            else:
                unset = {}
                update = {}
                if "unset" in json:
                    unset["fields"] = json["unset"]
                if "fields" in json:
                    update["fields"] = self._verify(
                        json["fields"],
                        template,
                        _id,
                        unset,
                    )
                if unset or update:
                    res = self._update(
                        type_,
                        {"_id": _id},
                        {"update": update, "unset": unset},
                    )
                    if not res.modified_count:
                        errors.append(
                            self._error_json(
                                f'"{_id}" does not match any documents of type "{type_}" to update',
                                json,
                                lookup=_id,
                            )
                        )
                    else:
                        updated += res.matched_count

        return {"updated": updated, "errored": errors}

    def _material_delete(self, type_, json_list):
        deleted = 0
        errors = []

        for _id in self._to_list(json_list):
            if not self.suid.validate(_id):
                errors.append(
                    self._error_json(
                        f'"{_id}" is an invalid suid.',
                        {},
                        lookup=_id,
                    )
                )
            else:
                res = self._delete(type_, {"_id": _id})
                if not res.deleted_count:
                    errors.append(
                        self._error_json(
                            f'"{_id}" does not match any documents to delete',
                            {},
                            lookup=_id,
                        )
                    )
                else:
                    deleted += res.deleted_count

        return {"deleted": deleted, "errored": errors}

    def _document_retrieve(self, gridfs, name):
        _id, _ = splitext(name)
        if self.suid.validate(_id):
            # https://stackoverflow.com/a/58382158
            try:
                fileobj = gridfs.get(file_id=_id)
            except NoFile:  # 404
                return None
            else:
                data = wrap_file(request.environ, fileobj, buffer_size=1024 * 255)
                response = current_app.response_class(
                    data,
                    mimetype=fileobj.content_type,
                    direct_passthrough=True,
                )
                response.content_length = fileobj.length
                response.last_modified = fileobj.upload_date
                response.set_etag(fileobj.md5)
                response.cache_control.max_age = 10
                response.cache_control.public = True
                response.make_conditional(request)
                return response
        return None

    def _document_get(self, gridfs, name):
        res = {}
        try:
            _id, _ = splitext(name)
            if not self.suid.validate(_id):
                raise InvalidSuidError(f'"{_id}" is an invalid suid')
            gridfs_res = gridfs.get(file_id=_id)
            res = {
                "content_type": gridfs_res.content_type,
                "filename": gridfs_res.filename,
                "size": gridfs_res.length,
                "md5": gridfs_res.md5,
                "metadata": gridfs_res.metadata,
                "upload_date": gridfs_res.upload_date,
            }
        except NoFile:
            res["error"] = f'"{_id}" does not match any documents to delete'
            res["lookup"] = _id
        except (InvalidSuidError, PyMongoError) as e:
            res["error"] = str(e)
            res["lookup"] = _id
        return res

    def _document_create(self, gridfs, files):
        created = []
        errors = []

        for file_ in files:
            _id = self.suid.generate()
            metadata = {"display": file_.filename, "thing": [], "group": []}
            try:
                gridfs_res = gridfs.put(
                    _id=_id,
                    data=file_,
                    filename=file_.filename,
                    metadata=metadata,
                    content_type=file_.mimetype,
                )
            except (InvalidSymbolicError, PyMongoError) as e:
                errors.append(self._error_json(e, str(file_)))
            else:
                created.append(gridfs_res)

        return {"created": created, "errored": errors}

    def _document_delete(self, gridfs, json_list):
        deleted = 0
        errors = []

        for _id in self._to_list(json_list):
            if self.suid.validate(_id):
                _ = gridfs.delete(file_id=_id)
                deleted += 1
            else:
                errors.append({"error": f'"{_id}" is not a valid suid', "lookup": _id})

        return {"deleted": deleted, "errored": errors}

    def asset_all(self):
        """Get all assets"""
        return self._symbolic_all("asset")

    def asset_get(self, value):
        """Get all things for asset"""
        return self._symbolic_get("asset", value)

    def asset_create(self, json_list):
        """Create new asset"""
        return self._symbolic_create("asset", json_list)

    def asset_update(self, json_list):
        """Update asset"""
        return self._symbolic_update("asset", json_list)

    def asset_delete(self, json_list):
        """Delete asset"""
        return self._symbolic_delete("asset", json_list)

    def thing_all(self, asset=None):
        """Get all things"""
        return self._material_all("thing", "asset", asset)

    def thing_get(self, _id):
        """Get specific thing"""
        return self._material_get("thing", "asset", _id)

    def thing_create(self, json_list):
        """Create thing"""
        return self._material_create("thing", json_list)

    def thing_update(self, json_list):
        """Update thing"""
        return self._material_update("thing", json_list)

    def thing_delete(self, json_list):
        """Delete thing"""
        return self._material_delete("thing", json_list)

    def combo_all(self):
        """Get all combos"""
        return self._symbolic_all("combo")

    def combo_get(self, value):
        """Get all groups for combo"""
        return self._symbolic_get("combo", value)

    def combo_create(self, json_list):
        """Create new combo"""
        return self._symbolic_create("combo", json_list)

    def combo_update(self, json_list):
        """Update combo"""
        return self._symbolic_update("combo", json_list)

    def combo_delete(self, json_list):
        """Delete combo"""
        return self._symbolic_delete("combo", json_list)

    def group_all(self, combo=None):
        """Get all groups"""
        return self._material_all("group", "combo", combo)

    def group_get(self, _id):
        """Get group"""
        return self._material_get("group", "combo", _id)

    def group_create(self, json_list):
        """Create new group"""
        return self._material_create("group", json_list)

    def group_update(self, json_list):
        """Update group"""
        return self._material_update("group", json_list)

    def group_delete(self, json_list):
        """Delete group"""
        return self._material_delete("group", json_list)

    def image_get(self, _id):
        """Get imgae"""
        return self._document_retrieve(self.image, _id)

    def image_get_info(self, _id):
        """Get info on image"""
        return self._document_get(self.image, _id)

    def image_create(self, files):
        """Create new image"""
        return self._document_create(self.image, files)

    def image_update(self, json_list):
        """Update image"""
        return self._material_update("image.files", json_list)

    def image_delete(self, json_list):
        """Delete image"""
        return self._document_delete(self.image, json_list)

    def extra_get(self, _id):
        """Get extra"""
        return self._document_retrieve(self.extra, _id)

    def extra_get_info(self, _id):
        """Get info on extra"""
        return self._document_get(self.extra, _id)

    def extra_create(self, files):
        """create extra"""
        return self._document_create(self.extra, files)

    def extra_update(self, json_list):
        """Update extra"""
        return self._material_update("extra.files", json_list)

    def extra_delete(self, json_list):
        """Delete extra"""
        return self._document_delete(self.extra, json_list)

    def download(self):
        """Download database as json"""
        return {
            "asset": self.asset_all(),
            "thing": self.thing_all()["thing"],
            "combo": self.combo_all(),
            "group": self.group_all()["group"],
        }

    @staticmethod
    def _order_symbolic_inheritance(symbolic, type_):
        ordered = []
        for idx, value in enumerate(symbolic):
            if value.get("name") == type_:
                ordered.append(value)
                del symbolic[idx]
                break

        for value in ordered:
            matches = [cur for cur in symbolic if value["_id"] == cur.get("inherit")]
            ordered.extend(matches)
            symbolic[:] = [
                cur for cur in symbolic if value["_id"] != cur.get("inherit")
            ]
        return ordered

    def upload(self, newdata):
        """Upload json as new database info"""
        old = self.download()
        create = {}
        if "asset" in newdata:
            new_asset = self._order_symbolic_inheritance(newdata["asset"], "Asset")
            self.database.drop_collection("asset")
            create["asset"] = self._insert_many("asset", new_asset).inserted_ids

        if "combo" in newdata:
            new_combo = self._order_symbolic_inheritance(newdata["combo"], "Combo")
            self.database.drop_collection("combo")
            create["combo"] = self._insert_many("combo", new_combo).inserted_ids

        if "thing" in newdata:
            new_thing = newdata["thing"]
            self.database.drop_collection("thing")
            create["thing"] = self._material_create("thing", new_thing)

        if "group" in newdata:
            new_group = newdata["group"]
            self.database.drop_collection("group")
            create["group"] = self._material_create("group", new_group)
        new = self.download()

        return {
            "old": old,
            "new": new,
            "create": create,
        }

    def _updates(self):
        return {}
