# SPATS Personal Asset Tracking Software
This is the backend for SPATS. It is a RESTful api that interfaces with a Mongo database.

## Endpoints
`/` - GET - (get returnts api info, maybe a list of endpoints available and info on them)  

`/asset` - GET - Info on availible assets  
`/asset/<assetId>` - GET - Get info on asset  
`/asset/create` - POST - Create a new asset type, GET will give info on the call  
`/asset/update` - PUT - Update an existing asset type, GET will give info on the call  
`/asset/delete` - DELETE - Delete an asset type based on it's _id, GET will give info on the call  

`/thing/<thingId>` - PUT, DELETE - Get info on thing  
`/thing/create` - POST - Create a new thing, GET will give info on the call  
`/thing/update` - PUT - Update an existing thing, GET will give info on the call  
`/thing/delete` - DELETE - Delete a thing based on it's _id, GET will give info on the call  

`/combo` - GET - Info on availible combos  
`/combo/<comboId>` - GET - Get info on combo  
`/combo/create` - POST - Create a new combo type, GET will give info on the call  
`/combo/update` - PUT - Update an existing combo type, GET will give info on the call  
`/combo/delete` - DELETE - Delete an combo type based on it's _id, GET will give info on the call  

`/group/<groupId>` - GET - Get info on group  
`/group/create` - POST - Create a new group, GET will give info on the call  
`/group/update` - PUT - Update an existing group, GET will give info on the call  
`/group/delete` - DELETE - Delete a group based on it's _id, GET will give info on the call  

`/image/<imageId>` - GET - Retrieve image  
`/image/<imageId>/info` - GET - Get info on the image  
`/image/create` - POST - Upload new image  
`/image/update` - PUT - Update image metadata  
`/image/delete` - DELETE - Delete image  

`/extra/<extraId>` - GET - Retrieve extra file  
`/extra/<extraId>/info` - GET - Get info on the extra file  
`/extra/create` - POST - Upload new extra file  
`/extra/update` - PUT - Update extra file metadata  
`/extra/delete` - DELETE - Delete extra file  


## Collections
* symbolic
  * asset
  * combo
* material
  * thing
  * group
* document
  * image
  * extra


## Types
The following types are permited for fields
* boolean
* date
* int
* decimal (2 ints [whole, fraction]; precision)
* string
* list (sorted) (one of the other)
* reference (string, from shortuuid)


## Symbolic Structure (Assets and Combos)
```
_id: suid
name: string
inherit: symbolic_suid or None / null
fields: {
	name: {
		description: strings
		type: string
		inherited: boolean
		parameters: {
			required (any)
			unique (any)
			default (any)
			list_type (list)
			ordered (list)
			min_length (string)
			max_length (string)
			reference (string)
			min_value (integer, decimal, date)
			max_value (integer, decimal, date)
			precision (decimal)
			date_format (date)
		}
	}, ...
}
order: [ field_name, ... ]
primary: field_name
secondary: field_name
tertiary: [ field_name, ... ]
type_list [ symbolic_suid, ... ]
```

## Material Structure (Things and Groups)
```
_id: suid
type: symbolic_suid
type_list: [ symbolic_suid, ... ]
fields: {
	name: value,
	...
}
```

## Document Structure (Images and Extras)
```
_id: suid
filename: string
metadata: { 
	display: string
	thing: [ material_suid, ... ]
	group: [ material_suid, ... ]
}, 
contentType: string
md5: string
chunkSize: integer
length: long
uploadDate: date
```


## License
[MIT License](https://opensource.org/licenses/MIT)
