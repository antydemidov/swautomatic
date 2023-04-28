"""Let you connect to MongoDB databases of Swautomatic project."""

from pymongo import MongoClient

from settings import SWASettings

settings = SWASettings()
client = MongoClient(settings.uri)
db = client.get_database(settings.database_name)
assets_coll = db.get_collection('assets')
tags_coll = db.get_collection('tags')
