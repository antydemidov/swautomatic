"""
SWA Settings
---
The module contains the class named SWASettings.
"""

import json
import os
from urllib.parse import quote_plus

from decouple import config
from jsonschema import validate

UTF8 = 'utf-8'


class SWASettings:
    """
    The object used to store settings of the project.

    Attributes:
    -----------
    - `HOST` : HOST string;
    - `PORT` : PORT string;
    - `USER` : username string;
    - `PASSWORD` : password string;
    - `authmechanism` : Literal indicating mechanism to authentication;
    - `authsource` : the name of database for authentication;
    - `common_path` : ;
    - `appid` : steam id of the game;
    - `app_path` : ;
    - `database_name` : ;
    - `common_path` : ;
    - `user_url_profiles` : ;
    - `user_url_id` : ;
    - `asset_url` : ;
    - `user_favs_url` : ;
    - `links_file_path` : ;
    - `previews_path` : ;
    - `steam_api_url` : ;
    - `needed_fields` : ;
    - `uri` : the connection URI for the database.
    
    Methods:
    --------
    - `load()` - Reads the settings.json file and put it into attributes of the SWASettings object.
    - `update(key, value)` - Reseives key and value of the attribute and put it into the attribute
    and update the settings.json.
    """
    def __init__(self) -> None:
        self.host: str = config('HOST', default='')
        self.port: str = config('PORT', default='')
        self.user: str = config('MONGO_USERNAME', default='')
        self.password: str = config('MONGO_PASSWORD', default='')
        self.authmechanism: str = ''
        self.authsource: str = ''
        self.common_path: str = ''
        self.appid: int = 0
        self.app_path: str = ''
        self.database_name: str = ''
        self.user_url_profiles: str = ''
        self.user_url_id: str = ''
        self.asset_url: str = ''
        self.user_favs_url: str = ''
        self.links_file_path: str = ''
        self.previews_path: str = ''
        self.steam_api_url: str = ''
        self.needed_fields: list = []
        self.load()

        if (self.user == '' or self.password == ''):
            raise ValueError(
                'Connection needs username and password! Check settings.json')
        if (self.host == '' or self.port == ''):
            raise ValueError(
                'Connection needs host and port! Check settings.json')

        url = f'mongodb://{quote_plus(self.user)}:{quote_plus(self.password)}'
        auth = f'{self.host}:{self.port}'
        params = f'?authMechanism={self.authmechanism}&authSource={self.authsource}'
        self.uri = f'{url}@{auth}/{params}'

    # Reads the settings.json file and put it into attributes of the BODSettings object.
    def load(self):
        """Reads the settings.json file and put it into attributes of the
        SWASettings object."""
        try:
            with open('settings.json', 'r', encoding=UTF8) as file:
                settings: dict = json.load(file)
            with open('schema.json', 'r', encoding=UTF8) as file:
                schema = json.load(file)
        except NameError('Check the file settings.json') as error:
            raise error

        validate(settings, schema)
        for key, value in settings.items():
            setattr(self, key, value)

        self.assets_path = self.common_path + '/Maps'
        self.mods_path = self.common_path + '/Mods'
        self.links_file_path = self.common_path + '/links.txt'
        if self.app_path == '':
            self.app_path = os.path.abspath(os.path.curdir)

        return self

    # Reseives key and value of the attribute and put it into the attribute
    # and update the settings.json.
    def update(self, key, value):
        """Reseives key and value of the attribute and put it into the attribute
        and update the settings.json."""
        with open('settings.json', 'r', encoding=UTF8) as file:
            settings: dict = json.loads(file.read())
        settings.update({key: value})

        with open('settings.json', 'w', encoding=UTF8) as file:
            file.write(json.dumps(settings))
        setattr(self, key, value)

        return self
