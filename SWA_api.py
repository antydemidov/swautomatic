import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime

import requests as rq
from bs4 import BeautifulSoup as bs

from results import CommonResult
from utils import get_author_data

from connection import assets_coll, tags_coll, settings, client

__author__ = 'Anton Demidov | @antydemidov'

url_parts = ['cw03361255710','cw85745255710','ca40929255710','ci03361255710']
base_links = [f'https://cdn.ggntw.com/{i}/' for i in url_parts] + [
    f'https://cdn.steamworkshopdownloader.ru/{i}/' for i in url_parts] + [
        'http://workshop.abcvg.info/archive/255710/'] + [
            f'http://workshop{i+1}.abcvg.info/archive/255710/' for i in range(9)]


class SWAObject:
    """Annotation"""
    def __init__(self):
        self.settings = settings
        self.client = client

    def get_asset(self, steam_id: int):
        asset = Asset(steam_id, swa_object=self)
        return asset

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
        tags = tags_coll.find({})
        tags_ids = [tag['_id'] for tag in tags]

        stats = []
        for tag in tags_ids:
            stat = {
                'tag_id': tag,
                'tag_name': tags_coll.find_one({'_id': tag})['tag'],
                'count': assets_coll.count_documents({'tags': tag})
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

    def steam_api_data(self, ids) -> dict:
        needed_fields = settings.needed_fields
        link_text = settings.steam_api_url
        if type(ids) in [str, int]:
            ids = [ids]
        post_data = {'itemcount': len(ids)}
        for i in range(len(ids)):
            post_data.update({f'publishedfileids[{i}]': ids[i]})
        post_data.update({'format': 'json'})

        with rq.post(link_text, data=post_data, timeout=settings.timeout) as req: # settings.timeout of big request
            data = req.json()['response']['publishedfiledetails']

        result = {}
        for item in data:
            needed_part = {}
            for field in needed_fields:
                try: # I don't remember why try is there CHECK
                    if 'time' in field:
                        needed_part.update({field: datetime.fromtimestamp(item[field])})
                    else:
                        needed_part.update({field: item[field]})
                except Exception:
                    pass
            result.update({item['publishedfileid']: needed_part})

        return result

    def check_updates(self):
        ids = [id['steamid'] for id in list(
            assets_coll.find({}, projection={'_id': False, 'steamid': True}))]
        data_steam = self.steam_api_data(ids)
        for key, value in data_steam.items():
            time_updated_local = assets_coll.find_one({'steamid': int(key)})['time_updated']
            time_updated_steam = value['time_updated']
            if time_updated_local < time_updated_steam:
                assets_coll.update_one(
                    {'steamid': int(key)},
                    {'$set': {
                        'time_updated': time_updated_steam,
                        'need_update': True
                    }})

    def info_steam(self, ids: list):
        data = {}
        steam_data = self.steam_api_data(ids)
        for key, value in steam_data.items():
            info = {}
            steamid = int(key)
            info_from_steam = value
            if info_from_steam.get('publishedfileid'):
                info.update({'steamid': steamid})
            else:
                info = None

                # === name ===
                asset_name = info_from_steam.get('title')
                if asset_name:
                    info.update({'name': asset_name})
                else:
                    info.update({'name': None})

                # === tags ===
                workshop_tags = info_from_steam['tags']
                if workshop_tags:
                    tags = [tags_coll.find_one({'tag': workshop_tag['tag']})[
                        '_id'] for workshop_tag in workshop_tags if workshop_tag is not None]
                    info.update({'tags': tags})
                else:
                    info.update({'tags': None})

                # === preview ===
                try:
                    preview_url = info_from_steam['preview_url']
                    with rq.head(preview_url, timeout=settings.timeout) as req:
                        pic_format = req.headers.get('Content-Type').split('/')[1]
                    if pic_format in ['jpg', 'jpeg', 'png']:
                        preview_path = ''.join(['previews/', str(steamid), '.', pic_format])
                    else:
                        preview_path = ''.join(['previews/', str(steamid), '.png'])
                    info.update({'preview_url': preview_url})
                    info.update({'preview_path': preview_path})
                except Exception:
                    info.update({'preview_url': None})
                    info.update({'preview_path': None})

                # === path ===
                if 'Mod' in workshop_tags:
                    path = f'{settings.mods_path}/{str(steamid)}'
                else:
                    path = f'{settings.assets_path}/{str(steamid)}'
                info.update({'path': path})

                # === is_installed ===
                info.update({'is_installed': self.is_installed(steamid)})

                # === time_local ===
                if info['is_installed'] is True:
                    time_local = datetime.fromtimestamp(os.path.getmtime(info['path']))
                else:
                    time_local = None
                info.update({'time_local': time_local})
                info.update({
                    'file_size': info_from_steam['file_size'],
                    'time_created': info_from_steam['time_created'],
                    'time_updated': info_from_steam['time_updated'],
                })
                info.update({'author': get_author_data(info_from_steam['creator'])})

                # === need_update ===
                need_update = (info['is_installed'] and (info['time_local'] < info['time_updated']))
                info.update({'need_update': need_update})
                data.update({steamid: info})

                # info.update({
                #     'steamid': steamid,
                #     'name': asset_name,
                #     'tags': tags,
                #     'preview_url': preview_url,
                #     'preview_path': preview_path,
                #     'path': path,
                #     'is_installed': self.is_installed(steamid),
                #     'time_local': time_local,
                #     'file_size': info_from_steam['file_size'],
                #     'time_created': info_from_steam['time_created'],
                #     'time_updated': info_from_steam['time_updated'],
                #     'author': get_author_data(info_from_steam['creator']),
                #     'need_update': (info['is_installed'] and (info['time_local'] < info['time_updated'])),
                # })
                # Asset.from_source()
        return data

    def update_database(self):
        ids_from_favs = self.ids_steam()
        ids_in_db = [id['steamid'] for id in list(assets_coll.find(
            {}, projection={'_id': False, 'steamid': True}))]

        if ids_from_favs.status_bool is True:
            ids_favs = getattr(ids_from_favs, 'ids')
            ids_to_delete = list(set(ids_in_db) - set(ids_favs))
            ids_to_update = list(set(ids_favs) - set(ids_in_db))
            if ids_to_delete:
                deleted_count = assets_coll.delete_many(
                    {'steamid': {'$in': ids_to_delete}}
                ).deleted_count
            else:
                deleted_count = 0
            if ids_to_update:
                new_data = self.info_steam(ids_to_update)
                inserted_count = len(assets_coll.insert_many(list(new_data.values())).inserted_ids)
            else:
                inserted_count = 0
        for id_to_update in ids_to_update:
            asset = Asset(id_to_update)
            asset.download_preview()

        return CommonResult(status='Done',
                            status_bool=True,
                            deleted_count=deleted_count,
                            inserted_count=inserted_count,
                            new_items=ids_to_update)

    def is_installed(self, steam_id):
        is_installed = os.path.exists(f'{settings.assets_path}/{steam_id}') or os.path.exists(
            f'{settings.mods_path}/{steam_id}')
        return is_installed


class Asset:
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
    """Annotation"""
    def __init__(self, asset_id, swa_object: SWAObject):
        self.steamid = int(asset_id)
        self.info = None
        self.swa_object = swa_object

    # @classmethod
    # def from_source(cls, **kwargs):
    #     asset = cls()
    #     for key, value in kwargs.items():
    #         if key == 'author':
    #             asset.author = SWAAuthor(**value)
    #         elif key == 'tags':
    #             if isinstance(value, list):
    #                 asset.tags = [SWATag(tag) for tag in value]
    #             else:
    #                 asset.tags = [SWATag(value)]
    #         elif key == 'preview_url':
    #             asset.preview_url = SWAPreview(value, getattr(asset, 'steamid'))
    #         else:
    #             setattr(asset, key, value)

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

    def info_steam(self):
        info = {}
        info_from_steam: dict = self.swa_object.steam_api_data(
            self.steamid)[str(self.steamid)]
        
        # === steam id ===
        if info_from_steam.get('publishedfileid') is None:
            self.info = None
            return None
        info.update({'steamid': self.steamid})

        # === name ===
        asset_name = info_from_steam.get('title')
        info.update({'name': asset_name if asset_name else None})

        # === tags ===
        workshop_tags = info_from_steam.get('tags')
        if workshop_tags:
            tags = []
            for workshop_tag in workshop_tags:
                tags.append(tags_coll.find_one({'tag': workshop_tag['tag']})['_id'])
            info.update({'tags': tags})
        else:
            info.update({'tags': None})

        # === preview ===
        try:
            preview_url = info_from_steam['preview_url']
            with rq.head(preview_url, timeout=settings.timeout) as req:
                pic_format = req.headers.get('Content-Type').split('/')[1]
            if pic_format in ['jpg', 'jpeg', 'png']:
                preview_path = f'previews/{self.steamid}.{pic_format}'
            else:
                preview_path = f'previews/{self.steamid}.png'
            info.update({'preview_url': preview_url})
            info.update({'preview_path': preview_path})
        except Exception:
            info.update({'preview_url': None})
            info.update({'preview_path': None})

        # === path ===
        if 'Mod' in workshop_tags:
            path = f'{settings.mods_path}/{self.steamid}'
        else:
            path = f'{settings.assets_path}/{self.steamid}'
        info.update({'path': path})

        # === downloaded? ===
        info.update({'is_installed': self.is_installed()})

        # === local date of update ===
        if info['is_installed']:
            time_local = datetime.fromtimestamp(os.path.getmtime(info['path']))
        else:
            time_local = None
        info.update({'time_local': time_local})

        info.update({
            'file_size': info_from_steam['file_size'],
            'time_created': info_from_steam['time_created'],
            'time_updated': info_from_steam['time_updated']
        })
        info.update({'author': get_author_data(info_from_steam['creator'])})

        # === need to update? ===
        need_update = (info['is_installed'] and (info['time_local'] < info['time_updated']))
        info.update({'need_update': need_update})
        d_asset = dAsset(**info)
        return d_asset
    
    def info_database(self):
        """Search info about the asset in database by its id"""
        data = assets_coll.find_one({'steamid': self.steamid})
        return dAsset(**data)

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
        if not os.path.exists(self.info.preview_path):
            preview_url = self.info.preview_url
            if preview_url is not None:
                with rq.get(preview_url, timeout=settings.timeout) as req:
                    preview_b = req.content
                path = self.info.preview_path
                with open(path, 'wb') as f:
                    f.write(preview_b)
                status = True
            else:
                status = False
            return status

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

    def update_preview_path(self):
        if not self.info:
            self.get_info()

        try:
            preview_url = self.info.preview_url
            with rq.head(preview_url, timeout=settings.timeout) as req:
                pic_format = req.headers.get('Content-Type').split('/')[1]
            if pic_format in ['jpg', 'jpeg', 'png']:
                preview_path = f'previews/{self.steamid}.{pic_format}'
            else:
                preview_path = f'previews/{self.steamid}.png'

            result = assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {'preview_path': preview_path}}
            )
            if result.matched_count == 1 and result.modified_count == 1:
                return CommonResult(
                    status='Preview path updated successfully.',
                    status_bool=True,
                    details=None
                )
            return CommonResult(
                status='Failed to update preview path.',
                status_bool=False,
                details=None
            )

        except rq.exceptions.RequestException as error:
            return CommonResult(
                status='Request failed.',
                status_bool=False,
                details=str(error)
            )

        except Exception as error:
            with open('errors.txt', 'a', encoding='utf-8') as file:
                file.write(f'{self.steamid}\n')
            return CommonResult(
                status='Failed to update preview path.',
                status_bool=False,
                details=str(error)
            )

    def update_preview_url(self):
        info = self.info_steam()
        if info:
            assets_coll.update_one(
                {'steamid': self.steamid},
                {'$set': {'preview_url': info['preview_url']}}
            )

    def download(self) -> bool:
        if not self.info:
            self.get_info()
        if (self.info.is_installed is False or self.info.need_update is True):
            path = f'{self.info.path}.zip'
            for base_link in base_links:
                url = f'{base_link}{self.steamid}.zip'
                url_headers = rq.head(url, timeout=settings.timeout)
                if (
                    ContentType(url_headers.headers.get('Content-Type')).type == 'application' and 
                    int(url_headers.headers.get('Content-Length')) >= 10000
                ):
                    # timeout for BIG requests
                    with rq.get(url, stream=True, timeout=settings.timeout+240) as req:
                        with open(path, 'wb') as f:
                            f.write(req.content)
                    break
            try:
                if zipfile.is_zipfile(path):
                    if os.path.exists(self.info.path):
                        shutil.rmtree(self.info.path)
                    with zipfile.ZipFile(path, 'r') as zip:
                        mod_tag_id = tags_coll.find_one({'tag': 'Mod'})['_id']
                        asset_tags = []
                        for tag in self.info.tags:
                            asset_tags.append(tag._id)
                        if mod_tag_id in asset_tags:
                            extract_path = settings.mods_path
                        else:
                            extract_path = settings.assets_path
                        zip.extractall(extract_path)
                os.remove(path)
                status = True
            except Exception:
                status = False
        else:
            status = True

        if status is True:
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
        is_installed = os.path.exists(
            f'{settings.assets_path}/{self.steamid}') or os.path.exists(
                f'{settings.mods_path}/{self.steamid}')
        return is_installed

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
            raise ValueError(string)
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
    """Annotation"""
    def __init__(self, url: str, steam_id: int, swa_object: SWAObject):
        self.url = url
        self.swa_object = swa_object
        with rq.head(url, timeout=settings.timeout) as req:
            if req.status_code == 200:
                # what if Content-Type is not set?
                pic_format = ContentType(req.headers.get('Content-Type')).format
            else:
                pic_format = 'png'
        # it's better to use os.path.abspath as ChatGPT said
        self.path = os.path.relpath(os.path.join(settings.previews_path, str(steam_id) + '.' + pic_format))

    def download(self):
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
