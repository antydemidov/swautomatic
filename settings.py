import json
import os
from sqlite3 import OperationalError
from urllib.parse import quote_plus

from decouple import config
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class SWASettings:
    def __init__(self) -> None:
        self.HOST: str = config('HOST', default='')
        self.PORT: str = config('PORT', default='')
        self.USER: str = config('MONGO_USERNAME', default='')
        self.PASSWORD: str = config('MONGO_PASSWORD', default='')
        self.authmechanism: str = ''
        self.authsource: str = ''
        self.common_path: str = ''
        self.appid: int = 0
        self.app_path: str = ''
        self.database_name: str = ''
        self.common_path: str = ''
        self.user_url_profiles: str = ''
        self.user_url_id: str = ''
        self.asset_url: str = ''
        self.user_favs_url: str = ''
        self.links_file_path: str = ''
        self.previews_path: str = ''
        self.steam_api_url: str = ''
        self.needed_fields: list = []

    def load(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                settings: dict = json.loads(f.read())
            for k, v in settings.items():
                self.__setattr__(k, v)
            self.assets_path = self.common_path + '/Maps'
            self.mods_path = self.common_path + '/Mods'
            self.links_file_path = self.common_path + '/links.txt'
            if self.app_path == '':
                self.app_path = os.path.abspath(os.path.curdir)
        else:
            raise NameError('Check the path to settings.json')
        return self

    def update(self, **kwargs):
        with open('settings.json', 'r') as f:
            settings: dict = json.loads(f.read())
        for key, value in kwargs.items():
            key = key.lower()
            settings.update({key: value})
            self.__setattr__(key, value)
        with open('settings.json', 'w') as f:
            f.write(json.dumps(settings, ))
        return self

    def validate(self):
        if (self.USER == '' or self.PASSWORD == ''):
            raise ValueError('Connection needs username and password! Check .env')
        elif (self.HOST == '' or self.PORT == ''):
            raise ValueError('Connection needs host and port! Check .env')
        else:
            try:
                uri = f"mongodb://{quote_plus(self.USER)}:{quote_plus(self.PASSWORD)}@{self.HOST}:{self.PORT}/?authMechanism={self.authmechanism}&authSource={self.authsource}"
                client = MongoClient(uri)
                client.list_database_names()
            except ConnectionFailure as err:
                print(err.add_note("Server is not available"))
            except OperationalError as err:
                print(err.add_note("Check authorization"))
        return self