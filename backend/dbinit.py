"""Generate the base Asset and Combo documents"""


def asset(_id):
    return {
        "_id": _id,
        "name": "Asset",
        "fields": {
            "Combos": {
                "description": "List of names of combos it's in",
                "parameters": {"list_type": "reference"},
                "type": "list",
                "origin": _id,
            },
            "Name": {
                "description": "What you call the thing",
                "parameters": {"required": True},
                "type": "string",
                "origin": _id,
            },
            "Notes": {
                "description": "Special notes that don't fit in any other attributes",
                "parameters": {},
                "type": "string",
                "origin": _id,
            },
            "Pics": {
                "description": "List of pics of the thing",
                "parameters": {"list_type": "reference"},
                "type": "list",
                "origin": _id,
            },
        },
        "order": ["Name", "Notes", "Pics", "Combos"],
        "primary": "Name",
        "secondary": None,
        "tertiary": [],
        "type_list": [_id],
    }


def combo(_id):
    return {
        "_id": _id,
        "name": "Combo",
        "fields": {
            "Combos": {
                "description": "List of names of combos it's in",
                "parameters": {"list_type": "reference"},
                "type": "list",
                "origin": _id,
            },
            "Name": {
                "description": "What you call the thing",
                "parameters": {"required": True},
                "type": "string",
                "origin": _id,
            },
            "Notes": {
                "description": "Special notes that don't fit in any other attributes",
                "parameters": {},
                "type": "string",
                "origin": _id,
            },
            "Pics": {
                "description": "List of pics of the thing",
                "parameters": {"list_type": "reference"},
                "type": "list",
                "origin": _id,
            },
        },
        "order": ["Name", "Notes", "Pics", "Combos"],
        "primary": "Name",
        "secondary": None,
        "tertiary": [],
        "type_list": [_id],
    }
