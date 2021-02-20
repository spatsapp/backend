from flask_pymongo import PyMongo

from .suid import Suid
from .field_parser import FieldParser

class Error(Exception):
	def __init__(self, message):
		self.message = message

class InvalidSymbolicTypeError(Error): pass
class InvalidInheritedSymbolicError(Error): pass
class InvalidSuidError(Error): pass
class MissingSymbolicTypeError(Error): pass
class NoDocumentFound(Error): pass
class RequiredAttributeError(Error): pass
class UniqueAttributeNotUniqueError(Error): pass

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

		self.suid = Suid()
		self.field_parser = FieldParser()

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
		elif self.suid.validate(value):
			return {'_id': value}
		else:
			raise InvalidSymbolicTypeError(f'"{value}" is not a valid name or suid')

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
				transformed[name] = self.field_parser.parse(field_type, json[name], params)
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
				json['_id'] = self.suid.generate()
				inherit = json.get('inherit')
				try:
					try:
						doc = self._name_or_id(inherit)
						symbolic = self._get(type_, doc)
					except NoDocumentFound as e:
						raise InvalidInheritedSymbolicError(f'"{inherit}" is not an existing {type_} type, create before inheriting from it')
				except Exception as e:
					errors.append({
						'message': e.message,
						'document': json
					})
				else:
					json = self._merge_docs(src=symbolic, dest=json)
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
				if not self.suid.validate(_id):
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
				if not self.suid.validate(_id):
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
			if not self.suid.validate(_id):
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
						raise MissingSymbolicTypeError(f'No type given to create {type_}')
					symbolic_doc = self._name_or_id(symbolic_type)
					template = self._get(symbolic, symbolic_doc)
					current = {}
					current['_id'] = self.suid.generate()
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
				if not self.suid.validate(_id):
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
				if not self.suid.validate(_id):
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
