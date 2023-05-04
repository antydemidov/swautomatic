"""## Swautomatic > `SWA_api`
Here must be the docstring

### Classes:
- SWAObject: The main object of Swautomatic project.
- SWAAsset: The object representing assets.
- SWATag: This is the minimal object describing tag of any asset.
- SWAAuthor: The object describing the author of any asset.
- SWAPreview: The object describing the preview of any asset.
"""

import os
import re
from datetime import datetime
from typing import Any
from urllib.request import urlopen
from zipfile import ZipFile

import requests as rq
from bs4 import BeautifulSoup as bs
from jsonschema import validate
from PIL import Image, UnidentifiedImageError
from pymongo import UpdateOne

from connection import assets_coll, client, settings, tags_coll
from models import swa_asset_schema, swa_author_schema
from results import CommonResult
from utils import get_author_data, get_directory_size, get_size_format

__version__ = 'v0.0.1'
__author__ = 'Anton Demidov | @antydemidov'

url_parts = ['cw03361255710','cw85745255710','ca40929255710','ci03361255710']
base_links = [f'https://cdn.ggntw.com/{i}/' for i in url_parts] + [
    f'https://cdn.steamworkshopdownloader.ru/{i}/' for i in url_parts] + [
        'http://workshop.abcvg.info/archive/255710/'] + [
            f'http://workshop{i+1}.abcvg.info/archive/255710/' for i in range(9)]

DFLT_DATE = datetime.fromordinal(1)

class SWAObject:
    """## Swautomatic > SWA_api > `SWAObject`
    The main object of Swautomatic project.

    ### Attributes
    - `client` (pymongo.MongoClient): desc
    - `settings` (SWASettings): desc

    ### Methods
    - `get_asset()`: desc
    - `get_statistics()`: The method returns a CommonResult object that
    contains the retrieved statistics"""

    def __init__(self):
        self.client = client
        self.settings = settings

    def get_asset(self, steam_id: int):
        """### Swautomatic > SWA_api > SWAObject.`get_asset()`
        Returns SWAAsset

        ### Parameters:
        - steam_id (int): an asset steamid."""
        return SWAAsset(steam_id, swa_object=self)

    def get_assets(self, steam_ids: list | None = None, skip: int = 0, limit: int = 0):
        """### Swautomatic > SWA_api > SWAObject.`get_assets()`

        Bulk getter of `~swautomatic.SWA_api.SWAAsset`.

        !!! It works only with assets in database. Assets which not exists
        will be empty.

        ### Example:
        >>> swa_object = SWAObject()
        >>> swa_object.get_assets([123, 321])
        ... [SWAAsset(asset_id=123), SWAAsset(asset_id=321)]

        ### Parameters:
        - steam_ids: `list` - a list of assets steam ids;
        - skip: `int` - a number of records to skip;
        - limit: `int` - a number of records to show."""

        if not steam_ids:
            data = assets_coll.find({}, skip=skip, limit=limit)
        else:
            data = assets_coll.find({'steamid': {'$in': steam_ids}},
                                    skip=skip, limit=limit)
        return [SWAAsset(swa_object=self, **info) for info in data]

    def get_statistics(self):
        """### Swautomatic > SWA_api > SWAObject.`get_statistics()`
        The method returns a CommonResult object that contains the retrieved
        statistics.

        #### Attributes
        - `count`: an integer value that represents the total number of assets
        in the database.
        - `count_by_tag`: a list of dictionaries that contains information
        about the count of assets by tag. Each dictionary in the list includes
        the following attributes:
            - `tag_id`: a unique identifier of the tag.
            - `tag_name`: a string value that represents the name of the tag.
            - `count`: an integer value that represents the count of assets
            that have the tag.
        - `installed`: an integer value that represents the count of installed
        assets.
        - `not_installed`: an integer value that represents the count of not
        installed assets.

        #### Return
        - `CommonResult` with data about database:
            - `count` (int): desc;
            - `count_by_tag` (list): desc;
            - `installed` (int): desc;
            - `not_installed` (int): desc;
            - `assets_size` (int): desc;
            - `mods_size` (int): desc;
            - `total_size` (int): desc."""

        # Add an aggregation here, now it has a loop with a lot of tags
        count = assets_coll.count_documents({})
        tags = {tag['_id']: tag['tag'] for tag in tags_coll.find({})}

        stats = []
        for key, value in tags.items():
            stat = {
                'tag_id': key,
                'tag_name': value,
                'count': assets_coll.count_documents({'tags': key})
            }
            stats.append(stat)

        installed = assets_coll.count_documents(
            {'is_installed': True})
        not_installed = assets_coll.count_documents(
            {'is_installed': False})

        assets_size = get_directory_size(settings.assets_path)
        mods_size = get_directory_size(settings.mods_path)
        total_size = assets_size + mods_size

        return CommonResult(count=count,
                            count_by_tag=stats,
                            installed=installed,
                            not_installed=not_installed,
                            assets_size=get_size_format(assets_size),
                            mods_size=get_size_format(mods_size),
                            total_size=get_size_format(total_size))

    def close(self):
        """### Swautomatic > SWA_api > SWAObject.`close()`
        Closes the database client."""
        self.client.close()

    # UPDATE
    def update_tags(self):
        """### Swautomatic > SWA_api > SWAObject.`update_tags()`
        Update the tags from Steam Community deleting all docs
        in collection before updating.

        #### Return
        Nothing"""

        with rq.get('https://steamcommunity.com/app/255710/workshop/',
                    timeout=settings.timeout) as req:
            soup = bs(req.content)
        tags_at_steam = []
        tags_in_db = [tag['tag'] for tag in tags_coll.find({})]
        tags_soup = soup.find_all('label', 'tag_label')
        if len(tags_soup) != 0:
            for tag in tags_soup:
                tags_at_steam.append(
                    ' '.join(re.findall(r'\S+', tag.text)[:-1]))
        data = []
        tags_to_del = list(set(tags_in_db) - set(tags_at_steam))
        tags_to_upd = list(set(tags_at_steam) - set(tags_in_db))

        if tags_to_del:
            tags_coll.delete_many({'tag': {'$in': tags_to_del}})
        if tags_to_upd:
            data = [{'tag': tag} for tag in tags_to_upd]
            data.append({'tag': 'No tags'})
            for doc in data:
                try:
                    tags_coll.insert_one(doc)
                except:
                    pass

        if tags_to_upd:
            status = 'Done'
            status_bool = True
        else:
            status = 'Tags not found'
            status_bool = False

        return CommonResult(status=status,
                            status_bool=status_bool,
                            data=data,
                            deleted_tags=tags_to_del,
                            inserted_tags=tags_to_upd)

    @staticmethod
    def steam_api_data(ids: list) -> dict[str, dict]:
        """### Swautomatic > SWA_api > SWAObject.`steam_api_data()`
        Returns data about assets and mods from Steam API.

        #### Return
        - `dict`: desc"""

        post_data = {'itemcount': len(ids)}
        post_data.update(
            {f'publishedfileids[{i}]': ids[i] for i in range(len(ids))})
        post_data.update({'format': 'json'})

        try:
            with rq.post(settings.steam_api_url, data=post_data,
                         timeout=settings.longtimeout) as req:
                data = req.json()['response']['publishedfiledetails']
        except (ValueError, KeyError):
            data = []

        result = {
            item['publishedfileid']: {
                field: datetime.fromtimestamp(item[field]) if 'time' in field
                else item[field] for field in settings.needed_fields if field
                in item
            } for item in data
        }
        return result

    def check_updates(self):
        """### Swautomatic > SWA_api > SWAObject.`check_updates()`
        This method doesn't return anything. Checks updates of
        the assets and mods. Updates the database. Uses
        `~swautomatic.SWA_api.SWAObject.steam_api_data().`

        #### Return
        Nothing."""

        ids = [id['steamid'] for id in assets_coll.find(
            {}, projection={'_id': False, 'steamid': True})]
        data_steam = self.steam_api_data(ids)

        projection = {'_id': False, 'steamid': True, 'time_local': True}
        asset_times = {
            asset['steamid']: asset['time_local'] for asset in assets_coll.find(
                {}, projection=projection)
        }

        bulk = []
        for key, value in data_steam.items():
            time_updated_local = asset_times.get(int(key), DFLT_DATE)
            if time_updated_local == None:
                time_updated_local = DFLT_DATE
            time_updated_steam = value.get('time_updated', DFLT_DATE)
            if time_updated_local < time_updated_steam:
                bulk.append(UpdateOne({'steamid': int(key)},
                                      {'$set': {
                                          'time_updated': time_updated_steam,
                                          'need_update': True
                                      }}))
        if bulk:
            assets_coll.bulk_write(bulk)

    def info_steam(self, ids: list):
        """### Swautomatic > SWA_api > SWAObject.`info_steam()`
        Returns the formated dictionary with the data from Steam. It uses
        `~swautomatic.SWA_api.SWAObject.steam_api_data()`.

        #### Return
        - `dict`: desc."""

        data = {}
        steam_data = self.steam_api_data(ids)
        for key, value in steam_data.items():
            steam_id = int(key)
            steam_id_from_steam = value.get('publishedfileid', 0)
            if steam_id_from_steam:
                # === steamid ===
                steam_id = int(steam_id_from_steam)

                # === name ===
                name = value.get('title', None)
                # TODO: Add an errors catcher. Closes #14

                # === tags ===
                workshop_tags: list = value.get('tags', [])
                tags = None
                if workshop_tags:
                    tags = [workshop_tag['tag'] for workshop_tag in
                            workshop_tags if workshop_tag is not None]
                # TODO: Add an errors catcher. Closes #14

                # === preview ===
                preview_url = value.get('preview_url')

                # === path ===
                if 'Mod' in workshop_tags:
                    path = os.path.join(settings.mods_path, str(steam_id))
                else:
                    path = os.path.join(settings.assets_path, str(steam_id))

                # === is_installed ===
                is_installed = self.installed(steam_id)

                # === time_local ===
                time_local = DFLT_DATE
                if is_installed:
                    time_local = datetime.fromtimestamp(os.path.getmtime(path))
                else:
                    time_local = DFLT_DATE
                file_size: int = value.get('file_size', 0)
                time_created = value.get('time_created', DFLT_DATE)
                time_updated = value.get('time_updated', DFLT_DATE)
                # TODO: Add an errors catcher. Closes #14

                # === author ===
                author = get_author_data(value['creator'])

                # === need_update ===
                need_update = False
                if is_installed and (time_local < time_updated):
                    need_update = True

                data.update({
                    steam_id: {
                        'steamid': steam_id,
                        'name': name,
                        'tags': tags,
                        'preview_url': preview_url,
                        'path': path,
                        'is_installed': is_installed,
                        'time_local': time_local,
                        'file_size': file_size,
                        'time_created': time_created,
                        'time_updated': time_updated,
                        'author': author,
                        'need_update': need_update,
                    }})

        return data

    # async def download_preview(asset_id):
    #     asset = SWAAsset(asset_id)
    #     await asset.download_preview()

    @staticmethod
    def ids_database() -> set[int]:
        """### Swautomatic > SWA_api > SWAObject.`ids_database()`
        Returns all ids in database.

        #### Return
        - `set` of assets' Steam IDs from the database."""
        return set(int(asset['steamid']) for asset in assets_coll.find(
            {}, projection={'steamid': True}))

    def ids_steam(self) -> set[int]:
        """### Swautomatic > SWA_api > SWAObject.`ids_steam()`
        Returns a dictionary of all published file IDs, titles, hrefs, and
        preview sources associated with a user's Steam account. Uses the
        Requests and BeautifulSoup libraries to scrape the user's favorites
        page on Steam, using the settings defined in the `params` variable.
        Iterates through pages of results until no more items are found.
        Returns a CommonResult object with details on the status of the
        operation, the number of items found, and a dictionary of the items
        and their associated data.

        #### Return
        - `set` of assets' Steam IDs from Steam Favourites."""

        i = 1
        msg = 'None'
        items = []
        params = {'browsefilter': 'myfavorites',
                  'sortmethod': 'alpha',
                  'section': 'items',
                  'appid': settings.appid,
                  'p': 1,
                  'numperpage': 30}

        with rq.Session() as session:
            while str(msg) == 'None':
                params.update({'p': i})
                try:
                    req = session.get(settings.user_favs_url,
                                      params=params, timeout=settings.timeout)
                    req.raise_for_status()
                except rq.exceptions.RequestException as error:
                    print(f'{str(error)}')
                    return set()
                soup = bs(req.content, 'html.parser')
                msg = soup.find('div', 'inventory_msg_content')
                divs = soup.find_all('div', 'workshopItem')
                items += (int(div.find('a').attrs['data-publishedfileid']) for div in divs)
                i += 1

        asset_ids = set(items)
        return asset_ids

    def ids_local(self) -> set[int]:
        """### Swautomatic > SWA_api > SWAObject.`ids_local()`
        Returns already installed steam IDs of assets and mods.

        #### Return
        - `set` of installed assets' Steam IDs."""

        asset_ids = set(int(steamid) for steamid in os.listdir(
            settings.assets_path) if steamid.isdigit())
        mod_ids = set(int(steamid) for steamid in os.listdir(
            settings.mods_path) if steamid.isdigit())
        return asset_ids.union(mod_ids)

    def reload_database(self):
        """### Swautomatic > SWA_api > SWAObject.`reload_database()`
        Deletes all records in assets collection in the database and collects
        them again. Deletes all previews and downloads them.

        #### Result
        - `dict`
            - size (int): sum of assets' sizes;
            - assets_count (int): count of installed assets;
            - preview_count (int): count of downloaded previews."""
        ids_local = self.ids_local()
        ids_steam = self.ids_steam()
        ids_to_update = ids_local | ids_steam

        # Remove all records in the database
        assets_coll.delete_many({})
        # Remove all previews
        preview_files = os.listdir(settings.previews_path)
        for preview_file in preview_files:
            os.remove(os.path.join(settings.previews_path, preview_file))
        # Download data for local and steam assets
        data = self.info_steam(list(ids_to_update))
        result = {
            'size': 0,
            'assets_count': 0,
            'preview_count': 0,
        }
        # ADD LOGGING HERE TODO: #18
        for steamid, info in data.items():
            asset = SWAAsset(steamid, self, **info)
            asset.send_to_db()
            # Write the asset to database
            status = asset.download()
            # Download preview for these assets
            if status:
                result['assets_count'] += 1
                preview_size = asset.preview.download()
                if preview_size:
                    result['size'] += preview_size
                    result['preview_count'] += 1

        return result

    def update_database(self):
        """### Swautomatic > SWA_api > SWAObject.`update_database()`
        Updates the database with new or deleted Steam Workshop items.

        Retrieves a list of Steam Workshop IDs from the user's favorites and
        compares it to the list of IDs already stored in the database. Deletes
        any IDs in the database that are not in the user's favorites, and adds
        any new IDs to the database. Also downloads preview images for any new
        items. Returns a `CommonResult` object containing information about the
        update, including the number of items deleted, inserted, and updated,
        and a list of the new items added.

        #### Returns:
            A `CommonResult` object containing information about the update."""

        ids_steam = self.ids_steam()
        ids_database = self.ids_database()
        ids_local = self.ids_local()

        ids_to_delete = (ids_local | ids_database) - ids_steam
        ids_to_insert = ids_steam - (ids_database | ids_local)
        ids_to_update = ids_database
        deleted_count = 0
        inserted_count = 0

        # DELETE
        if ids_to_delete:
            deleted_count = assets_coll.delete_many({
                'steamid': {'$in': ids_to_delete}
            }).deleted_count
            # Removing old previews
            previews_dir = os.listdir(settings.previews_path)
            for id_to_delete in ids_to_delete:
                files = [os.path.join(self.settings.previews_path, file)
                         for file in previews_dir if str(id_to_delete) in file]
                for file in files:
                    os.remove(file)
        # result = await assets_coll.delete_many(
        #     {'steamid': {'$in': list(ids_to_delete)}}
        # )
        # deleted_count = result.deleted_count

        # UPDATE
        updated_count = 0
        if ids_to_update:
            data = self.info_steam(list(ids_to_update))
            for key, value in data.items():
                value.pop('steamid')
                asset = SWAAsset(key, self, **value)
                asset.send_to_db()
                updated_count += 1

        # INSERT
        if ids_to_insert:
            new_data = self.info_steam(list(ids_to_insert))
            inserted_count = len(assets_coll.insert_many(
                list(new_data.values())).inserted_ids)
        # result = await assets_coll.insert_many(list(new_data.values()))
        # inserted_count = len(result.inserted_ids)
        for id_to_insert in ids_to_insert:
            asset = SWAAsset(id_to_insert, swa_object=self)
            asset.preview.download()
        # Download previews asynchronously
        # tasks = [download_preview(asset_id) for asset_id in ids_to_update]
        # await asyncio.gather(*tasks)

        return CommonResult(status='Done',
                            status_bool=True,
                            deleted_count=deleted_count,
                            inserted_count=inserted_count,
                            updated_count=updated_count,
                            new_items=list(ids_to_insert))

    def installed(self, steam_id):
        """### Swautomatic > SWA_api > SWAObject.`installed()`
        This method takes a `steam_id` as input and returns a boolean value
        indicating whether the corresponding asset or mod is installed on the
        local machine.

        #### Return
        - `bool` representating installed asset or not installed."""

        asset_path = os.path.join(settings.assets_path, str(steam_id))
        mod_path = os.path.join(settings.mods_path, str(steam_id))

        try:
            is_installed = os.path.exists(asset_path) or os.path.exists(mod_path)
        except OSError:
            is_installed = False

        return is_installed


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

    - `info_database(self)`
    Retrieves metadata about the asset from the local database using the
    `find_one()` method of the `assets_coll` collection. Returns a dictionary
    containing the metadata or `None` if the asset is not found in the database.

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
    `settings.assets_path` or `settings.mods_path`. Returns `True` if the asset is
    installed, `False` otherwise.

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

    def __init__(self, steamid, swa_object: SWAObject, **kwargs):
        self.steamid = int(steamid)
        self.swa_object = swa_object
        info = self.get_info() if not kwargs else kwargs
        if info is None:
            raise TypeError(
                f"""There is no asset with ID {steamid} or the app can not
                find it.""")
        self.name: str | None = info.get('name')
        data = info.get('tags')
        if data is not None:
            self.tags: list[SWATag] | None = [SWATag(x) for x in data]
        else:
            self.tags = [SWATag('No tags')]
        self.preview: SWAPreview = SWAPreview(
            steam_id=steamid,
            preview_url=info.get('preview_url', ''))
        self.is_installed: bool = info.get('is_installed', False)
        self.file_size: int = info.get('file_size', 0)
        time_created: datetime = info.get('time_created', DFLT_DATE)
        if not time_created:
            time_created = DFLT_DATE
        self.time_created = time_created
        time_updated: datetime = info.get('time_updated', DFLT_DATE)
        if not time_updated:
            time_updated = DFLT_DATE
        self.time_updated = time_updated
        data = info.get('author')
        self.author: SWAAuthor | None = SWAAuthor(
            **data) if data is not None else None
        self.need_update: bool = info.get('need_update', False)
        self.type = 'asset'
        if self.tags is None:
            self.type = 'asset'
        else:
            for tag in self.tags:
                if tag.tag == 'Mod':
                    self.type = 'mod'
        if self.type == 'asset':
            self.path: str = os.path.abspath(
                os.path.join(settings.assets_path, str(steamid)))
        else:
            self.path: str = os.path.abspath(
                os.path.join(settings.mods_path, str(steamid)))
        time_local: datetime = info.get('time_local', DFLT_DATE)
        if not time_local:
            time_local = DFLT_DATE
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

    def send_to_db(self):
        """### Swautomatic > SWA_api > SWAAsset.`send_to_db()`
        Sends the record to the database. If the record exists updates it, else
        inserts the new record to the database.

        #### Return
        `None`"""
        data = self.to_dict()
        assets_coll.update_one(filter={'steamid': data['steamid']},
                               update={'$set': data},
                               upsert=True)

    def update_record(self):
        """### Swautomatic > SWA_api > SWAAsset.`update_record()`
        Desc"""
        data = self.swa_object.info_steam([self.steamid])[self.steamid]
        data.pop('steamid')
        SWAAsset(self.steamid, self.swa_object, **data).send_to_db()

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

        #### Returns:
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
            if (url_headers.get('Content-Type').split(' ')[0] in filetypes and
                int(url_headers.get('Content-Length', 0)) >= 10000
                ):
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
        except OSError:
            status = False

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


class SWATag:
    """## Swautomatic > SWA_api > `SWATag`
    Simple class storing id and name of the tag

    ### Attributes
    - `tag` (str): desc."""

    def __init__(self, tag):
        self.tag = tag
        data = tags_coll.find_one({'tag': tag})
        try:
            self.tag = data['tag']
        except TypeError as error:
            print(f'The tag with name = {tag} not found. {str(error)}')


class SWAAuthor:
    """## Swautomatic > SWA_api > `SWAAuthor`
    Desc

    ### Parameters:
    **kwargs (dict[str, Unknown]): the data to fill the fields of this object."""

    def __init__(self, **kwargs) -> None:
        # validate(kwargs, swa_author_schema)
        self.steam_id64: int = int(kwargs.get('steamID64', 0))
        self.steam_id: str = kwargs.get('steamID', None)
        self.avatar_icon: str = kwargs.get('avatarIcon', None)
        self.avatar_medium: str = kwargs.get('avatarMedium', None)
        self.avatar_full: str = kwargs.get('avatarFull', None)
        self.custom_url: str = kwargs.get('customURL', None)

    def to_dict(self) -> dict:
        """### Swautomatic > SWA_api > SWAAuthor.`to_dict()`
        Desc

        #### Return
        - `dict`: desc
            - `steam_id64` (int): desc;
            - `steam_id` (str): desc;
            - `avatar_icon` (str): desc;
            - `avatar_medium` (str): desc;
            - `avatar_full` (str): desc;
            - `custom_url` (str): desc."""

        return {
            'steam_id64': self.steam_id64,
            'steam_id': self.steam_id,
            'avatar_icon': self.avatar_icon,
            'avatar_medium': self.avatar_medium,
            'avatar_full': self.avatar_full,
            'custom_url': self.custom_url,
        }


class SWAPreview:
    """## Swautomatic > SWA_api > `SWAPreview`
    An object representing a preview image for a Steam Workshop item.

    ### Attributes:
    - `url` (str): The URL of the preview image.
    - `path` (str): The path to the local file where the preview image is stored.
    - `format` (str): The file format of the preview image.

    ### Methods:
    - `download()`:
    Downloads the file from `self.url`, saves it to `self.path` and checks if
    the size of the downloaded file is equal to the expected Content-Length.

    ### Parameters:
    - `steam_id` (int): The Steam Workshop ID of the item to which this preview
    image belongs.
    - `preview_url` (str): The URL of the preview image."""

    def __init__(self, steam_id: int, preview_url: str):
        self.steam_id: int = steam_id
        self.url: str = preview_url

        # THE PATH FROM DIRECTORY
        # path = None
        # for file in os.listdir(settings.previews_path):
        #     if str(steam_id) in file:
        #         path = os.path.join(settings.app_path,
        #                             settings.previews_path, file)

        # # THE PATH FROM STEAM
        # if path is None:
        #     headers = None
        #     try:
        #         with rq.head(preview_url, timeout=settings.timeout) as req:
        #             headers = req.headers
        #             req.raise_for_status()
        #     except rq.exceptions.HTTPError:
        #         # TODO: Add an errors catcher. Closes #14
        #         pass
        #     pic_format = None
        #     if (headers is not None and 'Content-Type' in headers):
        #         pattern = re.compile(r'.+/|\s.+')
        #         pic_format = pattern.sub('', headers['Content-Type'])
        #     if pic_format not in ['png', 'jpg', 'jpeg']:
        #         pic_format = 'png'

        #     path = os.path.join(settings.app_path, settings.previews_path,
        #                         f'{self.steam_id}.{pic_format}')

        # self.path = path

    def to_dict(self):
        """### Swautomatic > SWA_api > SWAPreview.`to_dict()`
        Returns a dict for database.

        #### Return
        - `dict` desc."""
        return {'preview_url': self.url}

    def download(self) -> int:
        """### Swautomatic > SWA_api > SWAPreview.`download()`
        Downloads the file from `self.url`, saves it to `self.path` and checks
        if the size of the downloaded file is equal to the expected
        Content-Length. If successful, returns a `CommonResult` object
        with `status` 'Done', `status_bool` True, the `size` of the file,
        and the expected content length. Otherwise, returns a `CommonResult`
        object with `status` 'Error', `status_bool` False, `size` 0, and the
        expected content length.

        #### Returns:
        - [old] `CommonResult`: An object containing the `status` and `status_bool`
        of the download, as well as the `size` and `content_length` of the
        downloaded file.
        - `int`: a number of bytes."""
        # consider handling cases where the download fails
        #
        # Use a thread pool: If you need to download multiple preview images,
        # you could use a thread pool to download them concurrently. This would
        # make better use of the available network bandwidth and improve overall
        # download speed. The concurrent.futures module provides a
        # ThreadPoolExecutor class that you could use for this.
        #
        # Use asynchronous I/O: If you're downloading a large number of preview
        # images, using asynchronous I/O could be more efficient than using a
        # thread pool. You could use a library like asyncio to implement this.

        try:
            img = Image.open(urlopen(self.url))
            if min(img.size) > 512:
                ratio = 512 / min(img.size)
                width, height = img.size
                img = img.resize(
                    size=(int(width * ratio), int(height * ratio)))
            path = os.path.join(settings.app_path, settings.previews_path,
                                f'{self.steam_id}.{img.format.lower()}')
            img.save(path, optimize=True)
            img.close()

            return os.path.getsize(path)

        except FileNotFoundError as error:
            # Log
            # FileNotFoundError – If the file cannot be found.
            # PIL.UnidentifiedImageError – If the image cannot be opened and identified.
            # ValueError – If the mode is not “r”, or if a StringIO instance is used for fp.
            # TypeError – If formats is not None, a list or a tuple.
            print(error)
        except ValueError as error:
            # Log
            print(error)
        except TypeError as error:
            # Log
            print(error)
        except UnidentifiedImageError as error:
            # Log
            print(error)
        return 0
        # with rq.get(self.url, timeout=settings.timeout) as req:
        #     if req.status_code == 200:
        #         content_length = int(req.headers.get('Content-Length', 0))
        #         with open(self.path, 'wb') as file:
        #             file.write(req.content)
        # size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        # if (size == content_length and size != 0):
        #     status, status_bool = 'Done', True
        # else:
        #     status, status_bool = 'Error', False
        # return CommonResult(status=status,
        #                     status_bool=status_bool,
        #                     size=size,
        #                     content_length=content_length)
