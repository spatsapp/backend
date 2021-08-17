"""Interface for mongo database"""
from os.path import splitext

from flask import current_app, request
from gridfs import GridFS, NoFile
from pymongo.errors import PyMongoError, OperationFailure
from werkzeug.wsgi import wrap_file

from . import dbinit
from .field_parser import FieldParser
from .mongointerface import MongoInterface, NoDocumentFound
from .suid import Suid
from .support import TupleNoneCompare, from_keys, json2list, jsonerror, list2dict


class Error(Exception):
    """Base class for module exceptions"""

    def __init__(self, message):
        super().__init__()
        self.message = message


class RequiredAttributeError(Error):
    """Required field not given"""


class UniqueAttributeError(Error):
    """Unique filed not unique"""


class InvalidSuidError(Error):
    """Suid is invalid"""


class InvalidSymbolicError(Error):
    """Symbolic id or name is invlaid"""


class Database:
    """API interface for a Mongo database"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initalize the app"""
        self.app = app
        self.database = MongoInterface(app)
        self.image = GridFS(self.database.database, "image")
        self.extra = GridFS(self.database.database, "extra")

        self.suid = Suid()
        self.field_parser = FieldParser()

        self._init_database()

    def _init_database(self):
        try:
            self.database.get("asset", {"name": "Asset"})
        except NoDocumentFound:
            _id = self.suid.generate()
            self.database.insert("asset", dbinit.asset(_id))

        try:
            self.database.get("combo", {"name": "Combo"})
        except NoDocumentFound:
            _id = self.suid.generate()
            self.database.insert("combo", dbinit.combo(_id))

        self._create_index()

    def _create_index(self):
        self.database.database["asset"].create_index([("$**", "text")])
        self.database.database["combo"].create_index([("$**", "text")])
        self.database.database["thing"].create_index([("$**", "text")])
        self.database.database["group"].create_index([("$**", "text")])

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
            existing_doc = self.database.get(
                type_,
                {"type_list": origin, f"fields.{name}": value},
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
                    field_type,
                    json[name]["value"],
                    params,
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

    def symbolic_all(self, type_):
        """Get all entries of a given symbolic type"""
        try:
            docs = self.database.get_many(type_)["docs"]
        except NoDocumentFound:
            docs = []
        return sorted(docs, key=lambda doc: doc.get("name"))

    def symbolic_get(self, type_, value):
        """Get entry that matches value for given type"""
        res = {}
        try:
            doc = self._name_or_id(value)
            res[type_] = self.database.get(type_, doc)
        except NoDocumentFound:
            pass
        except InvalidSymbolicError as e:
            res["error"] = str(e)
            res["lookup"] = value
        return res

    def _symbolic_lookup(self, type_, value):
        try:
            doc = self._name_or_id(value)
            symbolic = self.database.get(type_, doc)
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

    def symbolic_create(self, type_, json_list, ignore=False):
        """Create new instance of symbolic type"""
        created = []
        errors = []
        merged = False

        for json in json2list(json_list):
            json["_id"] = json.get("_id") or self.suid.generate()
            inherit = json.get("inherit")
            try:
                self._symbolic_name_check(type_, f'_{json.get("name")}')
                if inherit is None and json.get("name", "").lower() == type_:
                    symbolic = {}
                else:
                    symbolic = self._symbolic_lookup(type_, inherit)
            except (InvalidSymbolicError, PyMongoError) as e:
                errors.append(jsonerror(e, json))
            else:
                json = self._merge_docs(symbolic, json)
                json["type_list"] = symbolic.get("type_list", []) + [json["_id"]]
                merged = True
            finally:
                if ignore or merged:
                    res = self.database.insert(type_, json)
                    created.append(res.inserted_id)

        return {"created": created, "errored": errors}

    # pylint: disable=too-many-locals
    def symbolic_update(self, type_, json_list):
        """Update values for symbolic type"""
        updated = 0
        errors = []

        for json in json2list(json_list):
            _id = json["_id"]
            update = json.get("update", {})
            if not self.suid.validate(_id):
                errors.append(
                    jsonerror(
                        f'"{_id}" is an invalid suid.',
                        json,
                        lookup=_id,
                    )
                )
                continue
            if "fields" in update:
                to_update = self.database.get(type_, {"_id": _id})
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
            res = self.database.update(type_, {"_id": _id}, json)
            if not res.matched_count:
                errors.append(
                    jsonerror(
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
                    for child in self.database.get_many(type_, {"type_list": _id})[
                        "docs"
                    ]
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
                        child_res = self.database.update(
                            type_, {"_id": child["_id"]}, document
                        )
                        updated += child_res.matched_count

        return {"updated": updated, "errored": errors}

    def symbolic_delete(self, type_, json_list):
        """Delete symbolic type"""
        deleted = 0
        errors = []

        for _id in json2list(json_list):
            if not self.suid.validate(_id):
                errors.append(
                    {"message": f'"{_id}" is an invalid suid.', "lookup": _id}
                )
            res = self.database.delete(type_, {"_id": _id})
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
                field_type,
                value,
                field_params,
            )
        return res

    def _material_sort_key(self, symbolic_res):
        def helper(doc):
            symbolic = from_keys(symbolic_res, doc["type_list"])
            primary_key = symbolic.get("primary")
            secondary_key = symbolic.get("secondary")
            tertiary_keys = symbolic.get("tertiary", [])
            fields = doc["fields"]
            vals = [fields.get(primary_key), fields.get(secondary_key)]
            if tertiary_keys:
                vals.extend([fields.get(key) for key in tertiary_keys])
            return TupleNoneCompare(vals)

        return helper

    def material_all(self, type_, symbolic_type, symbolic_lookup=None, page=None):
        """Get all instances of material type"""
        material_res = []
        symbolic_res = {}
        res = {}

        try:
            if symbolic_lookup:
                doc = self._name_or_id(symbolic_lookup)
                symbolic_res = self.database.get(symbolic_type, doc)
                raw_res = self.database.get_many(
                    type_, {"type_list": symbolic_res["_id"]}, page=page
                )
            else:
                raw_res = self.database.get_many(type_, page=page)
            symbolic_ids = list({doc["type"] for doc in raw_res["docs"]})
            symbolic_res = self.database.get_many(
                symbolic_type,
                {"_id": {"$in": symbolic_ids}},
            )["docs"]
        except NoDocumentFound:
            res["paginate"] = self.database.paginate(type_, page)
        else:
            symbolic_res = list2dict("_id", symbolic_res)
            raw_res["docs"].sort(key=self._material_sort_key(symbolic_res))
            for raw in raw_res["docs"]:
                raw_type = raw["type"]
                symbolic_cur = symbolic_res[raw_type]
                decoded = self._material_decode(raw, symbolic_cur)
                material_res.append(decoded)

            if raw_res.get("count") and raw_res.get("range"):
                res["paginate"] = {
                    "page": page,
                    "count": raw_res["count"],
                    "range": raw_res["range"],
                    "last": raw_res["last"],
                }

        res[symbolic_type] = symbolic_res
        res[type_] = material_res
        return res

    def material_get(self, type_, symbolic_type, _id):
        """Get instance of material type matching id"""
        material_res = {}
        symbolic_res = {}
        res = {}

        try:
            if not self.suid.validate(_id):
                raise InvalidSuidError(f'"{_id}" is an invalid suid')
            raw_res = self.database.get(type_, {"_id": _id})
        except NoDocumentFound:
            pass
        except InvalidSuidError as e:
            res["error"] = str(e)
            res["lookup"] = _id
        else:
            symbolic_res = self.database.get(symbolic_type, raw_res["type"])
            material_res = self._material_decode(raw_res, symbolic_res)
            symbolic_res = list2dict("_id", symbolic_res)

        res[type_] = material_res
        res[symbolic_type] = symbolic_res
        return res

    def material_create(self, type_, json_list):
        """Create new material instance"""
        created = []
        errors = []

        for json in json2list(json_list):
            try:
                symbolic_doc = self._name_or_id(json.get("type", ""))
                template = self.database.get(
                    "asset" if type_ == "thing" else "combo",
                    symbolic_doc,
                )
            except (InvalidSymbolicError, PyMongoError) as e:
                errors.append(jsonerror(e, json))
            else:
                current = {}
                current["_id"] = json.get("_id") or self.suid.generate()
                current["type"] = template["_id"]
                current["type_list"] = template["type_list"]
                current["fields"] = self._verify(json["fields"], template, type_)
                res = self.database.insert(type_, current)
                created.append(res.inserted_id)

        return {"created": created, "errored": errors}

    def material_update(self, type_, json_list):
        """Update existing materials"""
        updated = 0
        errors = []

        for json in json2list(json_list):
            _id = json["_id"]
            if not self.suid.validate(_id):
                errors.append(
                    jsonerror(
                        f'"{_id}" is an invalid suid.',
                        json,
                        lookup=_id,
                    )
                )
                continue
            try:
                symbolic_doc = self._name_or_id(json.get("type", ""))
                template = self.database.get(
                    "asset" if type_ == "thing" else "combo",
                    symbolic_doc,
                )
            except (InvalidSymbolicError, NoDocumentFound) as e:
                errors.append(jsonerror(e, json))
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
                    res = self.database.update(
                        type_,
                        {"_id": _id},
                        {"update": update, "unset": unset},
                    )
                    if not res.modified_count:
                        errors.append(
                            jsonerror(
                                f'"{_id}" does not match any documents of type "{type_}" to update',
                                json,
                                lookup=_id,
                            )
                        )
                    else:
                        updated += res.matched_count

        return {"updated": updated, "errored": errors}

    def material_delete(self, type_, json_list):
        """Delete material instances"""
        deleted = 0
        errors = []

        for _id in json2list(json_list):
            if not self.suid.validate(_id):
                errors.append(
                    jsonerror(
                        f'"{_id}" is an invalid suid.',
                        {},
                        lookup=_id,
                    )
                )
            else:
                res = self.database.delete(type_, {"_id": _id})
                if not res.deleted_count:
                    errors.append(
                        jsonerror(
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
                errors.append(jsonerror(e, str(file_)))
            else:
                created.append(gridfs_res)

        return {"created": created, "errored": errors}

    def _document_delete(self, gridfs, json_list):
        deleted = 0
        errors = []

        for _id in json2list(json_list):
            if self.suid.validate(_id):
                _ = gridfs.delete(file_id=_id)
                deleted += 1
            else:
                errors.append({"error": f'"{_id}" is not a valid suid', "lookup": _id})

        return {"deleted": deleted, "errored": errors}

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
        return self.material_update("image.files", json_list)

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
        return self.material_update("extra.files", json_list)

    def extra_delete(self, json_list):
        """Delete extra"""
        return self._document_delete(self.extra, json_list)

    def _search_symbolic(self, material, symbolic, document):
        symbolic_res = self.database.get(symbolic, document["type"])
        material_res = self._material_decode(document, symbolic_res)
        symbolic_res = list2dict("_id", symbolic_res)
        return {material: material_res, symbolic: symbolic_res}

    def search(self, json):
        """Search for value in entries"""
        asset = []
        combo = []
        thing = []
        group = []
        collections = json["collection"].split()

        try:
            if "asset" in collections:
                asset = self.database.search("asset", json["search"])
            if "combo" in collections:
                combo = self.database.search("combo", json["search"])
            if "thing" in collections:
                thing = self.database.search("thing", json["search"])
            if "group" in collections:
                group = self.database.search("group", json["search"])
        except OperationFailure:
            self._create_index()
            if "asset" in collections:
                asset = self.database.search("asset", json["search"])
            if "combo" in collections:
                combo = self.database.search("combo", json["search"])
            if "thing" in collections:
                thing = self.database.search("thing", json["search"])
            if "group" in collections:
                group = self.database.search("group", json["search"])

        thing = [self._search_symbolic("thing", "asset", t) for t in thing]
        group = [self._search_symbolic("group", "combo", g) for g in group]

        return {
            "asset": asset,
            "combo": combo,
            "thing": thing,
            "group": group,
        }

    def download(self):
        """Download database as json"""
        return {
            "asset": self.database.get_many("asset", error=False)["docs"],
            "thing": self.database.get_many("thing", error=False)["docs"],
            "combo": self.database.get_many("combo", error=False)["docs"],
            "group": self.database.get_many("group", error=False)["docs"],
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
        if newdata.get("asset"):
            new_asset = self._order_symbolic_inheritance(newdata["asset"], "Asset")
            self.database.database.drop_collection("asset")
            inserted = self.database.insert_many("asset", new_asset).inserted_ids
            create["asset"] = {
                "created": inserted,
                "errored": [
                    asset["_id"] for asset in new_asset if asset["_id"] not in inserted
                ],
            }
        if newdata.get("combo"):
            new_combo = self._order_symbolic_inheritance(newdata["combo"], "Combo")
            self.database.database.drop_collection("combo")
            inserted = self.database.insert_many("combo", new_combo).inserted_ids
            create["combo"] = {
                "created": inserted,
                "errored": [
                    combo["_id"] for combo in new_combo if combo["_id"] not in inserted
                ],
            }
        if newdata.get("thing"):
            self.database.database.drop_collection("thing")
            inserted = self.database.insert_many("thing", newdata["thing"]).inserted_ids
            create["thing"] = {
                "created": inserted,
                "errored": [
                    thing["_id"]
                    for thing in newdata["thing"]
                    if thing["_id"] not in inserted
                ],
            }
        if newdata.get("group"):
            self.database.database.drop_collection("group")
            inserted = self.database.insert_many("group", newdata["group"]).inserted_ids
            create["group"] = {
                "created": inserted,
                "errored": [
                    group["_id"]
                    for group in newdata["group"]
                    if group["_id"] not in inserted
                ],
            }
        new = self.download()

        return {
            "old": old,
            "new": new,
            "create": create,
        }

    def _updates(self):
        return {}
