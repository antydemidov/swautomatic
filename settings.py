"""
Steam Workshop Automatic Settings
---
The SWASettings module provides a class named `SWASettings` which is used to store the settings of a project. It contains various attributes to store settings related to the database, file paths, URLs, and timeout.

The `load` method reads the settings.json file and puts its content into the attributes of the `SWASettings` object. It also validates the JSON file against a schema file named `schema.json`. If the JSON file is not valid, it raises a `jsonschema.exceptions.ValidationError`. After loading the settings, the method sets some default values for some attributes if they are not already set.

The `update` method updates the value of an attribute and writes the new settings to the settings.json file. It first reads the current settings from the file, updates the specified attribute with the new value, and then writes the updated settings back to the file. It also sets the new value for the specified attribute in the `SWASettings` object.

Overall, the `SWASettings` class in the SWASettings module provides a convenient way to store and manage settings for a project. It abstracts the details of reading and writing the settings file and provides an easy-to-use interface for accessing and modifying the settings.
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
    - `host` : a string representing the hostname of the MongoDB server. This is read from the `HOST` environment variable or the `settings.json` file if it is defined there.
    - `port` : a string representing the port number on which the MongoDB server is listening. This is read from the `PORT` environment variable or the `settings.json` file if it is defined there.
    - `user` : a string representing the username to use when connecting to the MongoDB server. This is read from the `MONGO_USERNAME` environment variable or the `settings.json` file if it is defined there.
    - `password` : a string representing the password to use when connecting to the MongoDB server. This is read from the `MONGO_PASSWORD` environment variable or the `settings.json` file if it is defined there.
    - `authmechanism`: a string indicating the mechanism to use for authentication. This is set to an empty string by default, but can be set in the `settings.json` file if required.
    - `authsource`: a string representing the name of the database to use for authentication. This is set to an empty string by default, but can be set in the `settings.json` file if required.
    - `common_path`: a string representing a common path for various files used by the project.
    - `appid`: an integer representing the Steam ID of the game.
    - `app_path`: a string representing the path to the game directory.
    - `database_name`: a string representing the name of the MongoDB database to use.
    - `user_url_profiles`: a string representing the URL of the user's Steam profile page.
    - `user_url_id`: a string representing the URL of the user's Steam ID.
    - `asset_url`: a string representing the URL of the assets used by the game.
    - `user_favs_url`: a string representing the URL of the user's favorite items.
    - `links_file_path`: a string representing the path to a file containing links.
    - `previews_path`: a string representing the path to the directory containing preview images.
    - `steam_api_url`: a string representing the URL of the Steam API.
    - `needed_fields`: a list of strings representing the fields that are required for a document.
    - `uri`: a string representing the connection URI for the MongoDB database.
    - `timeout`: a float representing the number of seconds to wait for a request. This is set to 0 by default.
    
    Methods:
    --------
    - `update(self, key, value)`: A method that updates the value of an attribute in the `settings.json` file and in the instance variables of the class. It receives the key and value of the attribute as parameters and writes the new value to the `settings.json` file. It then updates the instance variable with the new value.
    """
    def __init__(self) -> None:
        self.host: str = config('HOST', default='') # outdated
        self.port: str = config('PORT', default='') # outdated
        self.user: str = config('MONGO_USERNAME', default='') # outdated
        self.password: str = config('MONGO_PASSWORD', default='') # outdated
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
        self.timeout: float = 0.0

        try:
            with open('settings.json', 'r', encoding=UTF8) as file:
                settings: dict = json.load(file)
            with open('schema.json', 'r', encoding=UTF8) as file:
                schema = json.load(file)
        except FileNotFoundError('Check the file settings.json') as error:
            raise error

        # ChatGPT said to use cerberus instead of jsonschema
        validate(settings, schema)
        for key, value in settings.items():
            setattr(self, key, value)

        self.assets_path = f'{self.common_path}/Maps'
        self.mods_path = f'{self.common_path}/Mods'
        self.links_file_path = f'{self.common_path}/links.txt'
        if self.app_path == '':
            self.app_path = os.path.abspath(os.path.curdir)

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

    # Reseives key and value of the attribute and put it into the attribute
    # and update the settings.json.

    # ChatGPT: It might be more efficient to read in the JSON data once and
    # store it as an attribute, then modify that data directly and write it
    # back out only when necessary.
    def update(self, key, value):
        """Reseives key and value of the attribute and put it into the attribute
        and update the settings.json."""
        try:
            with open('settings.json', 'r', encoding=UTF8) as file:
                settings: dict = json.loads(file.read())
            settings.update({key: value})

            with open('settings.json', 'w', encoding=UTF8) as file:
                file.write(json.dumps(settings))
            setattr(self, key, value)
        except FileNotFoundError('Check the file settings.json') as error:
            raise error
        return self
