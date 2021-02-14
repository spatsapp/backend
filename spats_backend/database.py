from flask_pymongo import PyMongo
from shortuuid import ShortUUID

# https://pypi.org/project/shortuuid/
uuid_length = 7
short_uuid = ShortUUID(alphabet="abcdfghijklnoqrstuwxyz") # removed p (q), m (n), e (c), v (u & w)
def suuid():
	return short_uuid.random(length=uuid_length)


class Database:
	def __init__(self, app=None):
		self.app = app
		if app is not None:
			self.init_app(app)

	def init_app(self,app):
		self.app = app
		self.mongo = PyMongo()
		self.mongo.init_app(app)
		self.db = self.mongo.db

	def info(self,uri):
		return uri_info[uri]


	def _merge_docs(self, src, dest):
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


	def asset_all(self):
		return list(self.db.asset.find({}))

	def asset_get(self, _id):
		pass

	def asset_create(self, json):
		pass

	def asset_update(self, json):
		pass

	def asset_delete(self, json):
		pass
