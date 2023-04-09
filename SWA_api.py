import os
import re
# import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime

import requests as rq
from bs4 import BeautifulSoup as bs
from pymongo import UpdateOne

from connection import assets_coll, client, settings, tags_coll
from results import CommonResult
from utils import get_author_data

__author__ = 'Anton Demidov | @antydemidov'

url_parts = ['cw03361255710','cw85745255710','ca40929255710','ci03361255710']
base_links = [f'https://cdn.ggntw.com/{i}/' for i in url_parts] + [
    f'https://cdn.steamworkshopdownloader.ru/{i}/' for i in url_parts] + [
        'http://workshop.abcvg.info/archive/255710/'] + [
            f'http://workshop{i+1}.abcvg.info/archive/255710/' for i in range(9)]


class SWAObject:
    """Annotation"""
    def __init__(self):
        self.client = client

    def get_asset(self, steam_id: int):
        return SWAAsset(steam_id, swa_object=self)

    def get_statistics(self):
        """
        The method returns a CommonResult object that contains the retrieved statistics.

        ### Attributes
        - `count`: an integer value that represents the total number of assets in the database.
        - `count_by_tag`: a list of dictionaries that contains information about the count of assets by tag. Each dictionary in the list includes the following attributes:
            - `tag_id`: a unique identifier of the tag.
            - `tag_name`: a string value that represents the name of the tag.
            - `count`: an integer value that represents the count of assets that have the tag.
        - `installed`: an integer value that represents the count of installed assets.
        - `not_installed`: an integer value that represents the count of not installed assets.
        """
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

        return CommonResult(count=count,
                            count_by_tag=stats,
                            installed=installed,
                            not_installed=not_installed)

    def close(self):
        self.client.close()

    @staticmethod
    def ids_database():
        return [id['steamid'] for id in assets_coll.find({})]

    def ids_steam(self):
        i = 1
        msg = 'None'
        data = {}
        params = {
            'browsefilter': 'myfavorites',
            'sortmethod': 'alpha',
            'section': 'items',
            'appid': settings.appid,
            'p': 1,
            'numperpage': 30,
        }

        with rq.Session() as session:
            while str(msg) == 'None':
                params.update({'p': i})
                req = session.get(settings.user_favs_url,
                                  params=params, timeout=settings.timeout)
                b = bs(req.content, 'html.parser')
                msg = b.find('div', 'inventory_msg_content')
                divs = b.find_all('div', 'workshopItem')
                for div in divs:
                    asset_id = int(div.find('a').attrs['data-publishedfileid'])
                    title = div.find('div', 'workshopItemTitle ellipsis').text
                    href = div.find('a').attrs['href']
                    src = div.find('img').attrs['src']
                    data.update({
                        asset_id: {
                            'title': title,
                            'href': href,
                            'preview_src': src
                        }
                    })
                i += 1
                ids = list(data.keys())
                count_items = len(ids)

        if count_items:
            status = 'Done'
            status_bool = True
        else:
            status = 'The list is empty'
            status_bool = False
        details = {
            'count_items': len(data),
            'items': data
        }

        return CommonResult(status=status,
                            status_bool=status_bool,
                            details=details,
                            count_items=count_items,
                            ids=ids,
                            data=data)

    def update_tags(self):
        """Update the tags from Steam Community deleting all docs
        in collection before updating."""
        with rq.get('https://steamcommunity.com/app/255710/workshop/', timeout=settings.timeout) as req:
            soup = bs(req.content)
        tags_at_steam = []
        tags_in_db = [tag['tag'] for tag in tags_coll.find({})]
        max_id = max([tag['_id'] for tag in tags_coll.find({})])
        tags_soup = soup.find_all('label', 'tag_label')
        if len(tags_soup) != 0:
            for tag in tags_soup:
                tags_at_steam.append(' '.join(re.findall('\S+', tag.text)[:-1]))
        data = []
        tags_to_del = list(set(tags_in_db) - set(tags_at_steam))
        tags_to_upd = list(set(tags_at_steam) - set(tags_in_db))
        i = max_id + 1
        for tag in tags_to_upd:
            data.append({'_id': i, 'tag': tag})
            i += 1
        if len(tags_to_del) > 0:
            tags_coll.delete_many({'tag': {'$in': tags_to_del}})
        if len(tags_to_upd) > 0:
            tags_coll.insert_many(data)

        for tag in tags_coll.find({}):
            count = assets_coll.count_documents({'tags': tag['_id']})
            tags_coll.update_one(
                {'_id': tag['_id']},
                {'$set': {'count': count}}
            )
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
    def steam_api_data(ids) -> dict:
        needed_fields = settings.needed_fields
        link_text = settings.steam_api_url
        if type(ids) in [str, int]:
            ids = [ids]
        post_data = {'itemcount': len(ids)}
        post_data.update(
            {f'publishedfileids[{i}]': ids[i] for i in range(len(ids))})
        post_data.update({'format': 'json'})

        try:
            with rq.post(link_text, data=post_data, timeout=settings.longtimeout) as req:
                data = req.json()['response']['publishedfiledetails']
        except (ValueError, KeyError):
            data = []

        result = {item['publishedfileid']: {field: datetime.fromtimestamp(
            item[field]) if 'time' in field else item[field] for field in needed_fields if field in item
        } for item in data}

        return result

    def check_updates(self):
        ids = [id['steamid'] for id in assets_coll.find(
            {}, projection={'_id': False, 'steamid': True})]
        data_steam = self.steam_api_data(ids)

        asset_times = {asset['steamid']: asset['time_updated'] for asset in assets_coll.find(
            {}, projection={'_id': False, 'steamid': True, 'time_updated': True})}

        bulk = []
        for key, value in data_steam.items():
            time_updated_local = asset_times.get(int(key), datetime.fromordinal(1))
            time_updated_steam = value.get('time_updated', datetime.fromordinal(1))
            if time_updated_local < time_updated_steam:
                bulk.append(UpdateOne({'steamid': int(key)},
                                      {'$set': {
                                          'time_updated': time_updated_steam,
                                          'need_update': True
                                      }}))
        if bulk:
            assets_coll.bulk_write(bulk)

        # for key, value in data_steam.items():
        #     time_updated_local = assets_coll.find_one({'steamid': int(key)})['time_updated']
        #     time_updated_steam = value['time_updated']
        #     if time_updated_local < time_updated_steam:
        #         assets_coll.update_one(
        #             {'steamid': int(key)},
        #             {'$set': {
        #                 'time_updated': time_updated_steam,
        #                 'need_update': True
        #             }})

    def info_steam(self, ids: list):
        data = {}
        steam_data = self.steam_api_data(ids)
        for key, value in steam_data.items():
            info = {}
            steamid = int(key)
            info_from_steam = value
            # === steamid ===
            if not info_from_steam.get('publishedfileid'):
                info = None
            else:
                steamid = int(info_from_steam.get('publishedfileid'))
                # info.update({'steamid': steamid})

                # === name ===
                asset_name = info_from_steam.get('title')
                if asset_name:
                    name = asset_name
                    # info.update({'name': asset_name})
                else:
                    name = None
                    # info.update({'name': None})

                # === tags ===
                workshop_tags = info_from_steam['tags']
                if workshop_tags:
                    tags = [tags_coll.find_one({'tag': workshop_tag['tag']})[
                        '_id'] for workshop_tag in workshop_tags if workshop_tag is not None]
                    # info.update({'tags': tags})
                else:
                    tags = None
                    # info.update({'tags': None})

                # === preview ===
                try:
                    preview_url = info_from_steam['preview_url']
                    with rq.head(preview_url, timeout=settings.timeout) as req:
                        pic_format = req.headers.get(
                            'Content-Type').split('/')[1]
                    if pic_format in ['jpg', 'jpeg', 'png']:
                        preview_path = ''.join(
                            ['previews/', str(steamid), '.', pic_format])
                    else:
                        preview_path = ''.join(
                            ['previews/', str(steamid), '.png'])
                    # info.update({'preview_url': preview_url})
                    # info.update({'preview_path': preview_path})
                except (KeyError, IndexError, TypeError):
                    # info.update({'preview_url': None})
                    preview_url = None
                    # info.update({'preview_path': None})
                    preview_path = None
                except Exception as e:
                    print(
                        f"An error occurred while processing preview for {steamid}: {str(e)}")
                    # info.update({'preview_url': None})
                    preview_url = None
                    # info.update({'preview_path': None})
                    preview_path = None

                # === path ===
                if 'Mod' in workshop_tags:
                    path = os.path.join(settings.mods_path, str(steamid))
                    path = f'{settings.mods_path}/{str(steamid)}'
                else:
                    path = os.path.join(settings.assets_path, str(steamid))
                    path = f'{settings.assets_path}/{str(steamid)}'
                # info.update({'path': path})

                # === is_installed ===
                is_installed = self.is_installed(steamid)
                # info.update({'is_installed': self.is_installed(steamid)})

                # === time_local ===
                if info['is_installed'] is True:
                    time_local = datetime.fromtimestamp(
                        os.path.getmtime(info['path']))
                else:
                    time_local = None
                # info.update({'time_local': time_local})
                file_size = info_from_steam['file_size']
                time_created = info_from_steam['time_created']
                time_updated = info_from_steam['time_updated']
                # info.update({
                #     'file_size': info_from_steam['file_size'],
                #     'time_created': info_from_steam['time_created'],
                #     'time_updated': info_from_steam['time_updated'],
                # })
                author = get_author_data(info_from_steam['creator'])
                # info.update({'author': get_author_data(info_from_steam['creator'])})

                # === need_update ===
                need_update = (info['is_installed'] and (
                    info['time_local'] < info['time_updated']))
                # info.update({'need_update': need_update})

                info.update({
                    'steamid': steamid,
                    'name': name,
                    'tags': tags,
                    'preview_url': preview_url,
                    'preview_path': preview_path,
                    'path': path,
                    'is_installed': is_installed,
                    'time_local': time_local,
                    'file_size': file_size,
                    'time_created': time_created,
                    'time_updated': time_updated,
                    'author': author,
                    'need_update': need_update,
                })

                # data.update({steamid: SWAAsset.from_source(**info)})
                data.update({steamid: info})
        return data

    # async def download_preview(asset_id):
    #     asset = SWAAsset(asset_id)
    #     await asset.download_preview()

    def update_database(self):
        """Updates the database with new or deleted Steam Workshop items.

        Retrieves a list of Steam Workshop IDs from the user's favorites and compares it
        to the list of IDs already stored in the database. Deletes any IDs in the database
        that are not in the user's favorites, and adds any new IDs to the database. Also
        downloads preview images for any new items. Returns a CommonResult object containing
        information about the update, including the number of items deleted, inserted, and
        updated, and a list of the new items added.

        Returns:
            A CommonResult object containing information about the update.
        """
        ids_from_favs = self.ids_steam()
        # ids_in_db = [id['steamid'] for id in list(assets_coll.find(
        #     {}, projection={'_id': False, 'steamid': True}))]

        ids_in_db = {id['steamid'] for id in assets_coll.find(
            {}, projection={'steamid': True})}

        if ids_from_favs.status_bool is True:
            ids_favs = set(getattr(ids_from_favs, 'ids'))
            ids_to_delete = ids_in_db - ids_favs
            ids_to_update = ids_favs - ids_in_db
            if ids_to_delete:
                deleted_count = assets_coll.delete_many(
                    {'steamid': {'$in': ids_to_delete}}
                ).deleted_count
                # result = await assets_coll.delete_many(
                #     {'steamid': {'$in': list(ids_to_delete)}}
                # )
                # deleted_count = result.deleted_count
            else:
                deleted_count = 0
            if ids_to_update:
                new_data = self.info_steam(list(ids_to_update))
                inserted_count = len(assets_coll.insert_many(list(new_data.values())).inserted_ids)
                # result = await assets_coll.insert_many(list(new_data.values()))
                # inserted_count = len(result.inserted_ids)
            else:
                inserted_count = 0

        for id_to_update in ids_to_update:
            asset = SWAAsset(id_to_update, swa_object=self)
            asset.download_preview()

        # Download previews asynchronously
            # tasks = [download_preview(asset_id) for asset_id in ids_to_update]
            # await asyncio.gather(*tasks)

        return CommonResult(status='Done',
                            status_bool=True,
                            deleted_count=deleted_count,
                            inserted_count=inserted_count,
                            new_items=list(ids_to_update))

    def is_installed(self, steam_id):
        """This method takes a `steam_id` as input and returns a boolean value
        indicating whether the corresponding asset or mod is installed on the
        local machine."""
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
    """
    # Class `SWAAsset`
    A class that represents a Steam Workshop asset or mod, which can be
    downloaded and installed.

    ## Attributes
    - `steamid`: an integer representing the Steam Workshop ID of the asset.
    - `info`: a dictionary containing metadata about the asset, such as its title,
    description, and tags. This attribute is initialized to `None` and is
    populated when the `get_info()` method is called.
    - `swa_object`: an instance of the SWAObject class, which provides methods
    for interacting with the Steam Web API and Steam Workshop.

    ## Methods
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

    ## Example
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
    ...         print("There was an error downloading or installing the asset.")
    """
    def __init__(self, asset_id, swa_object: SWAObject):
        self.steamid = int(asset_id)
        self.info = None
        self.swa_object = swa_object

    # REWRITE THIS CODE TO MAKE IT SMARTER
    # Avoid enumeration of attributes. Add validation with any library for validation.
    @classmethod
    def from_source(cls, swa_object: SWAObject, steamid: int, name: str, tags: list[int], preview_url: str,
                    preview_path: str, path: str, is_installed: bool, time_local: datetime,
                    file_size: int, time_created: datetime, time_updated: datetime,
                    author: dict, need_update: bool):
        """Creates a new SWAAsset instance from the given dictionary."""
        clAuthor = SWAAuthor(**author)
        clTags = [SWATag(tag) for tag in tags]

        info = {'steamid': steamid, 'name': name, 'tags': clTags, 'preview_url': preview_url,
                'preview_path': preview_path, 'path': path, 'is_installed': is_installed,
                'time_local': time_local, 'file_size': file_size, 'time_created': time_created,
                'time_updated': time_updated, 'author': clAuthor, 'need_update': need_update}
        asset = cls(steamid, swa_object=swa_object)
        asset.info = info
        # for key, value in kwargs.items():
        #     if key == 'author':
        #         asset.author = SWAAuthor(**value)
        #     elif key == 'tags':
        #         if isinstance(value, list):
        #             asset.tags = [SWATag(tag) for tag in value]
        #         else:
        #             asset.tags = [SWATag(value)]
        #     elif key == 'preview_url':
        #         asset.preview_url = SWAPreview(value, getattr(asset, 'steamid'))
        #     else:
        #         setattr(asset, key, value)

    # def to_dict(self):
    #     result = {}
    #     for key, value in self.__dict__.items():
    #         if key in ['author', 'preview_url']:
    #             result.update({key: value.__dict__})
    #         elif key == 'tags':
    #             result.update({'tags': [tag.__dict__ for tag in value]})
    #         else:
    #             result.update({key: value})
    #     return result

    def info_steam(self) -> dict:
        """It use the method from SWAObject and not duplicate code"""
        return self.swa_object.info_steam(self.steamid).get(self.steamid, None)

    def info_database(self):
        """Search info about the asset in database"""
        data = assets_coll.find_one({'steamid': self.steamid})
        # asset = SWAAsset(self.steamid, self.swa_object)
        # asset.info = data
        # return asset
        return data

    def get_info(self):
        info = self.info_database()
        if not info:
            info = self.info_steam()
        self.info = info
        status = info is not None
        return status

    def download_preview(self):
        if self.info is None:
            self.get_info()

        preview_url = self.info.preview_url
        if preview_url is None:
            return False

        if os.path.exists(self.info.preview_path):
            return True

        try:
            with rq.get(preview_url, timeout=settings.longtimeout) as req:
                req.raise_for_status()
                preview_b = req.content

            with open(self.info.preview_path, 'wb') as f:
                f.write(preview_b)

            return True

        except rq.exceptions.RequestException:
            return False

    # Strange thing
    # def update_stats_full(self):
    #     info_from_steam = self.info_steam()
    #     info_from_db = self.info_database()
    #     if (info_from_db is None and info_from_steam is False):
    #         return ValueError
    #     elif info_from_db is None:
    #         assets_coll.insert_one(info_from_steam) # FIXME:
    #     elif info_from_steam is not info_from_db:
    #         set_info_from_steam = info_from_steam.items() # FIXME:
    #         set_info_from_db = info_from_db.items() # FIXME:
    #         diff = set_info_from_steam - set_info_from_db
    #         if diff != set():
    #             assets_coll.update_one(
    #                 {'steamid': self.steamid}, {'$set': dict(diff)})

    # CHECK IF IT IS NECESSARY
    # def update_preview_path(self):
    #     if not self.info:
    #         self.get_info()

    #     try:
    #         preview_url = self.info.preview_url
    #         with rq.head(preview_url, timeout=settings.timeout) as req:
    #             pic_format = req.headers.get('Content-Type').split('/')[1]
    #         if pic_format in ['jpg', 'jpeg', 'png']:
    #             preview_path = f'previews/{self.steamid}.{pic_format}'
    #         else:
    #             preview_path = f'previews/{self.steamid}.png'

    #         result = assets_coll.update_one(
    #             {'steamid': self.steamid},
    #             {'$set': {'preview_path': preview_path}}
    #         )
    #         if result.matched_count == 1 and result.modified_count == 1:
    #             return CommonResult(
    #                 status='Preview path updated successfully.',
    #                 status_bool=True,
    #                 details=None
    #             )
    #         return CommonResult(
    #             status='Failed to update preview path.',
    #             status_bool=False,
    #             details=None
    #         )

    #     except rq.exceptions.RequestException as error:
    #         return CommonResult(
    #             status='Request failed.',
    #             status_bool=False,
    #             details=str(error)
    #         )

    #     except Exception as error:
    #         with open('errors.txt', 'a', encoding='utf-8') as file:
    #             file.write(f'{self.steamid}\n')
    #         return CommonResult(
    #             status='Failed to update preview path.',
    #             status_bool=False,
    #             details=str(error)
    #         )

    def update_preview_url(self):
        info = self.info_steam()
        if info:
            assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {'preview_url': info['preview_url']}}
            )

    def download(self) -> bool:
        """This method `download()` downloads and extracts a Steam Workshop asset
        or mod. If the asset is not installed or needs an update, it downloads
        the asset from Steam and extracts it to the appropriate folder. Finally,
        it updates the local database with the new installation time and sets
        the asset's `is_installed` flag to `True`. It returns a boolean indicating
        whether the download and extraction were successful."""
        if not self.info:
            self.get_info()

        if (self.info.is_installed is False or self.info.need_update is True):
            return True

        status = False
        path = f'{self.info.path}.zip'

        for base_link in base_links:
            url = f'{base_link}{self.steamid}.zip'
            url_headers = rq.head(url, timeout=settings.timeout)
            if (
                ContentType(url_headers.headers.get('Content-Type')).type == 'application' and
                int(url_headers.headers.get('Content-Length')) >= 10000
            ):
                # timeout for BIG requests
                with rq.get(url, stream=True, timeout=settings.longtimeout) as req:
                    with open(path, 'wb') as f:
                        f.write(req.content)
                break
            else:
                return False

        try:
            with zipfile.ZipFile(path, 'r') as zip:
                mod_tag_id = tags_coll.find_one({'tag': 'Mod'})['_id']
                asset_tags = [tag._id for tag in self.info.tags]
                extract_path = settings.mods_path if mod_tag_id in asset_tags else settings.assets_path
                zip.extractall(extract_path)

            os.remove(path)
            status = True
        except Exception:
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

    def is_installed(self):
        """Checks if the asset is installed"""
        asset_path = os.path.join(settings.assets_path, str(self.steamid))
        mod_path = os.path.join(settings.mods_path, str(self.steamid))
        return os.path.exists(asset_path) or os.path.exists(mod_path)

    # def update_is_intalled(self):
    #     """Updates status of the asset"""
    #     is_installed = self.is_installed()
    #     assets_coll.update_one(
    #         {'steamid': self.steamid},
    #         {'$set': {'is_installed': is_installed}}
    #     )

    # def update(self):
    #     """Updates the asset, downloads its zipfile and extracts it"""
    #     data = self.info_steam()
    #     assets_coll.update_one(
    #         {'steamid': self.steamid},
    #         {'$set': data}, upsert=True
    #     )

    # @classmethod
    # def from_dict(cls, info, swa_object):
    #     asset = cls(info['steamid'], swa_object)
    #     asset.info = info
    #     return asset


class ContentType:
    def __init__(self, string: str):
        if string is None:
            raise ValueError("String cannot be None")
        self.string = string
        other = []
        p = re.compile(r'\W')
        type, format, *other = p.split(string)
        self.type = type
        self.format = format
        i = 0
        params = {}
        while i in range(len(other)):
            params.update({other[i]: other[i+1]})
            setattr(self, other[i], other[i+1])
            i += 2
        self.params = params


# DATACLASSES
class SWATag:
    def __init__(self, id):
        self._id = id
        self.tag = tags_coll.find_one({'_id': id})['tag']


@dataclass
class SWAAuthor:
    steamID64: int
    steamID: str
    avatarIcon: str
    avatarMedium: str
    avatarFull: str
    customURL: str

    def __post_init__(self):
        self.steamID64 = int(self.steamID64)


class SWAPreview:
    """
    # Class: `SWAPreview`
    An object representing a preview image for a Steam Workshop item.

    ## Attributes:
    `url` (str): The URL of the preview image.
    `swa_object` (SWAObject): The SWAObject instance to which this preview image belongs.
    `path` (str): The path to the local file where the preview image is stored.
    `format` (str): The file format of the preview image.

    ## Methods:
    `__init__(self, url: str, steam_id: int, swa_object: SWAObject)`:
    Initializes a new `SWAPreview` instance with the specified parameters.

    ## Parameters:
    `url` (str): The URL of the preview image.
    `steam_id` (int): The Steam Workshop ID of the item to which this preview image belongs.
    `swa_object` (SWAObject): The SWAObject instance to which this preview image belongs.
    `download(self) -> CommonResult`:
    Downloads the file from `self.url`, saves it to `self.path` and checks if the size of the
    downloaded file is equal to the expected Content-Length.

    ## Parameters:
    None

    ## Returns:
    `CommonResult`: An object containing the status and status_bool of the download, as well
    as the size and content length of the downloaded file. If successful, `status` is
    'Done', `status_bool` is True, `size` is the size of the downloaded file, and `content_length`
    is the expected content length. Otherwise, `status` is 'Error', `status_bool` is False, `size`
    is 0, and `content_length` is the expected content length.

    ## Example:
    >>> from SWAObject import SWAObject
    ...
    ... # Initialize a new SWAObject instance
    >>> swa_object = SWAObject()
    ...
    ... # Create a new preview object for the item with Steam Workshop ID 12345
    >>> preview = SWAPreview('https://steamcommunity.com/sharedfiles/filedetails/?id=12345&preview=true', 12345, swa_object)
    ...
    ... # Download the preview image
    >>> result = preview.download()
    ...
    ... # Print the download result
    >>> print(f"Download status: {result.status}, Size: {result.size} bytes")
    """
    def __init__(self, url: str, steam_id: int, swa_object: SWAObject):
        self.url = url
        self.swa_object = swa_object
        headers = None
        try:
            with rq.head(url, timeout=settings.timeout) as req:
                headers = req.headers
                req.raise_for_status()
        except rq.exceptions.HTTPError:
            pass

        if headers is not None and 'Content-Type' in headers:
            content_type = ContentType(headers['Content-Type'])
            pic_format = content_type.format
        else:
            pic_format = 'png'

        self.path = os.path.join(settings.previews_path, f"{steam_id}.{pic_format}")
        self.format = pic_format

    def download(self):
        """Downloads the file from `self.url`, saves it to `self.path` and checks
        if the size of the downloaded file is equal to the expected
        Content-Length. If successful, returns a CommonResult object
        with `status` 'Done', `status_bool` True, the `size` of the file,
        and the expected content length. Otherwise, returns a CommonResult
        object with `status` 'Error', `status_bool` False, `size` 0, and the
        expected content length.

        ## Args:
            None

        ## Returns:
            `CommonResult`: An object containing the status and status_bool of
            the download, as well as the size and content length of the
            downloaded file.
        """
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
        with rq.get(self.url, timeout=settings.timeout) as req:
            if req.status_code == 200:
                content_length = int(req.headers.get('Content-Length'))
                with open(self.path, 'wb') as f:
                    f.write(req.content)
        size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        if (size == content_length and size != 0):
            status, status_bool = 'Done', True
        else:
            status, status_bool = 'Error', False
        return CommonResult(status=status,
                            status_bool=status_bool,
                            size=size,
                            content_length=content_length)
