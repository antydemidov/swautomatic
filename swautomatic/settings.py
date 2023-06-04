"""
Swautomatic > `Settings`
========================
The SWASettings module provides a class named `SWASettings` which is used to
store the settings of a project. It contains various attributes to store
settings related to the database, file paths, URLs, and timeout.
"""

import json
import os
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import dotenv

# from jsonschema import ValidationError, validate


__all__ = ['DFLT_DATE', 'ASSET', 'MOD', 'UTF8',
           'SWASettings', 'BASE_LINKS', 'FILETYPES']

DFLT_DATE = datetime.fromordinal(1)
'Default datetime if calculation was failed.'
# types
ASSET = 'asset'
'The name of type `Asset`'
MOD = 'mod'
'The name of type `Mod`'
UTF8 = 'utf-8'

NEEDED_FIELDS = ['creator', 'file_size', 'preview_url', 'publishedfileid',
                 'tags', 'time_created', 'time_updated', 'title']

AUTHOR_NEEDED_FIELDS = ['steamID64', 'steamID', 'avatarIcon', 'avatarMedium',
                        'avatarFull', 'customURL']

MAPPING_FIELDS = {'steamID64': 'steam_id64',
                  'steamID': 'steam_id',
                  'avatarIcon': 'avatar_icon',
                  'avatarMedium': 'avatar_medium',
                  'avatarFull': 'avatar_full',
                  'customURL': 'custom_url'}

VARIABLES = ['app_path', 'appid', 'asset_url', 'authmechanism', 'authsource',
             'common_path', 'database_name', 'longtimeout', 'per_page',
             'previews_path', 'steam_api_url', 'timeout', 'user_favs_url',
             'user_url_id', 'user_url_profiles']

url_parts = ['cw03361255710', 'cw85745255710',
             'ca40929255710', 'ci03361255710']
BASE_LINKS = [f'https://cdn.ggntw.com/{i}/' for i in url_parts] + [
    f'https://cdn.steamworkshopdownloader.ru/{i}/' for i in url_parts] + [
        'http://workshop.abcvg.info/archive/255710/'] + [
            f'http://workshop{i+1}.abcvg.info/archive/255710/' for i in range(9)]

FILETYPES = ['application/zip', 'application/octet-stream']

dotenv.load_dotenv()


class SWASettings:
    """
    swautomatic > settings > `SWASettings`
    --------------------------------------
    The object used to store settings of the project. The __setattr__ method
    was redefined, not it is saving the data to JSON file when the attribute
    was set.

    ! Keep in mind that this class must have the only instance (in basic case).

    Attributes
    ----------
    -   `app_path`: (string) - representing the path to the game directory.
    -   `appid`:  (integer) - representing the Steam ID of the game.
    -   `asset_url`: (string) - representing the URL of the assets used by the
        game.
    -   `authmechanism`: (string) - indicating the mechanism to use for
        authentication. It is a part of `uri`.
    -   `authsource`: (string) - representing the name of the database to use for
        authentication. It is a part of `uri`.
    -   `common_path`: (string) - representing a common path for various files used
        by the project.
    -   `database_name`: (string) - representing the name of the MongoDB database
        to use.
    -   `longtimeout`: float - representing the number of seconds to wait for a
        request.
    -   `per_page`:  (integer) - representing the number of assets shown per page.
    -   `previews_path`: (string) - representing the path to the directory
        containing preview images.
    -   `steam_api_url`: (string) - representing the URL of the Steam API.
    -   `timeout`: float - representing the number of seconds to wait for a
        request.
    -   `user_favs_url`: (string) - representing the URL of the user's favorite
        items.
    -   `user_url_id`: (string) - representing the URL of the user's Steam ID.
    -   `user_url_profiles`: (string) - representing the URL of the user's Steam
        profile page.
    -   `uri`: (string) - representing the connection URI for the MongoDB database.
    -   `needed_fields`: (list) - of strings representing the fields that are
        required for a document.
    -   `author_needed_fields`: (list) - a list of fields for `SWAAuthor`.
    -   `assets_path`: (string) - a path to assets.
    -   `mods_path`: (string) - a path to mods.
    -   `mapping_fields` (dictionary) - a mapping for Steam field to
        Swautomatic fields.
    """

    secret_key = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Write an intruction to store the instance of this class
    # It must be a single
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            error = OSError()
            error.add_note(f'The file {file_path} does not exist.')
            raise error
        self.__load_settings()
        if any(getattr(self, attr, None) is None for attr in VARIABLES):
            raise ValueError('Some of attributes are empty. Check the settings.')

    def __load_settings(self) -> None:
        """Loads the settings data from json file."""

        with open(self.file_path, 'r', encoding=UTF8) as file:
            data: dict = json.load(file)
        self.app_path:          str | None = data.get('app_path')
        self.appid:             int | None = data.get('appid')
        self.asset_url:         str | None = data.get('asset_url')
        self.authmechanism:     str | None = data.get('authmechanism')
        self.authsource:        str | None = data.get('authsource')
        self.common_path:       str | None = data.get('common_path')
        self.database_name:     str | None = data.get('database_name')
        self.longtimeout:     float | None = data.get('longtimeout')
        self.per_page:          int | None = data.get('per_page')
        self.previews_path:     str | None = data.get('previews_path')
        self.steam_api_url:     str | None = data.get('steam_api_url')
        self.timeout:         float | None = data.get('timeout')
        self.user_favs_url:     str | None = data.get('user_favs_url')
        self.user_url_id:       str | None = data.get('user_url_id')
        self.user_url_profiles: str | None = data.get('user_url_profiles')
        self.uri = self.__build_uri()
        if not self.common_path:
            self.common_path = os.path.abspath(os.path.curdir)
        self.assets_path = os.path.join(self.common_path, 'Maps')
        self.mods_path = os.path.join(self.common_path, 'Mods')
        if not self.app_path:
            self.app_path = os.path.abspath(os.path.curdir)
        self.needed_fields: list = NEEDED_FIELDS
        self.author_needed_fields: list = AUTHOR_NEEDED_FIELDS
        self.mapping_fields = MAPPING_FIELDS

    def __build_uri(self):
        host = os.environ.get('HOST') or 'localhost'
        port = os.environ.get('PORT') or '27017'
        mongo_username = os.environ.get('MONGO_USERNAME') or 'you-will-never-guess'
        mongo_password = os.environ.get('MONGO_PASSWORD') or 'you-will-never-guess'
        return f'mongodb://{quote_plus(mongo_username)}:' \
               f'{quote_plus(mongo_password)}@{host}:{port}' \
               f'/?authMechanism={self.authmechanism}&authSource={self.authsource}'

    def update(self, name: str, value: Any) -> None:
        """Updates an attribute and dumps it to the settings file."""

        self.__dict__[name] = value
        if name in VARIABLES:
            self.__save_settings()

    def __save_settings(self) -> None:
        """Dumps the data to json file."""

        data = {field: getattr(self, field) for field in VARIABLES}
        with open(self.file_path, 'w', encoding=UTF8) as file:
            json.dump(data, file, indent=4)


if __name__ == '__main__':
    settings = SWASettings('settings.json')
    print(settings.app_path)
