"""# swautomatic > `connection`

Let you connect to MongoDB databases of Swautomatic project."""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from .settings import SWASettings


_settings = SWASettings()
_client = MongoClient(_settings.uri)
_db: Database = _client.get_database(_settings.database_name)
_assets_coll: Collection = _db.get_collection('assets')
_tags_coll: Collection = _db.get_collection('tags')
