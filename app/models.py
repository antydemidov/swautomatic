"""Contains the objects' schemas"""

swa_asset_schema = {
    "type": "object",
    "properties": {
        "steamid": {"type": "integer"},
        "name": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "integer"}},
        "preview_url": {"type": "string"},
        # "preview_path": {"type": "string"},
        "path": {"type": "string"},
        "is_installed": {"type": "boolean"},
        "time_local": {"type": "string", "format": "date-time"},
        "file_size": {"type": "integer"},
        "time_created": {"type": "string", "format": "date-time"},
        "time_updated": {"type": "string", "format": "date-time"},
        "author": {"type": "object"},
        "need_update": {"type": "boolean"}
    },
    "required": [
        "steamid",
        "name",
        "tags",
        "preview_url",
        # "preview_path",
        "path",
        "is_installed",
        # "time_local",
        "file_size",
        "time_created",
        # "time_updated",
        "author",
        # "need_update",
    ]
}

swa_author_schema = {
    "type": "object",
    "properties": {
        "steamID64": {"type": "integer"},
        "steamID": {"type": "string"},
        "avatarIcon": {"type": "string"},
        "avatarMedium": {"type": "string"},
        "avatarFull": {"type": "string"},
        "customURL": {"type": "string"}
    },
    "required": [
        "steamID64",
        "steamID",
        "avatarIcon",
        "avatarMedium",
        "avatarFull",
        "customURL"
    ]
}
