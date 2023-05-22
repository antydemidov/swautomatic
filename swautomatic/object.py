"""# swautomatic > `object`

Module for class `SWAObject`.
"""

import logging
import os
import re
import shutil
from datetime import datetime
from typing import Optional

import requests as rq
from bs4 import BeautifulSoup as bs
# # from jsonschema import validate
from pymongo import UpdateOne

from .asset import SWAAsset
from .author import SWAAuthor
from .connection import _assets_coll, _client, _settings, _tags_coll
from .results import CommonResult, StatisticsResult
from .settings import DFLT_DATE
from .utils import get_directory_size, get_local_time, get_size_format

__all__ = ['SWAObject']


class SWAObject:
    """## swautomatic > object > `SWAObject`
        The main object of Swautomatic project.

    ### Attributes
        - `client` (pymongo.MongoClient): A MongoDB client object.
        - `settings` (SWASettings): An object representing Swautomatic settings.

    ### Methods
        - `get_asset()`: Retrieves a `SWAAsset` object for the specified asset
          steam ID.
        - `get_assets()`: Retrieves a list of SWAAsset objects based on the
          provided parameters.
        - `get_statistics()`: Retrieves statistics about the database and returns
          a ~results.`StatisticsResult` object.
        - `update_tags()`: Update the tags from Steam Community by deleting
          outdated documents in the collection before updating.
        - `steam_api_data()`: Returns data about assets and mods from Steam API.
        - `check_updates()`: desc.
        - `info_steam()`: desc.
        - `ids_database()`: desc.
        - `ids_steam()`: desc.
        - `ids_local()`: desc.
        - `total_reset()`: desc.
        - `update_reset()`: desc.
        - `installed()`: desc.
        - `close()`: Closes the database client.
    """

    def __init__(self):
        self.client = _client
        self.settings = _settings
        self.assets_coll = _assets_coll
        self.tags_coll = _tags_coll

    def get_asset(self, steam_id: int):
        """### swautomatic > object > SWAObject.`get_asset()`
            Retrieves a SWAAsset object for the specified asset steam ID.

        #### Parameters
            - `steam_id` (int): The steam ID of the asset.
        
        #### Return
            The SWAAsset object representing the asset.
        """
        return SWAAsset(steam_id, swa_object=self)

    def get_assets(self, steam_ids: Optional[list[int]] = None, fltr: Optional[dict] = None,
                   skip: int = 0, limit: int = 0):
        """### swautomatic > object > SWAObject.`get_assets()`

            Retrieves a list of SWAAsset objects based on the provided parameters.

            !!! It works only with assets in database. Assets which not exists
            will not be in returned list.

        #### Example::

            swa_object = SWAObject()
            swa_object.get_assets([123, 321])

        #### Parameters:
            - `steam_ids` (list): a list of assets steam ids.
            - `fltr` (dict): a dict used as a filter for Mongo request.
            - `skip` (integer): a number of records to skip.
            - `limit` (integer): a number of records to show.
        
        #### Return
            A list of SWAAsset objects.
        """

        if not fltr:
            fltr = {}
        if steam_ids:
            fltr.update({'steamid': {'$in': steam_ids}})

        data = self.assets_coll.find(filter=fltr,
                                     skip=skip,
                                     limit=limit,
                                     )
        return [SWAAsset(swa_object=self, **info) for info in data]

    def get_statistics(self):
        """### swautomatic > object > SWAObject.`get_statistics()`
            Retrieves statistics about the database and returns a CommonResult
            object.

        #### Return
            - `StatisticsResult`: The retrieved statistics including the
              following attributes:
                - `count` (int): The total number of assets in the database.
                - `count_by_tag` (list): A list of dictionaries containing
                  information about the count of assets by tag. Each dictionary
                  has the following attributes:
                    - `tag_id` (str): The unique identifier of the tag.
                    - `tag_name` (str): The name of the tag.
                    - `count` (int): The count of assets that have the tag.
                - `installed` (int): The count of installed assets.
                - `not_installed` (int): The count of not installed assets.
                - `assets_size` (str): The size of the assets directory in
                  human-readable format.
                - `mods_size` (str): The size of the mods directory in
                  human-readable format.
                - `total_size` (str): The total size of assets and mods
                  directories combined in human-readable format.
        """

        # Add an aggregation here, now it has a loop with a lot of tags
        count = self.assets_coll.count_documents({})
        tags = [tag['tag'] for tag in self.tags_coll.find({})]

        stats = {}
        for tag in tags:
            stats.update({tag: self.assets_coll.count_documents({'tags': tag})})

        installed = self.assets_coll.count_documents(
            {'is_installed': True})
        not_installed = self.assets_coll.count_documents(
            {'is_installed': False})

        assets_size = get_directory_size(self.settings.assets_path)
        mods_size = get_directory_size(self.settings.mods_path)
        total_size = assets_size + mods_size

        return StatisticsResult(count=count,
                                count_by_tag=stats,
                                installed=installed,
                                not_installed=not_installed,
                                assets_size=get_size_format(assets_size),
                                mods_size=get_size_format(mods_size),
                                total_size=get_size_format(total_size))

    # UPDATE
    def update_tags(self):
        """### swautomatic > object > SWAObject.`update_tags()`
            Update the tags from Steam Community by deleting outdated documents
            in the collection before updating.

        #### Return
            - `CommonResult`: An object containing the status of the update
              operation.

        #### Raises
            - `RequestException`: If there is an error in the HTTP request.
            - `ValueError`: If there is a value error during the execution.
        """

        try:
            response = rq.get(
                'https://steamcommunity.com/app/255710/workshop/',
                timeout=self.settings.timeout)
            soup = bs(response.content, 'html.parser')
            tags_soup = soup.find_all('label', 'tag_label')
            tags_at_steam = [' '.join(re.findall(r'\S+', tag.text)[:-1])
                             for tag in tags_soup]
            tags_in_db = [tag['tag'] for tag in self.tags_coll.find({})]

            tags_to_del = list(set(tags_in_db) - set(tags_at_steam))
            tags_to_upd = list(set(tags_at_steam) - set(tags_in_db))

            if tags_to_del:
                self.tags_coll.delete_many({'tag': {'$in': tags_to_del}})
            if tags_to_upd:
                data = [{'tag': tag} for tag in tags_to_upd]
                data.append({'tag': 'No tags'})
                self.tags_coll.insert_many(data)

            if tags_to_del or tags_to_upd:
                status = f'Done! Deleted {len(tags_to_del)} tags '
                status += f'and {len(tags_to_upd)} tags were added.'
            else:
                status = 'There are no new tags.'

            return CommonResult(status=status,
                                status_bool=True,
                                deleted_tags=tags_to_del,
                                inserted_tags=tags_to_upd,
                                )
        except (rq.RequestException, ValueError) as error:
            logging.critical('The tags could not be updated. %s', error)
            return CommonResult(status='Error',
                                status_bool=False,
                                message=str(error)
                                )

    def steam_api_data(self, ids: list[int] | set[int]) -> dict[str, dict]:
        """### swautomatic > object > SWAObject.`steam_api_data()`
            Returns data about assets and mods from Steam API.

        #### Parameters
            - `ids` (list): A list of asset IDs.

        #### Return
            A dictionary containing data about assets and mods from
            the Steam API.
        """

        ids = list(ids)
        post_data = {'itemcount': len(ids)}
        post_data.update(
            {f'publishedfileids[{i}]': ids[i] for i in range(len(ids))})
        post_data.update({'format': 'json'}) # type: ignore

        data = []
        try:
            with rq.post(self.settings.steam_api_url, data=post_data,
                         timeout=self.settings.longtimeout) as req:
                data = req.json()['response']['publishedfiledetails']
        except (ValueError, KeyError) as error:
            logging.critical('The connection was not established. %s', error)

        result = {
            item['publishedfileid']: {
                field: datetime.fromtimestamp(item[field]) if 'time' in field
                else item[field] for field in self.settings.needed_fields if field
                in item
            } for item in data
        }
        return result

    def check_updates(self):
        """### swautomatic > object > SWAObject.`check_updates()`
            Checks for updates of the assets and mods, and updates the database
            accordingly. It uses the `~.steam_api_data()` method.
        """

        ids = self.ids_database()
        data_steam = self.steam_api_data(ids)

        projection = {'_id': False, 'steamid': True, 'time_local': True}
        asset_times = {
            asset['steamid']: asset['time_local'] for asset in self.assets_coll.find(
                {}, projection=projection)
        }

        bulk = []
        for key, value in data_steam.items():
            time_updated_local = asset_times.get(int(key), DFLT_DATE)
            if time_updated_local is None:
                time_updated_local = DFLT_DATE
            time_updated_steam = value.get('time_updated', DFLT_DATE)
            if time_updated_local < time_updated_steam:
                bulk.append(UpdateOne({'steamid': int(key)},
                                      {'$set': {
                                          'time_updated': time_updated_steam,
                                          'need_update': True
                                      }}))
        if bulk:
            count = self.assets_coll.bulk_write(bulk).modified_count
            logging.info('Updated %s assets', count)

    def info_steam(self, ids: list) -> dict[int, dict]:
        """### swautomatic > object > SWAObject.`info_steam()`
            Returns the formated dictionary with the data from Steam. It uses
            `~swautomatic.SWA_api.SWAObject.steam_api_data()`.

        #### Parameters
            - `ids` (list): A list of asset IDs.

        #### Return
            A dictionary containing the formatted Steam data for the assets.
        """

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
                if name is None:
                    logging.error(
                        'Failed to retrieve name for asset with Steam ID %s',
                        steam_id)

                # === tags ===
                workshop_tags: list = value.get('tags', [])
                tags = None
                if workshop_tags:
                    try:
                        tags = [workshop_tag['tag']
                                for workshop_tag in workshop_tags if
                                workshop_tag is not None]
                    except (KeyError, TypeError) as error:
                        logging.error(
                            'Failed to retrieve tags for asset with Steam ID %s: %s',
                            steam_id, error)

                # === preview ===
                preview_url = value.get('preview_url')

                # === path ===
                if 'Mod' in workshop_tags:
                    path = os.path.join(self.settings.mods_path, str(steam_id))
                else:
                    path = os.path.join(self.settings.assets_path, str(steam_id))

                # === is_installed ===
                is_installed = os.path.exists(path)

                # === time_local ===
                time_local = get_local_time(path) if is_installed else DFLT_DATE
                file_size: int = value.get('file_size', 0)
                time_created = value.get('time_created', DFLT_DATE)
                time_updated = value.get('time_updated', DFLT_DATE)
                # TODO: Add an errors catcher. Closes #14

                # === author ===
                try:
                    author = SWAAuthor(int(value['creator'])).to_dict()
                except KeyError as error:
                    logging.error('Failed to retrieve author data for asset with\
                                   Steam ID %s: %s', steam_id, error)
                    author = None

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

    def ids_database(self) -> set[int]:
        """### swautomatic > object > SWAObject.`ids_database()`
            Returns a set of Steam IDs of assets stored in the database.

        #### Return
            A set of Steam IDs.
        """

        return set(int(asset['steamid']) for asset in self.assets_coll.find(
            {}, projection={'steamid': True}))

    def ids_steam(self) -> set[int]:
        """### swautomatic > object > SWAObject.`ids_steam()`
            Returns a set of Steam IDs of assets stored in the user's Steam
            favorites.

        #### Return
            A set of Steam IDs.
        """

        i = 1
        msg = 'None'
        items = []
        params = {'browsefilter': 'myfavorites',
                  'sortmethod': 'alpha',
                  'section': 'items',
                  'appid': self.settings.appid,
                  'p': 1,
                  'numperpage': 30}

        with rq.Session() as session:
            while str(msg) == 'None':
                params.update({'p': i})
                try:
                    req = session.get(self.settings.user_favs_url,
                                      params=params,
                                      timeout=self.settings.timeout
                                      )
                    req.raise_for_status()
                except rq.exceptions.RequestException as error:
                    logging.error(str(error))
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

    def ids_local(self) -> set[int]:
        """### swautomatic > object > SWAObject.`ids_local()`
            Returns a set of Steam IDs of installed assets and mods on the
            local machine.

        #### Return
            A set of Steam IDs.
        """

        asset_ids = set()
        mod_ids = set()

        for entry in os.scandir(self.settings.assets_path):
            if entry.is_dir() and entry.name.isdigit():
                asset_ids.add(int(entry.name))

        for entry in os.scandir(self.settings.mods_path):
            if entry.is_dir() and entry.name.isdigit():
                mod_ids.add(int(entry.name))

        return asset_ids.union(mod_ids)

    def total_reset(self):
        """### swautomatic > object > SWAObject.`total_reset()`
            DANGEROUS!!! Deletes all records in the assets collection in the
            database. Deletes all previews and assets.

        #### Result
            A dictionary containing information about the reset operation.
            - `size` (integer): sum of assets` sizes.
            - `assets_count` (integer): count of deleted assets.
            - `previews_count` (integer): count of deleted previews.
        """

        size = 0
        ids_local = self.ids_local()

        # Remove all records in the database
        self.assets_coll.delete_many({})

        # Remove all previews
        preview_files = [entry.name for entry in os.scandir(
            self.settings.previews_path) if entry.is_file() and entry.name != 'empty.jpg']
        for preview_file in preview_files:
            try:
                os.remove(os.path.join(self.settings.previews_path, preview_file))
            except OSError as error:
                logging.error(
                    'Error occurred while deleting preview file %s: %s',
                    preview_file, str(error))
        # Remove all assets
        size = self.__remove_assets(ids_local)
        assets_count = len(ids_local)
        previews_count = len(preview_files)
        logging.info(
            'Total reset: size - %s, assets_count - %s, previews_count - %s',
            size, ids_local, previews_count)
        return CommonResult(**{'size': size,
                               'assets_count': assets_count,
                               'previews_count': previews_count,
                               })

    def update_database(self):
        """### swautomatic > object > SWAObject.`update_database()`
            Updates the database by performing operations for deleting,
            updating, and inserting assets. It also downloads the previews for
            newly inserted assets. The function uses MongoDB transactions for
            ensuring data consistency.
        """

        try:
            ids_steam = self.ids_steam()
            ids_database = self.ids_database()
            ids_local = self.ids_local()
            ids_to_delete = (ids_local | ids_database) - ids_steam
            ids_to_insert = ids_steam - ids_database
            ids_to_update = ids_database

            deleted_count = self.delete_assets(ids_to_delete)
            updated_count = self.__update_assets(ids_to_update)
            inserted_count = self.__insert_assets(ids_to_insert)

            logging.info('The database updated, d: %s, u: %s, i: %s',
                         deleted_count, updated_count, inserted_count)
            return CommonResult(
                status='Done',
                status_bool=True,
                deleted_count=deleted_count,
                inserted_count=inserted_count,
                updated_count=updated_count,
                new_items=list(ids_to_insert)
            )
        except Exception as error:
            logging.critical('Updating was failed. %s', error)
            raise error

    def delete_assets(self, asset_ids, session=None):
        """### swautomatic > object > SWAObject.`__delete_assets()`
            Deletes assets from the database based on the provided asset IDs.
            It also removes the corresponding old previews associated with the
            deleted assets.
        """

        if asset_ids:
            deleted_count = self.assets_coll.delete_many(
                {'steamid': {'$in': list(asset_ids)}},
                session=session
            ).deleted_count
            if deleted_count:
                self.__remove_old_previews(asset_ids)
                self.__remove_assets(asset_ids)
            logging.info('Deleted %s assets from database', deleted_count)
            return deleted_count
        return 0

    def __update_assets(self, asset_ids, session=None):
        """### swautomatic > object > SWAObject.`__update_assets()`
            Updates assets in the database based on the provided asset IDs. It
            retrieves the updated data from the Steam API and sends it to the
            database.

        #### Parameters
            - `asset_ids` (list or set): The IDs of the assets to update.
            - `session` (~pymongo.`Session`): The database session to use for
              updating the assets. (optional, default = `None`).

        #### Return
            The number of assets that were updated, rtype: `int`.
        """

        updated_count = 0
        if asset_ids:
            data = self.info_steam(list(asset_ids))
            for key, value in data.items():
                value.pop('steamid')
                asset = SWAAsset(key, **value)
                asset.send_to_db(session=session)

                # Log the asset update
                logging.info('Updated asset: %s', asset)

                if not asset.preview.downloaded():
                    # Log the preview download
                    logging.info('Downloading preview for asset: %s', asset)
                    asset.preview.download()

                updated_count += 1

        # Log the total number of updated assets
        logging.info('Updated %s assets in the database', updated_count)

        return updated_count

    def __insert_assets(self, asset_ids, session=None):
        """### swautomatic > object > SWAObject.`__insert_assets()`
            Inserts new assets into the database based on the provided asset
            IDs. It retrieves the asset data from the Steam API and inserts it
            into the database collection.
        """

        inserted_count = 0
        if asset_ids:
            new_data = self.info_steam(list(asset_ids))
            inserted_count = len(self.assets_coll.insert_many(
                list(new_data.values()), session=session).inserted_ids)
            for key, value in new_data.items():
                value.pop('steamid')
                asset = SWAAsset(key, **value)
                asset.preview.download()
        logging.info('Inserted %s assets to database', inserted_count)
        return inserted_count

    def __remove_old_previews(self, asset_ids):
        """### swautomatic > object > SWAObject.`__remove_old_previews()`
            Removes the old previews associated with the specified asset IDs.
            It searches for files in the previews directory that contain the
            asset IDs and deletes those files.
        """

        previews_dir = os.listdir(self.settings.previews_path)
        for asset_id in asset_ids:
            files = [os.path.join(self.settings.previews_path, file)
                     for file in previews_dir if str(asset_id) in file]
            for file in files:
                os.remove(file)
            logging.info('Deleted assets ID %s to database', asset_id)

    def __remove_assets(self, asset_ids: list[int] | set[int]) -> int:
        """### swautomatic > object > SWAObject.`__remove_assets()`
            This method removes the assets specified by the provided asset IDs.
            It deletes the asset directories and returns the total size of the
            deleted assets.
        
        #### Args
        - `asset_ids` (list or set): The IDs of the assets to remove.

        #### Return
            - `int`: The size of the deleted assets.

        #### Raises:
            None
        """

        size = 0
        for asset_id in asset_ids:
            asset_path = os.path.join(self.settings.assets_path, str(asset_id))
            mod_path = os.path.join(self.settings.mods_path, str(asset_id))

            if os.path.exists(asset_path):
                size += get_directory_size(asset_path)
                self.__delete_directory(asset_path)
                logging.info('Asset %s removed. Path: %s', asset_id, asset_path)
            elif os.path.exists(mod_path):
                self.__delete_directory(mod_path)
                size += get_directory_size(mod_path)
                logging.info('Asset %s removed. Path: %s', asset_id, asset_path)
        logging.info('Total size of deleted assets: %s', size)
        return size

    def __delete_directory(self, path):
        """### swautomatic > object > SWAObject.`__delete_directory()`
            Removes the directory with given `path`.
        """
        try:
            shutil.rmtree(path)
            logging.info('Deleted directory: %s', path)
            print(f"Deleted directory: {path}")
        except OSError as error:
            logging.warning(
                'Failed to delete directory: %s Error: %s',
                path, str(error))

    def update_assets(self, asset_ids: list | set, skip: int = 0, limit: int = 0):
        """### swautomatic > object > SWAObject.`update_asset()`
            If the preview is not downloaded downloads it, updates the asset.
        """
        assets = self.get_assets(list(asset_ids), skip=skip, limit=limit)
        for asset in assets:
            if not asset.preview.downloaded():
                asset.preview.download()
            if asset.need_update:
                status = asset.download()
                if status:
                    logging.info('Installed asset with ID %s', asset.steamid)
                else:
                    logging.warning('Asset with ID %s cannot be intalled', asset.steamid)

    def get_tags(self) -> list[str]:
        """### swautomatic > object > SWAObject.`get_tags()`
            Returns a list of every tag in the database.
        """
        return sorted([tag['tag'] for tag in self.tags_coll.find({})])

    def count_assets(self, fltr: dict) -> int:
        """### swautomatic > object > SWAObject.`count_assets()`
            Counts assets in the database by given filter.
        
        #### Return
        `int`: Number of assets in the database.
        """
        return self.assets_coll.count_documents(filter=fltr)

    def close(self):
        """### swautomatic > object > SWAObject.`close()`
            Closes the database client.
        """
        self.client.close()
