# SPATS Personal Asset Tracking Software
This is the backend for SPATS. It is a RESTful api that interfaces with a Mongo database.

## Endpoints
`/` - GET - (get returnts api info, maybe a list of endpoints available and info on them)  

`/asset` - GET - Info on availible assets  
`/asset/<assetId>` - GET - Get info on asset  
`/asset/create` - GET, POST - Create a new asset type, GET will give info on the call  
`/asset/update` - GET, PUT - Update an existing asset type, GET will give info on the call  
`/asset/delete` - GET, DELTE - Delete an asset type based on it's _id, GET will give info on the call  

`/thing/<thingId>` - GET, PUT, DELETE - Get info on thing  
`/thing/create` - GET, POST - Create a new thing, GET will give info on the call  
`/thing/update` - GET, PUT - Update an existing thing, GET will give info on the call  
`/thing/delete` - GET, DELTE - Delete a thing based on it's _id, GET will give info on the call  

`/combo` - GET - Info on availible combos  
`/combo/<comboId>` - GET - Get info on combo  
`/combo/create` - GET, POST - Create a new combo type, GET will give info on the call  
`/combo/update` - GET, PUT - Update an existing combo type, GET will give info on the call  
`/combo/delete` - GET, DELTE - Delete an combo type based on it's _id, GET will give info on the call  

`/group/<groupId>` - GET - Get info on group  
`/group/create` - GET, POST - Create a new group, GET will give info on the call  
`/group/update` - GET, PUT - Update an existing group, GET will give info on the call  
`/group/delete` - GET, DELTE - Delete a group based on it's _id, GET will give info on the call  


## Collections
* asset
* thing
* combo
* group
* extra (or other) [pics, files, ect.]


## Types
The following types are permited for fields
* boolean
* datetime (date, time, or datetime)
* int
* decimal (2 ints [whole, fraction]; precision)
* string
* list (sorted) (one of the other)
* reference (string, from shortuuid)


## Asset Structure
```
_id: suuid
name: string
inherit: asset_suuid or None / null
fields: {
	name: {
		description: strings
		type: string
		inherited: boolean
		parameters: {
			required (any),
			unique (any),
			default (any),
			min_value (integer, decimal, date),
			max_value (integer, decimal, date),
			ordered (list),
			precision (decimal),
			list_type (list),
			min_length (string)
			max_length (string)
			reference_collection (string, point to collection)
			date_format (string)
		}
	}, ...
}
order: [ field_name, ... ]
primary: field_name
secondary: field_name
tertiary: [ field_name, ... ]
type_list [ asset_id, ... ]
```

## Thing Structure
```
_id: suuid
type: asset_id
type_list: [ asset_id, ... ]
fields: {
	name: value,
	...
}
```

## License
[The Anti-Capitalist Software License (v 1.4)](https://anticapitalist.software)
