"""Flask API Backend for SPATS"""

import dotenv
from flask import Flask, jsonify, redirect, request
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect

from .database import Database

app = Flask(__name__)
app.config.from_pyfile("backend.cfg")

db = Database()
db.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)


@app.before_request
def clear_trailing():
    """Cleans up requests by removing any trailing slashes"""
    path = request.path
    if path != "/" and path.endswith("/"):
        return redirect(path[:-1])
    return None


@app.route("/", methods=["GET"])
@csrf.exempt
def query_api():
    """Landing page, just returns a dict of possible endpoints"""
    return jsonify(
        {
            "version": 0.1,
            "endpoints": [
                {
                    "uri": "/",
                    "methods": ["GET"],
                    "description": "Get information on the api.",
                },
                {
                    "uri": "/asset/all",
                    "methods": ["GET"],
                    "description": "Retrieve a list of all asset types.",
                },
                {
                    "uri": "/asset/{_id}",
                    "methods": ["GET"],
                    "description": "Get info on asset with id {_id}",
                },
                {
                    "url": "/asset/create",
                    "methods": ["POST"],
                    "description": "Create new asset",
                },
                {
                    "url": "/asset/update",
                    "methods": ["PUT"],
                    "description": "Update existing asset",
                },
                {
                    "url": "/asset/delete",
                    "methods": ["DELETE"],
                    "description": "Delete asset",
                },
                {
                    "uri": "/thing/all",
                    "methods": ["GET"],
                    "description": "Get all things",
                },
                {
                    "uri": "/thing/asset/{_id}",
                    "methods": ["GET"],
                    "description": "Get all things belonging to asset with id {_id}",
                },
                {
                    "uri": "/thing/{_id}",
                    "methods": ["GET"],
                    "description": "Get thing with id {_id}",
                },
                {
                    "uri": "/thing/create",
                    "methods": ["POST"],
                    "description": "Create new thing",
                },
                {
                    "uri": "/thing/update",
                    "methods": ["PUT"],
                    "description": "Update existing thing",
                },
                {
                    "uri": "/thing/delete",
                    "methods": ["DELETE"],
                    "description": "Delete thing",
                },
                {
                    "uri": "/combo/all",
                    "methods": ["GET"],
                    "description": "Get all combos",
                },
                {
                    "uri": "/combo/{_id}",
                    "methods": ["GET"],
                    "description": "Get combo with id {_id}",
                },
                {
                    "uri": "/combo/create",
                    "methods": ["POST"],
                    "description": "Create new combo",
                },
                {
                    "uri": "/combo/update",
                    "methods": ["PUT"],
                    "description": "Update existing combo",
                },
                {
                    "uri": "/combo/delete",
                    "methods": ["DELETE"],
                    "description": "Delete combo",
                },
                {
                    "uri": "/group/all",
                    "methods": ["GET"],
                    "description": "Get all groups",
                },
                {
                    "uri": "/group/combo/{_id}",
                    "methods": ["GET"],
                    "description": "Get all groups of combo with id {_id}",
                },
                {
                    "uri": "/group/{_id}",
                    "methods": ["GET"],
                    "description": "Get group with id {_id}",
                },
                {
                    "uri": "/group/create",
                    "methods": ["POST"],
                    "description": "Create new group",
                },
                {
                    "uri": "/group/update",
                    "methods": ["PUT"],
                    "description": "Update existing group",
                },
                {
                    "uri": "/group/delete",
                    "methods": ["DELETE"],
                    "description": "Delete group",
                },
                {
                    "uri": "/image/{_id}",
                    "methods": ["GET"],
                    "description": "Get image with id {_id}",
                },
                {
                    "uri": "/image/{_id}/info",
                    "methods": ["GET"],
                    "description": "Get info about image with id {_id}",
                },
                {
                    "uri": "/image/create",
                    "methods": ["POST"],
                    "description": "Create image",
                },
                {
                    "uri": "/image/update",
                    "methods": ["PUT"],
                    "description": "Update image",
                },
                {
                    "uri": "/image/delete",
                    "methods": ["DELETE"],
                    "description": "Delete image",
                },
                {
                    "uri": "/extra/{_id}",
                    "methods": ["GET"],
                    "description": "Get extra file with id {_id}",
                },
                {
                    "uri": "/extra/{_id}/info",
                    "methods": ["GET"],
                    "description": "Get info about extra file with id {_id}",
                },
                {
                    "uri": "/extra/create",
                    "methods": ["POST"],
                    "description": "Create extra file",
                },
                {
                    "uri": "/extra/update",
                    "methods": ["PUT"],
                    "description": "Update extra file",
                },
                {
                    "uri": "/extra/delete",
                    "methods": ["DELETE"],
                    "description": "Delete extra file",
                },
            ],
        }
    )


@app.route("/asset/all", methods=["GET"])
@csrf.exempt
def asset_all():
    """List all asset types"""
    docs = db.asset_all()
    return jsonify(docs)


@app.route("/asset/<string:_id>", methods=["GET"])
@csrf.exempt
def asset_get(_id):
    """Get specific info for asset"""
    doc = db.asset_get(_id)
    return jsonify(doc)


@app.route("/asset/create", methods=["POST"])
@csrf.exempt
def asset_create():
    """Create new asset"""
    json = request.get_json(force=True)
    res = db.asset_create(json)
    return jsonify(res)


@app.route("/asset/update", methods=["PUT"])
@csrf.exempt
def asset_update():
    """Update asset"""
    json = request.get_json(force=True)
    res = db.asset_update(json)
    return jsonify(res)


@app.route("/asset/delete", methods=["DELETE"])
@csrf.exempt
def asset_delete():
    """Delete asset type"""
    json = request.get_json(force=True)
    res = db.asset_delete(json)
    return jsonify(res)


@app.route("/thing/all", methods=["GET"])
@csrf.exempt
def thing_all():
    """List all things"""
    docs = db.thing_all()
    return jsonify(docs)


@app.route("/thing/asset/<string:_id>", methods=["GET"])
@csrf.exempt
def thing_asset(_id):
    """Get all things for specific asset type"""
    docs = db.thing_all(_id)
    return jsonify(docs)


@app.route("/thing/<string:_id>", methods=["GET"])
@csrf.exempt
def thing_get(_id):
    """Get info for specific thing"""
    doc = db.thing_get(_id)
    return jsonify(doc)


@app.route("/thing/create", methods=["POST"])
@csrf.exempt
def thing_create():
    """Create new thing"""
    json = request.get_json(force=True)
    res = db.thing_create(json)
    return jsonify(res)


@app.route("/thing/update", methods=["PUT"])
@csrf.exempt
def thing_update():
    """Update thing"""
    json = request.get_json(force=True)
    res = db.thing_update(json)
    return jsonify(res)


@app.route("/thing/delete", methods=["DELETE"])
@csrf.exempt
def thing_delete():
    """Delete thing"""
    json = request.get_json(force=True)
    res = db.thing_delete(json)
    return jsonify(res)


@app.route("/combo/all", methods=["GET"])
@csrf.exempt
def combo_all():
    """Get list of all combos"""
    docs = db.combo_all()
    return jsonify(docs)


@app.route("/combo/<string:_id>", methods=["GET"])
@csrf.exempt
def combo_get(_id):
    """Get info for specific combo"""
    doc = db.combo_get(_id)
    return jsonify(doc)


@app.route("/combo/create", methods=["POST"])
@csrf.exempt
def combo_create():
    """Create new combo"""
    json = request.get_json(force=True)
    res = db.combo_create(json)
    return jsonify(res)


@app.route("/combo/update", methods=["PUT"])
@csrf.exempt
def combo_update():
    """Update combo"""
    json = request.get_json(force=True)
    res = db.combo_update(json)
    return jsonify(res)


@app.route("/combo/delete", methods=["DELETE"])
@csrf.exempt
def combo_delete():
    """Delete combo"""
    json = request.get_json(force=True)
    res = db.combo_delete(json)
    return jsonify(res)


@app.route("/group/all", methods=["GET"])
@csrf.exempt
def group_all():
    """Get info for all groups"""
    docs = db.group_all()
    return jsonify(docs)


@app.route("/group/combo/<string:_id>", methods=["GET"])
@csrf.exempt
def group_asset(_id):
    """Get info for all groups of type combo"""
    docs = db.group_all(_id)
    return jsonify(docs)


@app.route("/group/<string:_id>", methods=["GET"])
@csrf.exempt
def group_get(_id):
    """Get info for specifc group"""
    doc = db.group_get(_id)
    return jsonify(doc)


@app.route("/group/create", methods=["POST"])
@csrf.exempt
def group_create():
    """Create group"""
    json = request.get_json(force=True)
    res = db.group_create(json)
    return jsonify(res)


@app.route("/group/update", methods=["PUT"])
@csrf.exempt
def group_update():
    """Update group"""
    json = request.get_json(force=True)
    res = db.group_update(json)
    return jsonify(res)


@app.route("/group/delete", methods=["DELETE"])
@csrf.exempt
def group_delete():
    """Delete group"""
    json = request.get_json(force=True)
    res = db.group_delete(json)
    return jsonify(res)


@app.route("/image/<string:_id>", methods=["GET"])
@csrf.exempt
def image_get(_id):
    """Get specific image"""
    res = db.image_get(_id)
    return jsonify(res)


@app.route("/image/<string:_id>/info", methods=["GET"])
@csrf.exempt
def image_get_info(_id):
    """Get info on image"""
    res = db.image_get_info(_id)
    return jsonify(res)


@app.route("/image/create", methods=["POST"])
@csrf.exempt
def image_create():
    """Create new image"""
    files = request.files.getlist("files")
    res = db.image_create(files)
    return jsonify(res)


@app.route("/image/update", methods=["PUT"])
@csrf.exempt
def image_update():
    """Update image"""
    json = request.get_json(force=True)
    res = db.image_update(json)
    return jsonify(res)


@app.route("/image/delete", methods=["DELETE"])
@csrf.exempt
def image_delete():
    """Delete image"""
    json = request.get_json(force=True)
    res = db.image_delete(json)
    return jsonify(res)


@app.route("/extra/<string:_id>", methods=["GET"])
@csrf.exempt
def extra_get(_id):
    """Get extra"""
    res = db.extra_get(_id)
    return jsonify(res)


@app.route("/extra/<string:_id>/info", methods=["GET"])
@csrf.exempt
def extra_get_info(_id):
    """Get info about extra"""
    res = db.extra_get_info(_id)
    return jsonify(res)


@app.route("/extra/create", methods=["POST"])
@csrf.exempt
def extra_create():
    """Create extra"""
    files = request.files.getlist("files")
    res = db.extra_create(files)
    return jsonify(res)


@app.route("/extra/update", methods=["PUT"])
@csrf.exempt
def extra_update():
    """Update extra"""
    json = request.get_json(force=True)
    res = db.extra_update(json)
    return jsonify(res)


@app.route("/extra/delete", methods=["DELETE"])
@csrf.exempt
def extra_delete():
    """Delete extra"""
    json = request.get_json(force=True)
    res = db.extra_delete(json)
    return jsonify(res)

@app.route("/download", methods=["GET"])
@csrf.exempt
def download():
    """Downlaod database as a json"""
    res = db.download()
    return jsonify(res)

@app.route("/upload", methods=["POST"])
@csrf.exempt
def upload():
    """Upload json to load data into database"""
    json = request.get_json(force=True)
    res = db.upload(json)
    return jsonify(res)

@app.route("/updates", methods=["GET"])
@csrf.exempt
def updates():
    """Upload json to load data into database"""
    return jsonify(db._updates())

if __name__ == "__main__":
    app.run()
