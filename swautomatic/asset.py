"""
swautomatic > `asset`
=====================
Module for class `SWAAsset` and it`s interface - ISWAAssets.
"""

import os
from typing import Optional
from zipfile import ZipFile

import requests as rq
from bs4 import BeautifulSoup as bs
from pymongo import UpdateOne

from .author import SWAAuthor
from .connection import _assets_coll, _logger, _settings
from .preview import SWAPreview
from .results import CommonResult, DeleteResult
from .settings import ASSET, DFLT_DATE, MOD, BASE_LINKS, FILETYPES
from .tag import SWATag
from .utils import (check_datetime, delete_directory, get_directory_size,
                    get_info, get_local_time, get_size_format, info_steam,
                    steam_api_data)

__all__ = [
    'SWAAsset',
    'ISWAAssets'
]


# region with trying to format the data
# database_to_asset = {
#     'steamid': 'steamid',
#     'name': 'name',
#     'tags': 'tags',
#     'preview_url': 'preview_url',
#     'file_size': 'file_size',
#     'time_created': 'time_created',
#     'time_updated': 'time_updated',
#     'author': 'author',
# }
# steam_to_asset = {
#     'publishedfileid': 'steamid',
#     'title': 'name',
#     'tags': 'tags',
#     'preview_url': 'preview_url',
#     'file_size': 'file_size',
#     'time_created': 'time_created',
#     'time_updated': 'time_updated',
#     'creator': 'author',
# }


# @dataclass
# class FormatAssetDatabase:
#     """The class for formatting the data of assets."""

#     steamid: int = 0
#     name: Optional[str] = None
#     tags: list[str] = field(default_factory=list[str])
#     preview_url: Optional[str] = None
#     file_size: int = 0
#     time_created: datetime = DFLT_DATE
#     time_updated: datetime = DFLT_DATE
#     author: Optional[dict] = None


# @dataclass
# class FormatAssetSteam:
#     """The class for formatting the data of assets."""

#     publishedfileid: int = 0
#     title: Optional[str] = None
#     tags: list[str] = field(default_factory=list[str])
#     preview_url: Optional[str] = None
#     file_size: int = 0
#     time_created: datetime = DFLT_DATE
#     time_updated: datetime = DFLT_DATE
#     creator: Optional[dict] = None


# class FormatAsset(object):
#     """The class for formatting the data of assets."""

#     __slots__ = ('steamid', 'name', 'tags', 'preview_url', 'path',
#                  'is_installed', 'time_local', 'file_size', 'time_created',
#                  'time_updated', 'author', 'need_update', 'type')

#     def __init__(self, data: dict, source_type: Literal['database', 'steam']) -> None:
#         self.steamid: int = 0
#         self.name: Optional[str] = None
#         self.tags: list[str] = ['No tags']
#         self.preview_url: Optional[str] = None
#         self.file_size: int = 0
#         self.time_created: datetime = DFLT_DATE
#         self.time_updated: datetime = DFLT_DATE
#         self.author: Optional[dict] = None
#         if source_type == 'database':
#             asset = self.__database_format(data)
#             for src, dst in database_to_asset.items():
#                 setattr(self, dst, getattr(asset, src))
#         elif source_type == 'steam':
#             asset = self.__steam_format(data)
#             for src, dst in steam_to_asset.items():
#                 setattr(self, dst, getattr(asset, src))
#         self.type = MOD if 'Mod' in self.tags else ASSET
#         if self.type == MOD:
#             self.path = os.path.join(_settings.mods_path, str(self.steamid))
#         else:
#             self.path = os.path.join(_settings.assets_path, str(self.steamid))
#         self.is_installed: bool = os.path.exists(self.path)
#         self.time_local: datetime = get_local_time(self.path)
#         self.need_update: bool = self.is_installed and (
#             self.time_local < self.time_updated)

#     def __database_format(self, data: dict):
#         steamid = int(data.get('steamid', 0))
#         name = data.get('name')
#         tags = data.get('tags')
#         if not tags:
#             tags = ['No tags']
#         preview_url = data.get('preview_url')
#         file_size: int = data.get('file_size', 0)
#         time_created = check_datetime(data.get('time_created'))
#         time_updated = check_datetime(data.get('time_updated'))
#         author_data = data['author']
#         author = SWAAuthor(**author_data).to_dict()
#         asset = FormatAssetDatabase(steamid, name, tags, preview_url, file_size,
#                                     time_created, time_updated, author)
#         return asset

#     def __steam_format(self, data: dict[str, Any]):
#         # === steamid ===
#         publishedfileid = int(data.get('publishedfileid', 0))
#         # === name ===
#         title = data.get('title', None)
#         # === tags ===
#         workshop_tags: list | None = data.get('tags')
#         tags = None
#         if workshop_tags:
#             try:
#                 tags = [workshop_tag['tag']
#                         for workshop_tag in workshop_tags if
#                         workshop_tag is not None]
#             except (KeyError, TypeError) as error:
#                 logging.error(
#                     'Failed to retrieve tags for asset with Steam ID %s: %s',
#                     publishedfileid, error)
#         if tags is None:
#             tags = ['No tags']
#         # === preview ===
#         preview_url: str | None = data.get('preview_url')
#         file_size: int = data.get('file_size', 0)
#         time_created = check_datetime(data.get('time_created'))
#         time_updated = check_datetime(data.get('time_updated'))
#         # === author ===
#         try:
#             creator = SWAAuthor(int(data['creator'])).to_dict()
#         except KeyError as error:
#             logging.error('Failed to retrieve author data for asset with\
#                 Steam ID %s: %s', publishedfileid, error)
#             creator = None
#         asset = FormatAssetSteam(publishedfileid, title, tags, preview_url,
#                                  file_size, time_created, time_updated, creator)
#         return asset
# endregion


class SWAAsset(object):
    """
    swautomatic > asset > `SWAAsset`
    --------------------------------
    A class that represents a Steam Workshop asset or mod, which can be
    downloaded and installed.

    Attributes
    ----------
    -   `steamid` (integer or string): represents the Steam Workshop ID of
        the asset.
    -   `**kwargs`: can contain other parameters of the asset.

    Methods
    -------
    -   `to_dict()`: desc.
    -   `send_to_db()`: desc.
    -   `update_record()`: desc.
    -   `download()`: desc.
    -   `installed()`: desc.
    -   `get_files()`: desc.

    Example:
    --------
    ```python
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
    ```
    """

    # __slots__ = ('steamid', '__interface', 'name', 'tags', 'preview', 'file_size',
    #              'time_created', 'time_updated', 'author', 'type', 'path',
    #              'is_installed', 'time_local', 'need_update')
    # slots = __slots__

    def __init__(self, force_steam: bool = False, **kwargs):
        if kwargs and 'steamid' in kwargs:
            self.steamid = int(kwargs.pop('steamid'))
        else:
            raise ValueError('Parameter `steamid` is expected.')

        info = kwargs or get_info(self.steamid, force_steam)
        if info is None:
            _logger.error(
                'There is no asset with ID %s or the app can not find it.',
                self.steamid)
            raise TypeError(f'There is no asset with ID {self.steamid} or the \
                app can not find it.')

        self.name = info.pop('name', None)
        tags_data = info.pop('tags', None)
        self.tags = [SWATag(x) for x in tags_data] if tags_data is not None else [
            SWATag('No tags')]
        self.preview = SWAPreview(steam_id=self.steamid,
                                  preview_url=info.pop('preview_url', ''))
        self.file_size = int(info.pop('file_size', 0))
        self.time_created = check_datetime(info.pop('time_created', None))
        self.time_updated = check_datetime(info.pop('time_updated', None))
        author_data = info.pop('author', {})
        if info:
            _logger.info('Unexpected keys %s', str(info.keys()))
        self.author = SWAAuthor(**author_data)

        self.type = ASSET if self.tags is None else MOD if any(
            tag.tag == 'Mod' for tag in self.tags) else ASSET

        self.path = self.__get_path()
        self.is_installed = os.path.exists(self.path)

        self.time_local = get_local_time(self.path)
        self.need_update = self.__need_update()

    def __need_update(self) -> bool:
        """Checks if the asset needs update."""

        return (self.is_installed and self.time_local < self.time_updated)

    def __get_path(self) -> str:
        """Returns asset's path."""

        if self.type == ASSET:
            path = os.path.abspath(os.path.join(
                _settings.assets_path, str(self.steamid)))
        else:
            path = os.path.abspath(os.path.join(
                _settings.mods_path, str(self.steamid)))
        return path

    def to_dict(self) -> dict:
        """
        swautomatic > asset > SWAAsset.`to_dict()`
        ------------------------------------------
        Transforms object to `dict`.

        Return
        ------
        A dictionary with asset's data.
        """

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
        """
        swautomatic > asset > SWAAsset.`send_to_db()`
        ---------------------------------------------
        Sends the record to the database. If the record exists updates it,
        else inserts the new record to the database.

        Return
        ------
        `CommonResult` with attributes `status`, `status_bool`, `message`, `count`.
        """

        data = self.to_dict()
        count = _assets_coll.update_one(filter={'steamid': data['steamid']},
                                        update={'$set': data},
                                        upsert=True,
                                        session=session,
                                        ).modified_count

        return CommonResult(status='Done' if count != 0 else 'Error',
                            status_bool=count != 0,
                            message=f'{count} record was updated.',
                            count=count)

    def update_record(self) -> CommonResult:
        """
        swautomatic > asset > SWAAsset.`update_record()`
        ------------------------------------------------
        Sends the record to the database. If the record exists updates it,
        else inserts the new record to the database. Also it downloads a
        preview for the asset.

        Return
        ------
        `CommonResult` with attributes:
        -   `status`
        -   `status_bool`
        -   `message`
        -   `count`
        -   `preview_size`.
        """

        asset = SWAAsset(force_steam=True, steamid=self.steamid)
        result = asset.send_to_db()
        if not asset.preview.downloaded():
            size = asset.preview.download()
            result.preview_size = size
            # setattr(result, 'preview_size', size)

        return result

    def download(self) -> bool:
        """
        swautomatic > asset > SWAAsset.`download()`
        -------------------------------------------
        This method `download()` downloads and extracts a Steam Workshop
        asset or mod. If the asset is not installed or needs an update, it
        downloads the asset from Steam and extracts it to the appropriate
        folder. Finally, it updates the local database with the new
        installation time and sets the asset's `is_installed` flag to
        `True`. It returns a boolean indicating whether the download and
        extraction were successful.

        Return
        ------
        A boolean status.
        """

        if (self.is_installed and not self.need_update):
            return True

        status = False
        path = f'{self.path}.zip'

        for base_link in BASE_LINKS:
            url = f'{base_link}{self.steamid}.zip'
            url_headers = rq.head(url,
                                  timeout=_settings.timeout
                                  ).headers
            content_type = url_headers.get('Content-Type')
            content_length = int(url_headers.get('Content-Length', 0))
            if (content_type and content_type.split(' ')[0] in FILETYPES and
                content_length >= 10000):
                with rq.get(url, stream=True,
                            timeout=_settings.longtimeout
                            ) as req:
                    with open(path, 'wb') as file:
                        file.write(req.content)
                status = True
                break

        try:
            with ZipFile(path, 'r') as file:
                if self.type == MOD:
                    extract_path = _settings.mods_path
                else:
                    extract_path = _settings.assets_path
                file.extractall(extract_path)

            os.remove(path)
            status = True
            _assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {
                    'is_installed': True,
                    'time_local': get_local_time(extract_path),
                    'need_update': False
                }}
            )
            _logger.info('Asset with ID %s was installed', self.steamid)
        except OSError:
            status = False
            _logger.critical(
                'Asset with ID %s cannot be installed', self.steamid)

        return status

    def get_files(self) -> dict[str, int]:
        """
        swautomatic > asset > SWAAsset.`get_files()`
        --------------------------------------------
        Searches the files of the asset.

        Return
        ------
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


class ISWAAssets:
    """
    swautomatic > asset > `ISWAAssets`
    ----------------------------------
    Description.
    """
    def __init__(self) -> None:
        self.coll = _assets_coll

    def get_asset(self, steam_id: int | str) -> SWAAsset:
        """
        swautomatic > asset > ISWAAssets.`get_asset()`
        ----------------------------------------------
        Description.
        """

        return SWAAsset(steamid=steam_id)

    def get_assets(self, **kwargs) -> list[SWAAsset]:
        """
        swautomatic > asset > ISWAAssets.`get_assets()`
        -----------------------------------------------

        Retrieves a list of SWAAsset objects based on the provided parameters.

        !!! It works only with assets in database. Assets which not exists
        will not be in returned list.

        If parameters are not correct instances, they are ignored.

        Example
        -------
        ```python
        >>> swa_object = SWAObject()
        >>> swa_object.assets.get_assets([123, 321])
        # [SWAAsset(swa_object=123), SWAAsset(swa_object=321)]
        
        >>> swa_object.assets.get_assets([123, 321], is_installed=True)
        # [SWAAsset(swa_object=123)]
        ```

        Parameters
        ----------
        -   `steam_ids` (optional, default `None`): a list of assets steam ids.
        -   `tag` (optional, default `None`): desc.
        -   `need_update` (optional, default `None`): desc.
        -   `is_installed` (optional, default `None`): desc.
        -   `other_fltr` (optional, default `None`): a dict used as a filter
            for Mongo request.
        -   `skip` (optional, default `0`): a number of records to skip.
        -   `limit` (optional, default `0`): a number of records to show.
        
        Return
        ------
        A list of SWAAsset objects.
        """
        fltr = {}
        steam_ids = kwargs.get('steam_ids', None)
        tag = kwargs.get('tag', None)
        need_update = kwargs.get('need_update', None)
        is_installed = kwargs.get('is_installed', None)
        other_fltr = kwargs.get('other_fltr', None)
        skip = kwargs.get('skip', 0)
        limit = kwargs.get('limit', 0)

        if isinstance(steam_ids, (list, set)):
            fltr.update({'steamid': {'$in': steam_ids}})
        if isinstance(tag, str):
            fltr.update({'tags': tag})
        if isinstance(need_update, bool):
            fltr.update({'need_update': need_update})
        if isinstance(is_installed, bool):
            fltr.update({'is_installed': is_installed})
        if isinstance(other_fltr, dict):
            fltr.update(other_fltr)

        data = self.coll.find(filter=fltr,
                              skip=skip,
                              limit=limit,
                              )
        return [SWAAsset(**info) for info in data]

    def check_updates(self):
        """
        swautomatic > asset > ISWAAssets.`check_updates()`
        --------------------------------------------------
        Checks for updates of the assets and mods, and updates the database
        accordingly. It uses the `steam_api_data()` method.
        """

        count = 0
        ids = self.list_assets_db()
        data_steam = steam_api_data(ids)

        projection = {'_id': False, 'steamid': True,
                      'time_local': True, 'is_installed': True}
        asset_times = {asset['steamid']: (asset['time_local'], asset['is_installed'])
                       for asset in self.coll.find({}, projection=projection)}

        bulk = []
        for key, value in data_steam.items():
            time_updated_local, is_installed = asset_times.get(int(key), (DFLT_DATE, False))
            if time_updated_local is None:
                time_updated_local = DFLT_DATE
            time_updated_steam = value.get('time_updated', DFLT_DATE)
            need_update = time_updated_local < time_updated_steam and is_installed
            bulk.append(UpdateOne({'steamid': int(key)},
                                    {'$set': {
                                        'time_updated': time_updated_steam,
                                        'need_update': need_update
                                    }}))
        if bulk:
            count = self.coll.bulk_write(bulk).modified_count
            _logger.info('Updated %s assets', count)
        return CommonResult(message=f'{count} updates were found.')

    def list_assets_db(self) -> set[int]:
        """
        swautomatic > asset > ISWAAssets.`list_assets_db()`
        ---------------------------------------------------
        Returns a set of Steam IDs of assets stored in the database.

        Return
        ------
        A set of Steam IDs.
        """

        data = self.coll.find({}, projection={'steamid': True})
        if not data:
            return set([0])
        return set(int(asset['steamid']) for asset in data)

    def list_assets_remote(self) -> set[int]:
        """
        swautomatic > asset > ISWAAssets.`list_assets_remote()`
        -------------------------------------------------------
        Returns a set of Steam IDs of assets stored in the user's Steam
        favorites.

        Return
        ------
        A set of Steam IDs.
        """

        i = 1
        msg = 'None'
        items = []
        params = {'browsefilter': 'myfavorites',
                  'sortmethod': 'alpha',
                  'section': 'items',
                  'appid': _settings.appid,
                  'p': 1,
                  'numperpage': 30}

        with rq.Session() as session:
            while str(msg) == 'None':
                params.update({'p': i})
                try:
                    req = session.get(str(_settings.user_favs_url),
                                      params=params,
                                      timeout=_settings.timeout
                                      )
                    req.raise_for_status()
                except rq.exceptions.RequestException as error:
                    _logger.error(str(error))
                    return set()
                soup = bs(req.content, 'html.parser')
                msg = soup.find('div', 'inventory_msg_content')
                divs = soup.find_all('div', 'workshopItem')
                items.extend([int(
                    div.find('a').attrs['data-publishedfileid']
                ) for div in divs])
                i += 1

        asset_ids = set(items)
        return asset_ids

    def list_assets_local(self) -> set[int]:
        """
        swautomatic > asset > ISWAAssets.`list_assets_local()`
        ------------------------------------------------------
        Returns a set of Steam IDs of installed assets and mods on the
        local machine.

        Return
        ------
        A set of Steam IDs.
        """

        asset_ids = set()
        mod_ids = set()

        for entry in os.scandir(_settings.assets_path):
            if entry.is_dir() and entry.name.isdigit():
                asset_ids.add(int(entry.name))

        for entry in os.scandir(_settings.mods_path):
            if entry.is_dir() and entry.name.isdigit():
                mod_ids.add(int(entry.name))

        return asset_ids.union(mod_ids)

    def delete_assets(self, asset_ids: Optional[list[int]| set[int]] = None,
                      session = None):
        """
        swautomatic > asset > ISWAAssets.`delete_assets()`
        --------------------------------------------------
        Deletes assets from the database based on the provided asset IDs.
        It also removes the corresponding old previews associated with the
        deleted assets. If `asset_ids` is None then all assets will be
        deleted.

        Return
        ------
        ~results.`DeleteResult`.
        """

        size = 0
        if not asset_ids:
            asset_ids = self.list_assets_local()
        # Deleting records
        count = self.coll.delete_many(
            {'steamid': {'$in': list(asset_ids)}},
            session=session
        ).deleted_count
        # Deleting files & previews
        if count:
            self.remove_previews(asset_ids)
            for asset_id in asset_ids:
                asset_path = os.path.join(_settings.assets_path, str(asset_id))
                mod_path = os.path.join(_settings.mods_path, str(asset_id))
                if os.path.exists(asset_path):
                    size += get_directory_size(asset_path)
                    delete_directory(asset_path)
                    _logger.info('Asset %s removed. Path: %s', asset_id, asset_path)
                elif os.path.exists(mod_path):
                    delete_directory(mod_path)
                    size += get_directory_size(mod_path)
                    _logger.info('Asset %s removed. Path: %s', asset_id, asset_path)
            _logger.info('Total size of deleted assets: %s', size)
        result = DeleteResult(
            message=f'Deleted {count} assets, with total size {get_size_format(size)}',
            count=count,
            size=size)
        _logger.info(result.message)
        return result

    def update_assets(self, asset_ids: Optional[list[int]| set[int]] = None,
                      session = None):
        """
        swautomatic > asset > ISWAAssets.`update_assets()`
        --------------------------------------------------
        Updates assets in the database based on the provided asset IDs. It
        retrieves the updated data from the Steam API and sends it to the
        database.

        Parameters
        ----------
        -   `asset_ids` (list or set): The IDs of the assets to update.
        -   `session` (~pymongo.`Session`): The database session to use for
            updating the assets. (optional, default `None`).

        Return
        ------
        The number of assets that were updated, rtype: `int`.
        """

        updated_count = 0
        if asset_ids:
            data = info_steam(list(asset_ids))
            for item in data.values():
                asset = SWAAsset(**item)
                asset.send_to_db(session=session)
                _logger.info('Updated asset: %s', asset)

                if not asset.preview.downloaded():
                    _logger.info('Downloading preview for asset: %s', asset)
                    asset.preview.download()
                updated_count += 1

        _logger.info('Updated %s assets in the database', updated_count)
        return updated_count

    def insert_assets(self,
                      asset_ids: Optional[list[int]| set[int]] = None,
                      session=None):
        """
        swautomatic > asset > ISWAAssets.`insert_assets()`
        --------------------------------------------------
        Inserts new assets into the database based on the provided asset
        IDs. It retrieves the asset data from the Steam API and inserts it
        into the database collection.
        """

        inserted_count = 0
        if asset_ids:
            new_data = info_steam(list(asset_ids))
            inserted_count = len(self.coll.insert_many(
                list(new_data.values()), session=session).inserted_ids)
            for item in new_data.values():
                item.pop('steamid')
                asset = SWAAsset(**item)
                asset.preview.download()
        _logger.info('Inserted %s assets to database', inserted_count)
        return inserted_count

    def remove_previews(self, asset_ids: Optional[list[int] | set[int]] = None):
        """
        swautomatic > asset > ISWAAssets.`remove_previews()`
        ----------------------------------------------------
        Removes the old previews associated with the specified asset IDs.
        It searches for files in the previews directory that contain the
        asset IDs and deletes those files.
        """

        if not asset_ids:
            asset_ids = self.list_assets_local()
        previews_dir = os.listdir(_settings.previews_path)
        for asset_id in asset_ids:
            files = [os.path.join(str(_settings.previews_path), file)
                     for file in previews_dir if str(asset_id) in file]
            for file in files:
                os.remove(file)
            _logger.info('Deleted assets ID %s to database', asset_id)

    def download_assets(self,
                        asset_ids: list[int] | set[int],
                        skip: int = 0,
                        limit: int = 0) -> list:
        """
        swautomatic > asset > ISWAAssets.`update_asset()`
        -------------------------------------------------
        If the preview is not downloaded downloads it, updates the asset.

        Parameters
        ----------
        -   `asset_ids` (list[int] or set[int]): desc;
        -   `skip` (int): desc;
        -   `limit` (int): desc.

        Return
        ------
        A list of Steam ID with errors.
        """

        errors = []
        assets = self.get_assets(steam_ids=asset_ids, skip=skip, limit=limit)
        for asset in assets:
            if not asset.preview.downloaded():
                asset.preview.download()
            if asset.need_update:
                status = asset.download()
                if status:
                    _logger.info('Installed asset with ID %s', asset.steamid)
                else:
                    errors.append(asset.steamid)
                    _logger.warning('Asset with ID %s cannot be intalled',
                                    asset.steamid)
        return errors

    def count_assets(self, **kwargs) -> int:
        """
        swautomatic > asset > ISWAAssets.`count_assets()`
        -------------------------------------------------
        Counts assets in the database by given filter.
        
        Parameters
        ----------
        -   `steam_ids` (optional, default `None`): a list of assets steam ids.
        -   `tag` (optional, default `None`): desc.
        -   `need_update` (optional, default `None`): desc.
        -   `is_installed` (optional, default `None`): desc.
        -   `other_fltr` (optional, default `None`): a dict used as a filter
            for Mongo request.

        Return
        ------
        -   `int`: Number of assets in the database.
        """

        fltr = {}
        steam_ids = kwargs.get('steam_ids', None)
        tag = kwargs.get('tag', None)
        need_update = kwargs.get('need_update', None)
        is_installed = kwargs.get('is_installed', None)
        other_fltr = kwargs.get('other_fltr', None)

        if isinstance(steam_ids, (list, set)):
            fltr.update({'steamid': {'$in': steam_ids}})
        if isinstance(tag, str):
            fltr.update({'tags': tag})
        if isinstance(need_update, bool):
            fltr.update({'need_update': need_update})
        if isinstance(is_installed, bool):
            fltr.update({'is_installed': is_installed})
        if isinstance(other_fltr, dict):
            fltr.update(other_fltr)
        return self.coll.count_documents(fltr)
