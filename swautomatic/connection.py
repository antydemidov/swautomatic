"""
swautomatic > `connection`
==========================
Let you connect to MongoDB databases of Swautomatic project.
"""

import logging
from datetime import datetime

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .settings import SWASettings, UTF8


__all__ = ['_settings',
           '_client',
           '_db',
           '_assets_coll',
           '_tags_coll',
           '_logger'
           ]

date = datetime.today().isoformat(sep='_', timespec='minutes')
log_filename = f"logs/{date}.log".replace(':', '-')
_logger = logging.getLogger('swautomatic')
_logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_filename, mode='w', encoding=UTF8)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
_logger.addHandler(handler)

_settings = SWASettings('settings.json')
_client = MongoClient(_settings.uri)
_db: Database = _client.get_database(_settings.database_name)
_assets_coll: Collection = _db.get_collection('assets')
_tags_coll: Collection = _db.get_collection('tags')
