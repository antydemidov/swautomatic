"""
Let you connect to MongoDB databases of BoD project
"""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# from results import CommonResult
from settings import SWASettings

settings = SWASettings()
client = MongoClient(settings.uri)


class Connection:
    def __init__(self, db_name: str):
        if db_name in client.list_database_names():
            self.db: Database = client.get_database(db_name)
            self.db_name: str = self.db.name
            self.ls_colls: list[str] = self.db.list_collection_names()
            self.client: MongoClient = client
            for coll_name in self.ls_colls:
                self.__setattr__(coll_name, self.get_coll(coll_name))
        else:
            raise ValueError(db_name, 'This database is not exist')

    def get_coll(self, collection_name: str) -> Collection:
        if collection_name is None:
            raise ValueError(collection_name, "must be str")
        else:
            if collection_name in self.ls_colls:
                coll: Collection = self.db.get_collection(collection_name)
                return coll
            else:
                raise NameError('Collection is not exist')

    # def clean(self, collections: list = []):
    #     """
    #     Clean collections in database.
        
    #     Example:
    #     >>> database_cleaner(['houses', 'apartments'])

    #     :Parameters:
    #         `collections: list`: names of collections. If `collections`
    #         are empty, cleans every collection.

    #     ! This method takes some minutes.
    #     """
    #     details = {}
    #     deleted_count = 0
    #     if len(collections) == 0:
    #         colls = self.ls_colls
    #     else:
    #         colls = list(set(self.ls_colls) & set(collections))
    #     for coll_name in colls:
    #         deleted = self.get_coll(coll_name).delete_many({}).deleted_count
    #         details.update({coll_name: deleted})
    #         deleted_count += deleted
    #     result = CommonResult(
    #         status='Done',
    #         details=details,
    #         deleted_count=deleted_count)
    #     return result
