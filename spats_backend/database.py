from flask_pymongo import PyMongo
from shortuuid import ShortUUID
from collections import namedtuple
from datetime import datetime, date, MINYEAR, MAXYEAR
import math

class Error(Exception):
	def __init__(self, message):
		self.message = message

class InvalidAssetTypeError(Error): pass
class InvalidInheritedAssetError(Error): pass
class InvalidDecimalError(Error): pass
class InvalidLengthError(Error): pass
class InvalidSuuidError(Error): pass
class MissingAssetTypeError(Error): pass
class OutOfBoundsError(Error): pass
class RequiredAttributeError(Error): pass
class UnknownFieldError(Error): pass

Decimal = namedtuple('Decimal', ('whole', 'fraction'))

class Suuid:
	# https://pypi.org/project/shortuuid/
	def __init__(self, length=7, alphabet="abcdfghijklnoqrstuwxyz"):
		self.alphabet = alphabet
		self.length = length
		self.short_uuid = ShortUUID(alphabet=self.alphabet)

	def generate(self):
		return self.short_uuid.random(length=self.length)

	def validate(self, value):
		return len(value) == 7 and all([char in self.alphabet for char in value])

suuid = Suuid()

class FieldParser:
	truthy = ['t', 'true', 'T', 'True', True]
	falsey = ['f', 'false', 'F', 'False', False]
	list_types = ['boolean', 'integer', 'decimal', 'date', 'reference']

	def parse(field, value, params):
		return_value = None
		if field == "boolean":
			return_value = FieldParser.boolean_field(value, params)
		elif field == "string":
			return_value = FieldParser.string_field(value, params)
		elif field == "integer":
			return_value = FieldParser.integer_field(value, params)
		elif field == "decimal":
			return_value = FieldParser.decimal_field(value, params)
		elif field == "date":
			return_value = FieldParser.date_field(value, params)
		elif field == "list":
			return_value = FieldParser.list_field(value, params)
		elif field == "reference":
			return_value = FieldParser.reference_field(value, params)
		else:
			raise UnknownFieldError(f'Field type of "{field}" is undefined')
		return return_value

	def boolean_field(value, params):
		if value not in truthy or value not in falsey:
			raise BooleanNameError(f'Boolean is not of right type. "{value}" needs to be one of the following: {truthy} or {falsey}')
		return value in truthy

	def string_field(value, params):
		str_value = str(value)
		min_length = params.get('min_length')
		max_length = params.get('max_length')
		if ((min_length is not None and (len(str_value) < min_length))
			or (max_length is not None and len(str_value) > max_length)):
			raise InvalidLengthError(f'"{value}" does is either under {min_length} or over {max_length}')
		return str_value

	def integer_field(value, params):
		new_value = int(json[name])
		min_value = params.get('min_value', -math.inf)
		max_value = params.get('max_value', math.inf)
		if not (min_value <= new_vale <= max_value):
			raise OutOfBoundsError(f'"{value}" does not fall into required range of {min_value} and {max_value}')
		return new_value

	def _split_decimal(decimal, precision=None):
		str_value = str(decimal)
		point = str_value.count('.')
		whole = '0'
		fraction = '0'
		if point == 1:
			whole, fraction = str_value.split('.')
		elif point == 0:
			whole = str_value
		else:
			raise InvalidDecimalError(f'Decimal value "{str_value}" has too many decimal points')
		if precision is not None and len(fraction) != precision:
			fraction = fraction.ljust(precision, '0')[:precision]
		if whole.startswith('-'):
			fraction = '-' + fraction
		return {'whole': int(whole), 'fraction': int(fraction)}

	def decimal_field(value, params):
		str_value = str(value)
		precision = params.get('precision')

		new_dic = FieldParser._split_decimal(str_value, precision)
		new_value = Decimal(**new_dic)

		param_min = params.get('min_value')
		min_dic = FieldParser._split_decimal(param_min, precision) if param_min is not None else {'whole': -math.inf, 'fraction': -math.inf}
		min_value = Decimal(**min_dic)

		param_max = params.get('max_value')
		max_dic = FieldParser._split_decimal(param_max, precision) if param_max is not None else {'whole': math.inf, 'fraction': math.inf}
		max_value = Decimal(**max_dic)

		if not (min_value <= new_value <= max_value):
			raise OutOfBoundsError(f'"{value}" does not fall into required range of {min_value} and {max_value}')
		return {'whole': new_value.whole, 'fraction': new_value.fraction}

	def date_field(value, params):
		date_format = params.get('date_format', '%Y-%m-%d')
		date_value = datetime.strptime(str(value), date_format)
		min_value = params.get('min_value', datetime(MINYEAR, 1, 1))
		max_value = params.get('max_value', datetime(MAXYEAR, 12, 31))
		if not (min_value <= date_value <= max_value):
			raise OutOfBoundsError(f'"{value}" does not fall into required range of {min_value} and {max_value}')
		return date_value

	def list_field(value, params):
		list_type = params.get('list_type', 'string')
		ordered = params.get('ordered', False)
		if not isinstance(value, list):
			value = [value]
		values = [ FieldParser.parse(list_type, val, params) for val in value ]
		if ordered:
			values.sort()
		return values

	def reference_field(value, params):
		str_value = str(value)
		if not suuid.validate(str_value):
			raise InvalidSuuidError(f'{value} is not a valid suuid')
		return str_value



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

	def _get(self, collection, filter):
		return self.db[collection].find_one(filter)

	def _get_many(self, collection, filter={}):
		return self.db[collection].find(filter)

	def _insert(self, collection, document):
		return self.db[collection].insert_one(document)

	def _insert_many(self, collection, documents):
		return self.db[collection].insert_many(documents)

	def _update(self, collection, filter, update):
		return self.db[collection].update_one(filter, {"$set": update}, upsert=False)

	def _update_many(self, collection, filter, update):
		return self.db[collection].update_many(filter, {"$set": update}, upsert=False)

	def _delete(self, collection, filter):
		return self.db[collection].delete_one(filter)

	def _delete_many(self, collection, filter):
		return self.db[collection].delete_many(filter)

	def _merge_docs(self, src, dest):
		dest['inherit'] = src['_id']
		dest_field_names = []
		added_field_names = []
		for name, field in dest['fields'].items():
			dest_field_names.append(name)
			field['inherited'] = False
		for name, field in src['fields'].items():
			if name not in dest_field_names:
				field['inherited'] = True
				dest['fields'][name] = field
				added_field_names.append(name)

		dest['type_list'] = src['type_list'] + [dest['_id']]
		unordered = [ name for name in added_field_names if name not in dest['order'] ]
		dest['order'].extend(unordered)
		return dest

	def _name_or_id(self, value):
		if value.startswith('_'):
			return {'name': value[1:]}
		elif suuid.validate(value):
			return {'_id': value}
		return None

	def asset_all(self):
		return list(self._get_many('asset'))

	def asset_get(self, value):
		doc = self._name_or_id(value)
		if doc is None:
			raise InvalidAssetTypeError(f'"{value}" is not a valid asset name or id')
		return self._get('asset', doc)

	def asset_create(self, json_list):
		created = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				json['_id'] = suuid.generate()
				inherit = json.get('inherit')
				doc = None
				if inherit is not None:
					doc = self._name_or_id(inherit)
				if doc:
					res = self._get('asset', doc)
					if res:
						json = self._merge_docs(src=res, dest=json)
					else:
						raise InvalidInheritedAssetError(f'"{inherit}" is not an existing asset type')
				elif json['name'] != 'Asset':
					raise InvalidInheritedAssetError(f'"{inherit}" is not a valid asset type')
				else:
					json['type_list'] = [json['_id']]
				res = self._insert('asset', json)
				created.append(res.inserted_id)
		return {'created': created}

	def asset_update(self, json_list):
		updated = 0
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				res = self._update('asset', {'_id': json['_id']}, json)
				updated += res.matched_count
		return {'updated': updated}

	def asset_delete(self, json_list):
		deleted = 0
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				res = self._delete('asset', {"_id": json["_id"]})
				deleted += res.deleted_count
		return {'deleted': deleted}

	def thing_all(self, asset=None):
		thing_res = []
		if asset:
			doc = self._name_or_id(asset)
			asset_res = self._get('asset', doc)
			if asset_res:
				thing_res = self._get_many('thing', {'type_list': asset_res['_id']})
		else:
			thing_res = self._get_many('thing')
		return list(thing_res)

	def thing_get(self, _id):
		return self._get('thing', {'_id': _id})

	def _verify(self, json, template):
		transformed = {}
		fields = template['fields']
		for name, field in fields.items():
			field_type = field['type']
			params = field.get('parameters')
			params = params if params is not None else {}
			required = params.get('required', False)
			if required and name not in json:
				raise RequiredAttributeError(f'"{name}" required field when creating asset "{template["name"]}"')
			if name not in json and 'default' in params:
				transformed[name] = params['default']
			elif name in json:
				transformed[name] = FieldParser.parse(field_type, json[name], params)
		return transformed

	def thing_create(self, json_list):
		created = []
		if json_list:
			transformed = []
			json_list = self._to_list(json_list)
			for json in json_list:
				asset_lookup = json.get('type')
				if asset_lookup is None:
					raise MissingAssetTypeError('No asset given to create thing')
				template = self.asset_get(asset_lookup)
				current = {}
				current['_id'] = suuid.generate()
				current['type'] = template['_id']
				current['type_list'] = template['type_list']
				current['fields'] = self._verify(json['fields'], template)
				res = self._insert('thing', current)
				created.append(res.inserted_id)
		return {'created': created}

	def thing_update(self, json_list):
		updated = 0
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				res = self._update('thing', {'_id': json['_id']}, json)
				updated += res.matched_count
		return {'updated': updated}

	def thing_delete(self, json_list):
		deleted = 0
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				res = self._delete('thing', {"_id": json["_id"]})
				deleted += res.deleted_count
		return {'deleted': deleted}