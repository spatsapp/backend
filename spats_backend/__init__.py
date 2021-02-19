from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
from shortuuid import ShortUUID
import dotenv

from .database import Database

app = Flask(__name__)
app.config.from_pyfile('backend.cfg')

db = Database()
db.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

@app.before_request
def clear_trailing():
	path = request.path
	if path != '/' and path.endswith('/'):
		return redirect(path[:-1])


@app.route('/', methods=['GET'])
@csrf.exempt
def query_api():
	return jsonify({
		'version': 0.1,
		'endpoints': [
			{
				'uri': '/',
				'description': 'Get information on the api.'
			},
			{
				'uri': '/asset/all',
				'description': 'Retrieve a list of all asset types.'
			},
			{
				'uri': '/asset/{_id}',
				'description': 'Get info on asset with id {_id}'
			}
		]
	})

@app.route('/asset/all', methods=['GET'])
@csrf.exempt
def asset_all():
	docs = db.asset_all()
	return jsonify(docs)

@app.route('/asset/<string:_id>', methods=['GET'])
@csrf.exempt
def asset_get(_id):
	doc = db.asset_get(_id)
	return jsonify(doc)

@app.route('/asset/create', methods=['POST'])
@csrf.exempt
def asset_create():
	json = request.get_json(force=True)
	res = db.asset_create(json)
	return jsonify(res)

@app.route('/asset/update', methods=['PUT'])
@csrf.exempt
def asset_update():
	json = request.get_json(force=True)
	res = db.asset_update(json)
	return jsonify(res)

@app.route('/asset/delete', methods=['DELETE'])
@csrf.exempt
def asset_delete():
	json = request.get_json(force=True)
	res = db.asset_delete(json)
	return jsonify(res)


@app.route('/thing/all', methods=['GET'])
@csrf.exempt
def thing_all():
	docs = db.thing_all()
	return jsonify(docs)

@app.route('/thing/asset/<string:_id>', methods=['GET'])
@csrf.exempt
def thing_asset(_id):
	docs = db.thing_all(_id)
	return jsonify(docs)

@app.route('/thing/<string:_id>', methods=['GET'])
@csrf.exempt
def thing_get(_id):
	doc = db.thing_get(_id)
	return jsonify(doc)

@app.route('/thing/create', methods=['POST'])
@csrf.exempt
def thing_create():
	json = request.get_json(force=True)
	res = db.thing_create(json)
	return jsonify(res)

@app.route('/thing/update', methods=['PUT'])
@csrf.exempt
def thing_update():
	json = request.get_json(force=True)
	res = db.thing_update(json)
	return jsonify(res)

@app.route('/thing/delete', methods=['DELETE'])
@csrf.exempt
def thing_delete():
	json = request.get_json(force=True)
	res = db.thing_delete(json)
	return jsonify(res)


@app.route('/combo/all', methods=['GET'])
@csrf.exempt
def combo_all():
	docs = db.combo_all()
	return jsonify(docs)

@app.route('/combo/<string:_id>', methods=['GET'])
@csrf.exempt
def combo_get(_id):
	doc = db.combo_get(_id)
	return jsonify(doc)

@app.route('/combo/create', methods=['POST'])
@csrf.exempt
def combo_create():
	json = request.get_json(force=True)
	res = db.combo_create(json)
	return jsonify(res)

@app.route('/combo/update', methods=['PUT'])
@csrf.exempt
def combo_update():
	json = request.get_json(force=True)
	res = db.combo_update(json)
	return jsonify(res)

@app.route('/combo/delete', methods=['DELETE'])
@csrf.exempt
def combo_delete():
	json = request.get_json(force=True)
	res = db.combo_delete(json)
	return jsonify(res)


if __name__ == "__main__":
	app.run()