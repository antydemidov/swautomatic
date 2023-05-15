import logging
import os
from datetime import datetime
from typing import Any

import requests as rq


class SWAAsset:
    # Use multithreading or multiprocessing: If you have many assets to download
    # or process, you could consider using multiple threads or processes to
    # speed up the operations. You could use the threading or multiprocessing
    # modules for this.
    #
    # Optimize database queries: If you're frequently querying the database for
    # individual assets, you could consider batching the queries or using a more
    # efficient query mechanism like aggregation in MongoDB.
    #
    # Optimize I/O operations: If you're frequently reading or writing files to
    # disk, you could consider using asynchronous I/O operations to speed up the process.
    """## Swautomatic > SWA_api > `SWAAsset`
    A class that represents a Steam Workshop asset or mod, which can be
    downloaded and installed.

    ### Attributes
    - `steamid`: an integer representing the Steam Workshop ID of the asset.
    - `info`: a dictionary containing metadata about the asset, such as its
    title, description, and tags. This attribute is initialized to `None` and
    is populated when the `get_info()` method is called.
    - `swa_object`: an instance of the SWAObject class, which provides methods
    for interacting with the Steam Web API and Steam Workshop.

    ### Methods
    - `__init__(self, asset_id: int, swa_object: SWAObject)`
    Creates a new instance of the SWAAsset class with the specified Steam
    Workshop ID and SWAObject instance.
    - `info_steam(self) -> dict`
    Retrieves metadata about the asset from the Steam Web API using the
    `info_steam()` method of the SWAObject instance associated with this asset.
    Returns a dictionary containing the metadata or `None` if the retrieval was
    unsuccessful.
    - `info_database(self)`: Retrieves metadata about the asset from the local
    database using the `find_one()` method of the `assets_coll` collection.
    Returns a dictionary containing the metadata or `None` if the asset is not
    found in the database.
    - `get_info(self)`
    Retrieves metadata about the asset either from the local database or from
    the Steam Web API, depending on which source has more up-to-date information.
    Populates the `info` attribute of this instance with the retrieved metadata
    and returns `True` if the retrieval was successful, `False` otherwise.
    - `download_preview(self)`
    Downloads the preview image of the asset and saves it to disk. If the preview
    image is already downloaded, returns `True`. If the preview URL is not
    available, returns `False`. Returns `True` if the download was successful,
    `False` otherwise.
    - `update_preview_url(self)`
    Updates the preview URL of the asset in the local database with the latest
    value from the Steam Web API. Returns `None`.
    - `download(self) -> bool`
    Downloads and extracts the asset or mod to the appropriate folder. If the
    asset is not installed or needs an update, downloads it from Steam and
    extracts it to the appropriate folder. Finally, updates the local database
    with the new installation time and sets the asset's `is_installed` flag to
    `True`. Returns `True` if the download and extraction were successful,
    `False` otherwise.
    - `is_installed(self)`
    Checks if the asset is installed by checking if its folder exists in the
    `settings.assets_path` or `settings.mods_path`. Returns `True` if the asset
    is installed, `False` otherwise.

    ### Example
    >>> from swautomatic.swa_api import SWAAsset
    ...
    ... # create a SWAObject instance to pass into the SWAAsset constructor
    >>> swa_object = SWAObject()
    ...
    ... # create a new SWAAsset instance with an asset ID and SWAObject instance
    >>> my_asset = SWAAsset("123456789", swa_object)
    ...
    ... # check if the asset is installed
    >>> if my_asset.is_installed():
    ...     print("The asset is already installed!")
    ... else:
    ...     # download and extract the asset
    ...     download_successful = my_asset.download()
    ...     if download_successful:
    ...         print("The asset was downloaded and installed successfully!")
    ...     else:
    ...         print("There was an error downloading or installing the asset.")"""

    def __init__(self, steamid: int | str, swa_object: SWAObject, **kwargs):
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
        if info.get('author'):
            author_data = info.get('author')
            self.author = SWAAuthor(**author_data) # type: ignore
        else:
            self.author = None
        self.need_update = info.get('need_update', False)

        self.type = 'asset' if self.tags is None else 'mod' if any(
            tag.tag == 'Mod' for tag in self.tags) else 'asset'

        if self.type == 'asset':
            self.path = os.path.abspath(os.path.join(
                settings.assets_path, str(steamid)))
        else:
            self.path = os.path.abspath(
                os.path.join(settings.mods_path, str(steamid)))
        self.is_installed = os.path.exists(self.path)

        time_local = info.get('time_local', DFLT_DATE) or DFLT_DATE
        if self.is_installed and (time_local == DFLT_DATE or time_local is None):
            time_local = datetime.fromtimestamp(os.path.getmtime(self.path))
        self.time_local = time_local

    def to_dict(self):
        """### Swautomatic > SWA_api > SWAAsset.`to_dict()`
        Transforms object to `dict`.

        #### Return
        `dict` with asset's data."""

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
        """### Swautomatic > SWA_api > SWAAsset.`send_to_db()`
        Sends the record to the database. If the record exists updates it, else
        inserts the new record to the database.

        #### Return
        `None`"""

        data = self.to_dict()
        assets_coll.update_one(filter={'steamid': data['steamid']},
                               update={'$set': data},
                               upsert=True,
                               session=session)

    def update_record(self):
        """### Swautomatic > SWA_api > SWAAsset.`update_record()`
        Desc

        #### Return
        `None`"""

        data = self.swa_object.info_steam([self.steamid])
        data: dict | None = data.get(self.steamid, None)
        if data is not None:
            data.pop('steamid')
            SWAAsset(self.steamid, self.swa_object, **data).send_to_db()
        else:
            logging.critical('There is no data for asset with id: %s', self.steamid)

    # def info_steam(self) -> dict | None:
    #     """### Swautomatic > SWA_api > SWAAsset.`info_steam()`
    #     It use the method from SWAObject and not duplicate code"""
    #     return self.swa_object.info_steam(self.steamid).get(self.steamid, None)

    # def info_database(self) -> dict | None:
    #     """### Swautomatic > SWA_api > SWAAsset.`info_database()`
    #     Search info about the asset in database"""
    #     return assets_coll.find_one({'steamid': self.steamid})

    def get_info(self) -> dict[str, Any] | None:
        """### Swautomatic > SWA_api > SWAAsset.`get_info()`
        This is the main method to get the asset's or mod's data.

        #### Return
        - `info` (dict): the data of asset."""

        info = assets_coll.find_one({'steamid': self.steamid})
        if not info:
            info = self.swa_object.info_steam(
                [self.steamid]).get(self.steamid, None)
        return info

    def download(self) -> bool:
        """### Swautomatic > SWA_api > SWAAsset.`download()`
        This method `download()` downloads and extracts a Steam Workshop asset
        or mod. If the asset is not installed or needs an update, it downloads
        the asset from Steam and extracts it to the appropriate folder. Finally,
        it updates the local database with the new installation time and sets
        the asset's `is_installed` flag to `True`. It returns a boolean
        indicating whether the download and extraction were successful.

        #### Return
        - `bool` desc."""

        if (self.is_installed and not self.need_update):
            return True

        status = False
        path = f'{self.path}.zip'
        filetypes = ['application/zip', 'application/octet-stream']

        for base_link in base_links:
            url = f'{base_link}{self.steamid}.zip'
            url_headers = rq.head(url, timeout=settings.timeout).headers
            content_type = url_headers.get('Content-Type')
            content_length = int(url_headers.get('Content-Length', 0))
            if (content_type and content_type.split(' ')[0] in filetypes and
                content_length >= 10000):
                with rq.get(url, stream=True, timeout=settings.longtimeout) as req:
                    with open(path, 'wb') as file:
                        file.write(req.content)
                status = True
                break

        try:
            with ZipFile(path, 'r') as file:
                if self.type == 'mod':
                    extract_path = settings.mods_path
                else:
                    extract_path = settings.assets_path
                file.extractall(extract_path)

            os.remove(path)
            status = True
            logging.info('Asset with ID %s was installed', self.steamid)
        except OSError:
            status = False
            logging.critical(
                'Asset with ID %s cannot be installed', self.steamid)

        if status:
            assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {
                    'is_installed': True,
                    'time_local': datetime.now(),
                    'need_update': False
                }}
            )

        return status

    def installed(self):
        """### Swautomatic > SWA_api > SWAAsset.`installed()`
        This method takes a `steam_id` as input and returns a boolean value
        indicating whether the corresponding asset or mod is installed on the
        local machine.

        #### Result
        - `bool` desc."""
        asset_path = os.path.join(settings.assets_path, str(self.steamid))
        mod_path = os.path.join(settings.mods_path, str(self.steamid))

        try:
            is_installed = os.path.exists(
                asset_path) or os.path.exists(mod_path)
        except OSError:
            is_installed = False

        return is_installed

    def get_files(self) -> dict:
        """### Swautomatic > SWA_api > SWAAsset.`get_files()`
        Desc

        #### Return
        - `dict`: `{file name: file size}`."""

        data = {}
        if os.path.exists(self.path):
            files = os.listdir(self.path)
            for file in files:
                full_path = os.path.join(self.path, file)
                data.update({file: os.stat(full_path).st_size})
        else:
            data.update({'No files': 0})
        return data
