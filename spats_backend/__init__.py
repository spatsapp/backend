from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
from shortuuid import ShortUUID
import dotenv

from .database import Database

app = Flask(__name__)
app.config.from_pyfile('backend.cfg')

# mongo = PyMongo()
# mongo.init_app(app)
db = Database()
db.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

# https://pypi.org/project/shortuuid/
uuid_length = 7
short_uuid = ShortUUID(alphabet="abcdfghijklnoqrstuwxyz") # removed p (q), m (n), e (c), v (u & w)
def suuid():
	return short_uuid.random(length=uuid_length)

@app.before_request
def clear_trailing():
	path = request.path
	if path != '/' and path.endswith('/'):
		return redirect(path[:-1])


def merge_docs(src, dest):
	dest['inherit'] = src['_id']

	dest_field_names = []
	for name, field in dest['fields'].items():
		dest_field_names.append(name)
		field['inherited'] = False

	added_field_names = []
	for name, field in src['fields'].items():
		if name not in dest_field_names:
			field['inherited'] = True
			dest['fields'][name] = field
			added_field_names.append(name)

	unordered = [ name for name in added_field_names if name not in dest['order'] ]
	dest['order'].extend(unordered)
	return dest


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
	# docs = list(db.asset.find({}))
	docs = db.asset_all()
	return jsonify(docs)

@app.route('/asset/<string:_id>', methods=['GET'])
@csrf.exempt
def asset_get(_id):
	doc = db.asset.find_one({'_id': _id})
	return jsonify(doc)

@app.route('/asset/create', methods=['POST'])
@csrf.exempt
def asset_create():
	json_list = request.get_json(force=True)
	if not isinstance(json_list, list):
		json_list = [json_list]
	for json in json_list:
		json['_id'] = suuid()
		inherit = json.get('inherit')
		if inherit:
			doc = None
			if inherit[0] == '_':
				doc = {'name': inherit[1:]}
			elif len(inherit) == 7:
				doc = {'_id': inherit}
			res = db.asset.find_one(doc)
			if res:
				merged = merge_docs(src=res, dest=json)
				json = merged
	res = db.asset.insert_many(json_list)
	return jsonify({'ids': res.inserted_ids})

@app.route('/asset/update', methods=['PUT'])
@csrf.exempt
def asset_update():
	json_list = request.get_json(force=True)
	if not isinstance(json_list, list):
		json_list = [json_list]

	responses = []
	for json in json_list:
		res = db.asset.update_one({"_id": json["_id"]}, {"$set": json}, upsert=False)
		responses.append(res.raw_result)
	return jsonify(responses)

@app.route('/asset/delete', methods=['DELETE'])
@csrf.exempt
def asset_delete():
	json = request.get_json(force=True)
	if not isinstance(json_list, list):
		json_list = [json_list]

	deleted_count = 0
	for json in json_list:
		res = db.asset.delete_one({"_id": json["_id"]})
		deleted_count += res.deleted_count
	return jsonify({'count': deleted_count})



if __name__ == "__main__":
	app.run()