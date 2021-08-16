"""Flask API Backend for SPATS"""

import dotenv
from flask import Flask, jsonify, redirect, request
from flask_pymongo import PyMongo

# from flask_wtf.csrf import CSRFProtect
from werkzeug.routing import BaseConverter, ValidationError

from .database import Database


class OptionConverter(BaseConverter):
    """URL converter that only allows things in the list"""

    def __init__(self, url_map, *args):
        super().__init__(url_map)
        self.options = set(args)

    def to_python(self, value):
        if value not in self.options:
            raise ValidationError()
        return value

    def to_url(self, value):
        return value


def _symbolic_type(material):
    return "asset" if material == "thing" else "combo"


app = Flask(__name__)
app.config.from_pyfile("backend.cfg")
app.url_map.converters["option"] = OptionConverter

db = Database()
db.init_app(app)

# csrf = CSRFProtect()
# csrf.init_app(app)


@app.before_request
def clear_trailing():
    """Cleans up requests by removing any trailing slashes"""
    path = request.path
    if path != "/" and path.endswith("/"):
        return redirect(path[:-1])
    return None


# <option('thing', 'group'):material>
# <option('asset', 'combo'):symbolic>


@app.route("/search", methods=["POST"])
def search_docs():
    """Search for docs"""
    json = request.get_json(force=True)
    res = db.search(json)
    return jsonify(res)


@app.route("/<option('asset', 'combo'):symbolic>/all", methods=["GET"])
def symbolic_all(symbolic):
    """List all asset types"""
    docs = db.symbolic_all(symbolic)
    return jsonify(docs)


@app.route("/<option('asset', 'combo'):symbolic>/<string:_id>", methods=["GET"])
def symbolic_get(symbolic, _id):
    """Get specific info for asset"""
    doc = db.symbolic_get(symbolic, _id)
    return jsonify(doc)


@app.route("/<option('asset', 'combo'):symbolic>/create", methods=["POST"])
def symbolic_create(symbolic):
    """Create new asset"""
    json = request.get_json(force=True)
    res = db.symbolic_create(symbolic, json)
    return jsonify(res)


@app.route("/<option('asset', 'combo'):symbolic>/update", methods=["PUT"])
def symbolic_update(symbolic):
    """Update asset"""
    json = request.get_json(force=True)
    res = db.symbolic_update(symbolic, json)
    return jsonify(res)


@app.route("/<option('asset', 'combo'):symbolic>/delete", methods=["DELETE"])
def symbolic_delete(symbolic):
    """Delete asset type"""
    json = request.get_json(force=True)
    res = db.symbolic_delete(symbolic, json)
    return jsonify(res)


@app.route("/<option('thing', 'group'):material>/all", methods=["GET"])
def material_all(material):
    """List all things"""
    docs = db.material_all(material, _symbolic_type(material))
    return jsonify(docs)


@app.route("/<option('thing', 'group'):material>/all/<int:page>", methods=["GET"])
def material_all_page(material, page):
    """List all things"""
    docs = db.material_all(material, _symbolic_type(material), page=page)
    return jsonify(docs)


@app.route(
    "/<option('thing', 'group'):material>/<option('asset', 'combo'):symbolic>/<string:_id>",
    methods=["GET"],
)
def material_symbolic(material, symbolic, _id):
    """Get all things for specific asset type"""
    docs = db.material_all(material, symbolic, _id)
    return jsonify(docs)


@app.route(
    (
        "/<option('thing', 'group'):material>"
        "/<option('asset', 'combo'):symbolic>"
        "/<string:_id>/<int:page>"
    ),
    methods=["GET"],
)
def material_symbolic_page(material, symbolic, _id, page):
    """Get all things for specific asset type"""
    docs = db.material_all(material, symbolic, _id, page=page)
    return jsonify(docs)


@app.route("/<option('thing', 'group'):material>/<string:_id>", methods=["GET"])
def material_get(material, _id):
    """Get info for specific thing"""
    doc = db.material_get(material, _symbolic_type(material), _id)
    return jsonify(doc)


@app.route("/<option('thing', 'group'):material>/create", methods=["POST"])
def material_create(material):
    """Create new thing"""
    json = request.get_json(force=True)
    res = db.material_create(material, json)
    return jsonify(res)


@app.route("/<option('thing', 'group'):material>/update", methods=["PUT"])
def material_update(material):
    """Update thing"""
    json = request.get_json(force=True)
    res = db.material_update(material, json)
    return jsonify(res)


@app.route("/<option('thing', 'group'):material>/delete", methods=["DELETE"])
def material_delete(material):
    """Delete thing"""
    json = request.get_json(force=True)
    res = db.material_delete(material, json)
    return jsonify(res)


@app.route("/image/<string:_id>", methods=["GET"])
def image_get(_id):
    """Get specific image"""
    res = db.image_get(_id)
    return jsonify(res)


@app.route("/image/<string:_id>/info", methods=["GET"])
def image_get_info(_id):
    """Get info on image"""
    res = db.image_get_info(_id)
    return jsonify(res)


@app.route("/image/create", methods=["POST"])
def image_create():
    """Create new image"""
    files = request.files.getlist("files")
    res = db.image_create(files)
    return jsonify(res)


@app.route("/image/update", methods=["PUT"])
def image_update():
    """Update image"""
    json = request.get_json(force=True)
    res = db.image_update(json)
    return jsonify(res)


@app.route("/image/delete", methods=["DELETE"])
def image_delete():
    """Delete image"""
    json = request.get_json(force=True)
    res = db.image_delete(json)
    return jsonify(res)


@app.route("/extra/<string:_id>", methods=["GET"])
def extra_get(_id):
    """Get extra"""
    res = db.extra_get(_id)
    return jsonify(res)


@app.route("/extra/<string:_id>/info", methods=["GET"])
def extra_get_info(_id):
    """Get info about extra"""
    res = db.extra_get_info(_id)
    return jsonify(res)


@app.route("/extra/create", methods=["POST"])
def extra_create():
    """Create extra"""
    files = request.files.getlist("files")
    res = db.extra_create(files)
    return jsonify(res)


@app.route("/extra/update", methods=["PUT"])
def extra_update():
    """Update extra"""
    json = request.get_json(force=True)
    res = db.extra_update(json)
    return jsonify(res)


@app.route("/extra/delete", methods=["DELETE"])
def extra_delete():
    """Delete extra"""
    json = request.get_json(force=True)
    res = db.extra_delete(json)
    return jsonify(res)


@app.route("/download", methods=["GET"])
def download():
    """Downlaod database as a json"""
    res = db.download()
    return jsonify(res)


@app.route("/upload", methods=["POST"])
def upload():
    """Upload json to load data into database"""
    json = request.get_json(force=True)
    res = db.upload(json)
    return jsonify(res)


@app.route("/updates", methods=["GET"])
def updates():
    """Upload json to load data into database"""
    # pylint: disable=protected-access
    return jsonify(db._updates())


if __name__ == "__main__":
    app.run()
