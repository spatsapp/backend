from flask_pymongo import PyMongo
from shortuuid import ShortUUID
from collections import namedtuple, MutableMapping
from datetime import datetime, date, MINYEAR, MAXYEAR
import math

class Error(Exception):
	def __init__(self, message):
		self.message = message

class InvalidAssetTypeError(Error): pass
class InvalidInheritedAssetError(Error): pass
class InvalidInheritedComboError(Error): pass
class InvalidDecimalError(Error): pass
class InvalidLengthError(Error): pass
class InvalidNameOrId(Error): pass
class InvalidSuidError(Error): pass
class MissingAssetTypeError(Error): pass
class NoDocumentFound(Error): pass
class OutOfBoundsError(Error): pass
class RequiredAttributeError(Error): pass
class UniqueAttributeNotUniqueError(Error): pass
class UnknownFieldError(Error): pass

Decimal = namedtuple('Decimal', ('whole', 'fraction'))

class Suid:
	# https://pypi.org/project/shortuuid/
	def __init__(self, length=7, alphabet="abcdfghijklnoqrstuwxyz"):
		self.alphabet = alphabet
		self.length = length
		self.short_uuid = ShortUUID(alphabet=self.alphabet)

	def generate(self):
		return self.short_uuid.random(length=self.length)

	def validate(self, value):
		return len(value) == 7 and all([char in self.alphabet for char in value])

suid = Suid()

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
		new_value = int(value)
		min_value = params.get('min_value', -math.inf)
		max_value = params.get('max_value', math.inf)
		if not (min_value <= new_value <= max_value):
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
		min_dic = (FieldParser._split_decimal(param_min, precision)
			if param_min is not None
			else {'whole': -math.inf, 'fraction': -math.inf})
		min_value = Decimal(**min_dic)

		param_max = params.get('max_value')
		max_dic = (FieldParser._split_decimal(param_max, precision)
			if param_max is not None
			else {'whole': math.inf, 'fraction': math.inf})
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
		if not suid.validate(str_value):
			raise InvalidSuidError(f'{value} is not a valid suuid')
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

	def _flatten(self, dic, parent_key='', sep='.'):
		# https://stackoverflow.com/a/6027615
		items = []
		for key, value in dic.items():
			new_key = parent_key + sep + key if parent_key else key
			if isinstance(value, MutableMapping):
				items.extend(self._flatten(value, new_key, sep=sep).items())
			else:
				items.append((new_key, value))
		return dict(items)

	def _get(self, collection, filter_):
		doc = self.db[collection].find_one(filter_)
		if doc is None:
			raise NoDocumentFound(f'No document in collection "{collection}" matches filter: {filter_}')
		return doc

	def _get_many(self, collection, filter_={}):
		docs = list(self.db[collection].find(filter_))
		if len(docs) == 0:
			raise NoDocumentFound(f'No documents in collection "{collection}" matches filter: {filter_}')
		return docs

	def _search(self, collection, filter_={}):
		return self.db[collection].find(filter_)

	def _insert(self, collection, document):
		return self.db[collection].insert_one(document)

	def _insert_many(self, collection, documents):
		return self.db[collection].insert_many(documents)

	def _update(self, collection, filter_, update):
		preflat = update.get('_preflat', False)
		if preflat:
			del update['_preflat']
			flat_update = update
		else:
			flat_update = self._flatten(update)
		return self.db[collection].update_one(filter_, {"$set": flat_update}, upsert=False)

	def _update_many(self, collection, filter_, update):
		flat_update = self._flatten(update)
		return self.db[collection].update_many(filter_, {"$set": flat_update}, upsert=False)

	def _delete(self, collection, filter_):
		return self.db[collection].delete_one(filter_)

	def _delete_many(self, collection, filter_):
		return self.db[collection].delete_many(filter_)

	def _merge_docs(self, src, dest):
		dest['inherit'] = src['_id']
		dest_field_names = []
		added_field_names = []
		for name, field in dest['fields'].items():
			dest_field_names.append(name)
			field['inherited'] = False
			field['origin'] = dest['_id']
		for name, field in src['fields'].items():
			if name not in dest_field_names:
				field['inherited'] = True
				dest['fields'][name] = field
				added_field_names.append(name)

		dest['type_list'] = src['type_list'] + [dest['_id']]
		unordered = [ name for name in added_field_names if name not in dest['order'] ]
		dest['order'].extend(unordered)
		return dest

	def _check_unique(self, value, name, origin):
		existing_doc = self._get('thing', {'type_list': origin, f'fields.{name}': value})
		return existing_doc is None

	def _name_or_id(self, value):
		if value.startswith('_'):
			return {'name': value[1:]}
		elif suid.validate(value):
			return {'_id': value}
		else:
			raise InvalidAssetTypeError(f'"{value}" is not a valid name or suid')

	def _verify(self, json, template):
		transformed = {}
		fields = template['fields']
		for name, field in fields.items():
			field_type = field['type']
			params = field.get('parameters')
			params = params if params is not None else {}
			required = params.get('required', False)
			unique = params.get('unique', False)
			if required and name not in json:
				raise RequiredAttributeError(f'"{name}" required field when creating asset "{template["name"]}"')
			if name not in json and 'default' in params:
				transformed[name] = params['default']
			elif name in json:
				transformed[name] = FieldParser.parse(field_type, json[name], params)
			if unique and name in transformed and not self._check_unique(transformed[name], name, field['origin']):
				raise UniqueAttributeNotUniqueError(f'"{name}" is a unique field and matches another document')
		return transformed


	def _symbolic_get(self, type_, value):
		try:
			doc = self._name_or_id(value)
			res = self._get(type_, doc)
		except Exception as e:
			return {'error': e.message, 'value': value}
		else:
			return res

	def _symbolic_create(self, type_, json_list):
		created = []
		errors = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				json['_id'] = suid.generate()
				inherit = json.get('inherit')
				try:
					try:
						doc = self._name_or_id(inherit)
						combo = self._get(type_, doc)
					except NoDocumentFound as e:
						raise InvalidInheritedComboError(f'"{inherit}" is not an existing {type_} type, create before inheriting from it')
				except Exception as e:
					errors.append({
						'message': e.message,
						'document': json
					})
				else:
					json = self._merge_docs(src=combo, dest=json)
					res = self._insert(type_, json)
					created.append(res.inserted_id)
		return {'created': created, 'errored': errors}

	def _symbolic_update(self, type_, json_list):
		updated = 0
		errors = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				_id = json['_id']
				if not suid.validate(_id):
					errors.append({
						'message': f'"{_id}" is an invalid suid.',
						'document': json
					})
				else:
					if "fields" in json:
						to_update = self._get(type_, {'_id': _id})
						for name in json['fields']:
							if to_update['fields'][name]['inherited']:
								json['fields'][name]['inherited'] = False
					res = self._update(type_, {'_id': _id}, json)
					if not res.matched_count:
						errors.append({
							'message': f'"{_id}" does not match any documents to update',
							'document': json
						})
					else:
						child_matches = 0
						if "fields" in json:
							children = self._get_many(type_, {'type_list': _id})
							for child in children:
								child_update = {}
								for name, update in json['fields'].items():
									if child['fields'][name]['inherited']:
										child_update[name] = update
								if child_update:
									child_res = self._update(type_, {'_id': child['_id']}, {'fields': child_update})
									child_matches += child_res.matched_count
						updated += (res.matched_count + child_matches)
		return {'updated': updated, 'errored': errors}

	def _symbolic_delete(self, type_, json_list):
		deleted = 0
		errors = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				_id = json['_id']
				if not suid.validate(_id):
					errors.append({
						'message': f'"{_id}" is an invalid suid.',
						'document': json
					})
				res = self._delete(type_, {'_id': _id})
				if not res.deleted_count:
					errors.append({
						'message': f'"{_id}" does not match any documents to delete',
						'document': json
					})
				else:
					deleted += res.deleted_count
		return {'deleted': deleted, 'errored': errors}

	def _material_all(self, type_, symbolic_type, symbolic_lookup=None):
		material_res = []
		if symbolic_lookup:
			try:
				doc = self._name_or_id(symbolic_lookup)
				symbolic_res = self._get(symbolic_type, doc)
			except Exception as e:
				return {'error': e.message, 'lookup': symbolic_lookup, 'type': type_ }
			else:
				if symbolic_res:
					material_res = self._get_many(type_, {'type_list': symbolic_res['_id']})
		else:
			material_res = self._get_many(type_)
		return list(material_res)

	def _material_get(self, type_, _id):
		try:
			if not suid.validate(_id):
				raise InvalidSuidError(f'"{_id}" is an invalid suid')
			res = self._get(type_, {'_id': _id})
		except Exception as e:
			return {'error': e.message, 'value': _id}
		else:
			return res

	def _material_create(self, type_, json_list):
		created = []
		errors = []
		if json_list:
			transformed = []
			json_list = self._to_list(json_list)
			for json in json_list:
				try:
					symbolic_type = json.get('type')
					if symbolic_type is None:
						raise MissingAssetTypeError(f'No type given to create {type_}')
					symbolic_doc = self._name_or_id(symbolic_type)
					template = self._get(symbolic, symbolic_doc)
					current = {}
					current['_id'] = suid.generate()
					current['type'] = template['_id']
					current['type_list'] = template['type_list']
					current['fields'] = self._verify(json['fields'], template)
					res = self._insert(type_, current)
					created.append(res.inserted_id)
				except Exception as e:
					errors.append({
						'message': e.message,
						'document': json
					})
		return {'created': created, 'errored': errors}

	def _material_update(self, type_, json_list):
		updated = 0
		errors = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				_id = json['_id']
				if not suid.validate(_id):
					errors.append({
						'message': f'"{_id}" is an invalid suid.',
						'document': json
					})
				else:
					res = self._update(type_, {'_id': _id}, json)
					if not res.modified_count:
						errors.append({
							'message': f'"{_id}" does not match any documents to update',
							'document': json
						})
					else:
						updated += res.matched_count
		return {'updated': updated, 'errored': errors}

	def _material_delete(self, type_, json_list):
		deleted = 0
		errors = []
		if json_list:
			json_list = self._to_list(json_list)
			for json in json_list:
				_id = json['_id']
				if not suid.validate(_id):
					errors.append({
						'message': f'"{_id}" is an invalid suid.',
						'document': json
					})
				else:
					res = self._delete(type_, {'_id': _id})
					if not res.deleted_count:
						errors.append({
							'message': f'"{_id}" does not match any documents to delete',
							'document': json
						})
					else:
						deleted += res.deleted_count
		return {'deleted': deleted, 'errored': errors}


	def asset_all(self):
		return self._get_many('asset')

	def asset_get(self, value):
		return self._symbolic_get('asset', value)

	def asset_create(self, json_list):
		self._symbolic_create('asset', json_list)

	def asset_update(self, json_list):
		self._symbolic_update('asset', json_list)

	def asset_delete(self, json_list):
		self._symbolic_delete('asset', json_list)

	def thing_all(self, asset=None):
		return self._material_all('thing', 'asset', asset)

	def thing_get(self, _id):
		return self._material_get('thing', _id)

	def thing_create(self, json_list):
		return self._material_create('thing', json_list)

	def thing_update(self, json_list):
		return self._material_update('thing', json_list)

	def thing_delete(self, json_list):
		return self._material_delete('thing', json_list)

	def combo_all(self):
		return self._get_many('combo')

	def combo_get(self, value):
		return self._symbolic_get('combo', value)

	def combo_create(self, json_list):
		self._symbolic_create('combo', json_list)

	def combo_update(self, json_list):
		self._symbolic_update('combo', json_list)

	def combo_delete(self, json_list):
		self._symbolic_delete('combo', json_list)

	def group_all(self, combo=None):
		return self._material_all('group', 'combo', combo)

	def group_get(self, _id):
		return self._material_get('group', _id)

	def group_create(self, json_list):
		return self._material_create('group', json_list)

	def group_update(self, json_list):
		return self._material_update('group', json_list)

	def group_delete(self, json_list):
		return self._material_delete('group', json_list)
