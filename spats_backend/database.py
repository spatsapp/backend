from flask_pymongo import PyMongo
from shortuuid import ShortUUID
from collections import namedtuple
from datetime import datetime
import math

class Error(Exception):
	def __init__(self, message):
		self.message = message

class RequiredAttributeError(Error): pass
class OutOfBoundsError(Error): pass
class InvalidDecimalError(Error): pass
class InvalidLenghtError(Error): pass
class UnknownFieldError(Error): pass

# https://pypi.org/project/shortuuid/
uuid_length = 7
short_uuid = ShortUUID(alphabet="abcdfghijklnoqrstuwxyz") # removed p (q), m (n), e (c), v (u & w)
def suuid():
	return short_uuid.random(length=uuid_length)

Decimal = namedtuple('Decimal', ('whole', 'fraction'))

class TypeParser:
	truthy = ['t', 'true', 'T', 'True', True]
	falsey = ['f', 'false', 'F', 'False', False]

	def boolean(value, params):
		if value not in truthy or value not in falsey:
			raise BooleanNameError(f'Boolean is not of right type. "{value}" needs to be one of the following: {truthy} or {falsey}')
		return value in truthy

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

	def _to_list(self, json):
		return json if isinstance(json, list) else [json]

	def _get(self, collection_name, _id):
		return self.db[collection_name].find_one({'_id': _id})

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
		return self._get('asset', _id)

	def asset_create(self, json_list):
		if json_list:
			json_list = self._to_list(json_list)

			for json in json_list:
				json['_id'] = self.suuid()
				inherit = json.get('inherit')
				if inherit:
					doc = None
					if inherit[0] == '_':
						doc = {'name': inherit[1:]}
					elif len(inherit) == 7:
						doc = {'_id': inherit}
					res = self.db.asset.find_one(doc)
					if res:
						merged = merge_docs(src=res, dest=json)
						json = merged
			res = self.db.asset.insert_many(json_list)
			created = res.inserted_ids
		else:
			created = []

		return {'created': created}

	def asset_update(self, json_list):
		if json_list:
			json_list = self._to_list(json_list)

			updated = 0
			for json in json_list:
				res = self.db.asset.update_one({"_id": json["_id"]}, {"$set": json}, upsert=False)
				updated += res.matched_count
		else:
			updated = 0

		return {'updated': updated}

	def asset_delete(self, json_list):
		if json_list:
			json_list = self._to_list(json_list)

			deleted = 0
			for json in json_list:
				res = self.db.asset.delete_one({"_id": json["_id"]})
				deleted += res.deleted_count
		else:
			deleted = 0

		return {'deleted': deleted}

	def thing_all(self, asset=None):
		if asset:
			res = None
			if '_' == asset[0]:
				res = self.db.asset.find_one({'name': asset[1:]})
			else:
				res = self.db.asset.find_one({'_id': asset})
			if res:
				aid = res['_id']
				res = self.db.thing.find({'asset': aid})
		else:
			res = self.db.thing.find({})

		return res

	def thing_get(self, _id):
		return self._get('thing', _id)

	def _verify(self, json, template):
		transformed = {}
		fields = template['fields']
		for name, field in fields:
			field_type = field['type']
			params = field['parameters']
			if params['required'] and name not in json:
				raise RequiredAttributeError(f'"{name}" required field when creating asset "{template["name"]}"')
			if name not in json and default in params:
				transformed[name] = params['default']
			elif name in json:
				if field_type == "boolean":
					if json[name] not in ['t', 'true', 'True', 'f', 'false', 'False']:
						raise BooleanNameError(f'Boolean is not of right type. "{json[name]}" needs to be one of the following: t, true, True, f, false, or False')
					transformed[name] = json[name] in ['t', 'true', 'True']
				elif filed_type == "string":
					value = json[name]
					min_length = params.get('min_length')
					max_length = params.get('max_length')
					if (min_lenght is not None and len(value < min_length)
						or (max_length is not None and len(value) > max_length):
						raise InvalidLenghtError(f'"{name}" does is either under {min_lenght} or over {max_lenght}')
					transformed[name] = value
				elif field_type == "integer":
					new_value = int(json[name])
					min_value = params.get('min_value', -math.inf)
					max_value = params.get('max_value', math.inf)
					if not (min_value <= new_vale <= max_value):
						raise OutOfBoundsError(f'"{name}" does not fall into required range of {min_value} and {max_value} with a value of "{json[name]}"')
					transformed[name] = new_value
				elif field_type == "decimal":
					str_value = str(json[name])
					precision = params.get('precision')
					point = str_value.count('.')
					if point == 1:
						whole, fraction = str_value.split('.')
						if precision is not None and len(fraction) != precision:
							fraction = fraction.ljust(precision, '0')[:precision]
						if '-' == whole[0]:
							fraction = '-' + fraction
						new_value = Decimal(int(whole), int(fraction))
						min_value = Decimal(**params.get('min_value', {-math.inf, -math.inf}))
						max_value = Decimal(**params.get('max_value', {'whole': math.inf, 'fraction': math.inf}))
						if not (min_value <= new_value <= max_value):
							raise OutOfBoundsError(f'"{name}" does not fall into required range of {min_value} and {max_value} with a value of "{json[name]}"')
					elif point == 0:
						new_value = Decimal(int(whole), 0)
					else:
						raise InvalidDecimalError(f'Decimal value "{json[name]}" has too many decimal points')
					transform[name] = {'whole': new_value['whole'], 'fraction': new_value['fraction']}
				elif field_type == "date":
					date_format = params.get('date_format', '%Y-%m-%d')
					transform[name] = datetime.strptime(json[name], date_format).date()
				elif field_type == "range":
					pass
				elif field_type == "list":
					pass
				elif field_type == "reference":
					pass
				else:
					raise UnknownFieldError(f'Field type of "{field_type}" is undefined')



	def thing_create(self, json_list):
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				json['_id'] = suuid()
		else:
			created = []

		return {'created': created}