"""#Steam Workshop Automatic Settings
The SWASettings module provides a class named `SWASettings` which is used to
store the settings of a project. It contains various attributes to store
settings related to the database, file paths, URLs, and timeout.

The `load` method reads the settings.json file and puts its content into the
attributes of the `SWASettings` object. It also validates the JSON file against
a schema file named `schema.json`. If the JSON file is not valid, it raises a
`jsonschema.exceptions.ValidationError`. After loading the settings, the method
sets some default values for some attributes if they are not already set.

The `update` method updates the value of an attribute and writes the new settings
to the settings.json file. It first reads the current settings from the file,
updates the specified attribute with the new value, and then writes the updated
settings back to the file. It also sets the new value for the specified attribute
in the `SWASettings` object.

Overall, the `SWASettings` class in the SWASettings module provides a convenient
way to store and manage settings for a project. It abstracts the details of reading
and writing the settings file and provides an easy-to-use interface for accessing
and modifying the settings."""

import json
import os
from urllib.parse import quote_plus

from jsonschema import ValidationError, validate

from config import Config

__version__ = 'v0.0.1'
__author__ = 'Anton Demidov | @antydemidov'

UTF8 = 'utf-8'
config = Config()

class SWASettings:
    """# Class `SWASettings`
    The object used to store settings of the project.

    ## Attributes:
    - `host` : str - representing the hostname of the MongoDB server. This is
    read from the `HOST` environment variable or the `settings.json` file if
    it is defined there.
    - `port` : str - representing the port number on which the MongoDB server
    is listening. This is read from the `PORT` environment variable or the
    `settings.json` file if it is defined there.
    - `user` : str - representing the username to use when connecting to the
    MongoDB server. This is read from the `MONGO_USERNAME` environment variable
    or the `settings.json` file if it is defined there.
    - `password` : str - representing the password to use when connecting to the
    MongoDB server. This is read from the `MONGO_PASSWORD` environment variable
    or the `settings.json` file if it is defined there.
    - `authmechanism`: str - indicating the mechanism to use for authentication.
    This is set to an empty string by default, but can be set in the
    `settings.json` file if required.
    - `authsource`: str - representing the name of the database to use for
    authentication. This is set to an empty string by default, but can be set
    in the `settings.json` file if required.
    - `common_path`: str - representing a common path for various files used
    by the project.
    - `appid`:  int - representing the Steam ID of the game.
    - `app_path`: str - representing the path to the game directory.
    - `database_name`: str - representing the name of the MongoDB database
    to use.
    - `user_url_profiles`: str - representing the URL of the user's Steam
    profile page.
    - `user_url_id`: str - representing the URL of the user's Steam ID.
    - `asset_url`: str - representing the URL of the assets used by the game.
    - `user_favs_url`: str - representing the URL of the user's favorite items.
    - `links_file_path`: str - representing the path to a file containing links.
    - `previews_path`: str - representing the path to the directory containing
    preview images.
    - `steam_api_url`: str - representing the URL of the Steam API.
    - `needed_fields`: list - of strings representing the fields that are required
    for a document.
    - `uri`: str - representing the connection URI for the MongoDB database.
    - `timeout`: float - representing the number of seconds to wait for a request.
    This is set to 15 by default.
    - `longtimeout`: float - representing the number of seconds to wait for a request.
    This is set to 60 by default.
    - `per_page`:  int - representing the number of assets shown per page.
    This is set to 20 by default.

    ## Methods:
    - `update(self, key, value)`: A method that updates the value of an attribute
    in the `settings.json` file and in the instance variables of the class. It
    receives the key and value of the attribute as parameters and writes the new
    value to the `settings.json` file. It then updates the instance variable with
    the new value."""
    def __init__(self) -> None:
        try:
            with open('settings.json', 'r', encoding=UTF8) as file:
                settings: dict = json.load(file)
        except FileNotFoundError('Check the file settings.json') as error:
            raise error

        self.app_path: str = settings.get('app_path', '')
        self.appid: int = settings.get('appid', 0)
        self.asset_url: str = settings.get('asset_url', '')
        self.authmechanism: str = settings.get('authmechanism', '')
        self.author_needed_fields: list = ['steamID64', 'steamID', 'avatarIcon', 'avatarMedium', 'avatarFull', 'customURL']
        self.authsource: str = settings.get('authsource', '')
        self.common_path: str = settings.get('common_path', '')
        self.database_name: str = settings.get('database_name', '')
        # self.links_file_path: str = settings.get('links_file_path', '')
        self.longtimeout: float = settings.get('longtimeout', 60.0)
        self.needed_fields: list = settings.get('needed_fields', None)
        self.per_page: int = settings.get('per_page', 20)
        self.previews_path: str = settings.get('previews_path', '')
        self.steam_api_url: str = settings.get('steam_api_url', '')
        self.timeout: float = settings.get('timeout', 15.0)
        self.user_favs_url: str = settings.get('user_favs_url', '')
        self.user_url_id: str = settings.get('user_url_id', '')
        self.user_url_profiles: str = settings.get('user_url_profiles', '')

        # ChatGPT said to use cerberus instead of jsonschema
        # validate(settings, schema)

        self.assets_path = os.path.join(self.common_path, 'Maps')
        self.mods_path = os.path.join(self.common_path, 'Mods')
        if self.app_path == '':
            self.app_path = os.path.abspath(os.path.curdir)
        # self.links_file_path = os.path.join(self.app_path, 'links.txt')

        url = f'mongodb://{quote_plus(config.MONGO_USERNAME)}:{quote_plus(config.MONGO_PASSWORD)}'
        auth = f'{config.HOST}:{config.PORT}'
        params = f'?authMechanism={self.authmechanism}&authSource={self.authsource}'
        self.uri = f'{url}@{auth}/{params}'

    # ChatGPT: It might be more efficient to read in the JSON data once and
    # store it as an attribute, then modify that data directly and write it
    # back out only when necessary.
    def update(self, key, value):
        """Reseives key and value of the attribute and put it into the attribute
        and update the settings.json."""
        try:
            with open('settings.json', 'r', encoding=UTF8) as file:
                settings: dict = json.loads(file.read())
            with open('schema.json', 'r', encoding=UTF8) as file:
                schema = json.load(file)
            settings.update({key: value})
            try:
                validate(settings, schema)
            except ValidationError as error:
                print(f'Your settings is not valid: {str(error)}')
                # TODO: Add an errors catcher. Closes #14

            with open('settings.json', 'w', encoding=UTF8) as file:
                file.write(json.dumps(settings))
            setattr(self, key, value)
        except FileNotFoundError('Check the file settings.json') as error:
            raise error
        # return self
