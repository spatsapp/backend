"""Interface for mongo db"""
from collections.abc import MutableMapping

from flask_pymongo import PyMongo


class Error(Exception):
    """Base class for module exceptions"""

    def __init__(self, message):
        super().__init__()
        self.message = message


class NoDocumentFound(Error):
    """No documents exist for requested type"""


class MongoInterface:
    def __init__(self, app):
        self.mongo = PyMongo()
        self.mongo.init_app(app)
        self.database = self.mongo.db

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

    def paginate(self, collection, page, limit=10):
        cursor = self.database[collection].find({})
        count = cursor.count()
        last = int(count / limit)
        return {
            "page": page,
            "count": count,
            "last": last,
            "range": (-1, float("inf")),
        }

    def get(self, collection, filter_, error=True):
        doc = self.database[collection].find_one(filter_)
        if doc is None and error:
            raise NoDocumentFound(
                f'No document in collection "{collection}" matches filter: {filter_}'
            )
        return doc

    def get_many(self, collection, filter_=None, error=True, page=None):
        limit = 10
        filter_ = filter_ or {}
        cursor = self.database[collection].find(filter_)
        ret = {}
        if page is not None:
            ret["count"] = cursor.count()
            ret["range"] = (page * limit, (page * limit) + limit)
            ret["last"] = int(ret["count"] / limit)
            ret["docs"] = list(cursor.skip(page * limit).limit(limit))
        else:
            ret["docs"] = list(cursor)

        if len(ret["docs"]) == 0 and error:
            raise NoDocumentFound(
                f'No documents in collection "{collection}" matches filter: {filter_}'
            )

        return ret

    # pylint: disable=dangerous-default-value
    def search(self, collection, filter_=None):
        filter_ = filter_ or {}
        return self.database[collection].find(filter_)

    def insert(self, collection, document):
        return self.database[collection].insert_one(document)

    def insert_many(self, collection, documents):
        return self.database[collection].insert_many(documents)

    def update(
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

    def update_many(self, collection, filter_, update):
        flat_update = self._flatten(update)
        return self.database[collection].update_many(
            filter_,
            {"$set": flat_update},
            upsert=False,
        )

    def delete(self, collection, filter_):
        return self.database[collection].delete_one(filter_)

    def delete_many(self, collection, filter_):
        return self.database[collection].delete_many(filter_)
