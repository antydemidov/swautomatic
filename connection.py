"""Let you connect to MongoDB databases of Swautomatic project."""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from settings import SWASettings

settings = SWASettings()
client = MongoClient(settings.uri)
db: Database = client.get_database(settings.database_name)
assets_coll: Collection = db.get_collection('assets')
tags_coll: Collection = db.get_collection('tags')
