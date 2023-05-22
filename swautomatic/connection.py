"""# swautomatic > `connection`

Let you connect to MongoDB databases of Swautomatic project."""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .settings import SWASettings

__all__ = [
    '_settings',
    '_client',
    '_db',
    '_assets_coll',
    '_tags_coll',
]

_settings = SWASettings()
_client = MongoClient(_settings.uri)
_db: Database = _client.get_database(_settings.database_name)
_assets_coll: Collection = _db.get_collection('assets')
_tags_coll: Collection = _db.get_collection('tags')
