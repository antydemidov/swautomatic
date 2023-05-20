"""# swautomatic > `asset`

Module for class `SWAAsset`.
"""

import logging
import os
from datetime import datetime
from typing import Any
from zipfile import ZipFile

import requests as rq

from .author import SWAAuthor
from .connection import _assets_coll, _settings
# from . import SWAObject
from .preview import SWAPreview
from .settings import DFLT_DATE
from .tag import SWATag
from .utils import get_local_time

url_parts = ['cw03361255710', 'cw85745255710',
             'ca40929255710', 'ci03361255710']
base_links = [f'https://cdn.ggntw.com/{i}/' for i in url_parts] + [
    f'https://cdn.steamworkshopdownloader.ru/{i}/' for i in url_parts] + [
        'http://workshop.abcvg.info/archive/255710/'] + [
            f'http://workshop{i+1}.abcvg.info/archive/255710/' for i in range(9)]


class SWAAsset:
    # Use multithreading or multiprocessing: If you have many assets to download
    # or process, you could consider using multiple threads or processes to
    # speed up the operations. You could use the threading or multiprocessing
    # modules for this.
    #
    # Optimize database queries: If you're frequently querying the database for
    # individual assets, you could consider batching the queries or using a
    # more efficient query mechanism like aggregation in MongoDB.
    #
    # Optimize I/O operations: If you're frequently reading or writing files to
    # disk, you could consider using asynchronous I/O operations to speed up the
    # process.
    """## swautomatic > asset > `SWAAsset`
        A class that represents a Steam Workshop asset or mod, which can be
        downloaded and installed.

    ### Attributes
        - `steamid` (integer): represents the Steam Workshop ID of the asset.
        - `info` (dict): contains metadata about the asset, such as its title,
          description, and tags. This attribute is initialized to `None` and
          is populated when the `get_info()` method is called.
        - `swa_object`: an instance of the SWAObject class, which provides
          methods for interacting with the Steam Web API and Steam Workshop.

    ### Methods
        - `info_steam(self) -> dict`
        - `info_database(self)`
        - `get_info(self)`
        - `download_preview(self)`
        - `update_preview_url(self)`
        - `download(self) -> bool`
        - `is_installed(self)`

    ### Example::

        from swautomatic.swa_api import SWAAsset

        # create a SWAObject instance to pass into the SWAAsset constructor
        swa_object = SWAObject()

        # create a new SWAAsset instance with an asset ID and SWAObject instance
        my_asset = SWAAsset("123456789", swa_object)

        # check if the asset is installed
        if my_asset.is_installed():
            print("The asset is already installed!")
        else:
            # download and extract the asset
            download_successful = my_asset.download()
            if download_successful:
                print("The asset was downloaded and installed successfully!")
            else:
                print("There was an error downloading or installing the asset.")
    """

    def __init__(self, steamid: int | str, swa_object, **kwargs):
        self.steamid = int(steamid) # type: ignore
        self.swa_object = swa_object

        info = kwargs or self.get_info()
        if info is None:
            logging.error(
                'There is no asset with ID %s or the app can not find it.', steamid)
            raise TypeError(
                f'There is no asset with ID {steamid} or the app can not find it.')

        self.name = info.get('name')
        tags_data = info.get('tags')
        self.tags = [SWATag(x) for x in tags_data] if tags_data is not None else [
            SWATag('No tags')]
        self.preview = SWAPreview(steam_id=self.steamid,
                                  preview_url=info.get('preview_url', ''))
        self.file_size = info.get('file_size', 0)
        self.time_created = info.get('time_created', DFLT_DATE) or DFLT_DATE
        self.time_updated = info.get('time_updated', DFLT_DATE) or DFLT_DATE
        author_data = info.get('author', dict())
        author_id = int(author_data.get('steam_id64', 0))
        if author_data:
            author_data.pop('steam_id64')
        self.author = SWAAuthor(steamid=author_id,
                                **author_data)


        self.type = 'asset' if self.tags is None else 'mod' if any(
            tag.tag == 'Mod' for tag in self.tags) else 'asset'

        if self.type == 'asset':
            self.path = os.path.abspath(os.path.join(
                _settings.assets_path, str(steamid)))
        else:
            self.path = os.path.abspath(
                os.path.join(_settings.mods_path, str(steamid)))
        self.is_installed = os.path.exists(self.path)

        time_local = get_local_time(self.path) if self.is_installed else DFLT_DATE
        self.time_local = time_local
        self.need_update = (self.is_installed and self.time_local < self.time_updated)

    def to_dict(self):
        """### swautomatic > asset > SWAAsset.`to_dict()`
            Transforms object to `dict`.

        #### Return
            A dictionary with asset's data."""

        result = {}
        for key, value in self.__dict__.items():
            if key == 'author':
                result.update({key: value.to_dict()})
            elif key == 'preview':
                result.update(value.to_dict())
            elif key == 'tags' and value is not None:
                result.update({'tags': [tag.tag for tag in value]})
            elif key == 'swa_object':
                pass
            else:
                result.update({key: value})
        return result

    def send_to_db(self, session=None):
        """### swautomatic > asset > SWAAsset.`send_to_db()`
            Sends the record to the database. If the record exists updates it,
            else inserts the new record to the database.
        """

        data = self.to_dict()
        _assets_coll.update_one(filter={'steamid': data['steamid']},
                               update={'$set': data},
                               upsert=True,
                               session=session)

    def update_record(self):
        """### swautomatic > asset > SWAAsset.`update_record()`
            Desc.
        """

        data = self.swa_object.info_steam([self.steamid])
        data: dict | None = data.get(self.steamid, None) #type: ignore
        if data is not None:
            data.pop('steamid')
            asset = SWAAsset(self.steamid, self.swa_object, **data)
            asset.send_to_db()
            if not asset.preview.downloaded():
                asset.preview.download()
        else:
            logging.critical(
                'There is no data for asset with id: %s', self.steamid)

    def get_info(self) -> dict[str, Any] | None:
        """### swautomatic > asset > SWAAsset.`get_info()`
            This is the main method to get the asset's or mod's data.

        #### Return
            A dictionary with data about asset.
        """

        info = _assets_coll.find_one({'steamid': self.steamid})
        if not info:
            info = self.swa_object.info_steam(
                [self.steamid]).get(self.steamid, None)
        return info

    def download(self) -> bool:
        """### swautomatic > asset > SWAAsset.`download()`
            This method `download()` downloads and extracts a Steam Workshop
            asset or mod. If the asset is not installed or needs an update, it
            downloads the asset from Steam and extracts it to the appropriate
            folder. Finally, it updates the local database with the new
            installation time and sets the asset's `is_installed` flag to
            `True`. It returns a boolean indicating whether the download and
            extraction were successful.

        #### Return
            A boolean.
        """

        if (self.is_installed and not self.need_update):
            return True

        status = False
        path = f'{self.path}.zip'
        filetypes = ['application/zip', 'application/octet-stream']

        for base_link in base_links:
            url = f'{base_link}{self.steamid}.zip'
            url_headers = rq.head(url, timeout=_settings.timeout).headers
            content_type = url_headers.get('Content-Type')
            content_length = int(url_headers.get('Content-Length', 0))
            if (content_type and content_type.split(' ')[0] in filetypes and
                content_length >= 10000):
                with rq.get(url, stream=True, timeout=_settings.longtimeout) as req:
                    with open(path, 'wb') as file:
                        file.write(req.content)
                status = True
                break

        try:
            with ZipFile(path, 'r') as file:
                if self.type == 'mod':
                    extract_path = _settings.mods_path
                else:
                    extract_path = _settings.assets_path
                file.extractall(extract_path)

            os.remove(path)
            status = True
            logging.info('Asset with ID %s was installed', self.steamid)
        except OSError:
            status = False
            logging.critical(
                'Asset with ID %s cannot be installed', self.steamid)

        if status:
            _assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {
                    'is_installed': True,
                    'time_local': datetime.now(),
                    'need_update': False
                }}
            )

        return status

    def installed(self):
        """### swautomatic > asset > SWAAsset.`installed()`
            This method takes a `steam_id` as input and returns a boolean value
            indicating whether the corresponding asset or mod is installed on
            the local machine.

        #### Result
            A boolean.
        """
        asset_path = os.path.join(_settings.assets_path, str(self.steamid))
        mod_path = os.path.join(_settings.mods_path, str(self.steamid))

        try:
            is_installed = os.path.exists(
                asset_path) or os.path.exists(mod_path)
        except OSError:
            is_installed = False

        return is_installed

    def get_files(self) -> dict:
        """### swautomatic > asset > SWAAsset.`get_files()`
            Searches the files of the asset.

        #### Return
            A dictionary `{file name: file size}`.
        """

        data = {}
        if os.path.exists(self.path):
            files = os.listdir(self.path)
            for file in files:
                full_path = os.path.join(self.path, file)
                data.update({file: os.stat(full_path).st_size})
        else:
            data.update({'No files': 0})
        return data
