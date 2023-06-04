"""
swautomatic > `utils`
=====================
Module for some functions.
"""

import os
import shutil
from datetime import datetime
from typing import Any, Optional

import requests as rq

from swautomatic.author import SWAAuthor

from .connection import _assets_coll, _logger, _settings
from .settings import DFLT_DATE

__all__ = [
    'check_datetime',
    'delete_directory',
    'delete_files_in_dir',
    'find_preview',
    'get_directory_size',
    'get_info',
    'get_local_time',
    'get_size_format',
    'info_steam',
    'steam_api_data',
]


def get_size_format(size, factor=1024, suffix='B'):
    """
    swautomatic > utils > `get_size_format()`
    -----------------------------------------
    Scale bytes to its proper byte format.

    Example
    -------
    ```python
    >>> get_size_format(1253656)
    '1.196 MB'
    >>> get_size_format(1253656678)
    '1.168 GB'
    >>> get_size_format(2000, factor=1000, suffix='m')
    '2.000 Km'
    ```
    """

    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < factor:
            return f'{size:.3f} {unit}{suffix}'
        size /= factor
    return f'{size:.3f} Y{suffix}'


def get_directory_size(directory) -> int:
    """
    swautomatic > utils > `get_directory_size()`
    --------------------------------------------
    Returns the `directory` size in bytes.
    """

    total = 0
    try:
        # print("[+] Getting the size of", directory)
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                try:
                    total += get_directory_size(entry.path)
                except FileNotFoundError:
                    total += 0
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total


def __get_local_time(path: str) -> float:
    """
    swautomatic > utils > `__get_local_time()`
    ------------------------------------------
    Returns the latest time of modification in directory.
    """

    time_local = 1.0
    if os.path.exists(path):
        for entry in os.scandir(path):
            if entry.is_file():
                time = entry.stat().st_mtime
                if time > time_local:
                    time_local = time
            elif entry.is_dir():
                time = __get_local_time(entry.path)
                if time > time_local:
                    time_local = time
    return time_local


def get_local_time(path: str) -> datetime:
    """
    swautomatic > utils > `get_local_time()`
    ----------------------------------------
    Returns the latest time of modification in directory.
    """

    time_local = __get_local_time(path)
    return datetime.fromtimestamp(time_local)


def find_preview(directory: str, steam_id: str | int) -> str | None:
    """
    swautomatic > utils > `find_preview()`
    --------------------------------------
    Searches a preview for the asset with ID `steam_id` in given directory.
    """

    path = None
    steam_id = str(steam_id)
    for file in os.listdir(directory):
        if steam_id in file:
            path = file
    return path


def delete_directory(path: str):
    """
    swautomatic > utils > `delete_directory()`
    ------------------------------------------
    Removes the directory with given `path`.
    """

    try:
        shutil.rmtree(path)
        _logger.info('Deleted directory: %s', path)
        print(f"Deleted directory: {path}")
    except OSError as error:
        _logger.warning(
            'Failed to delete directory: %s Error: %s',
            path, str(error))


def steam_api_data(ids: list[int] | set[int]) -> dict[str, dict]:
    """
    swautomatic > utils > `steam_api_data()`
    ----------------------------------------
    Returns data about assets and mods from Steam API.

    Parameters
    ----------
    - `ids` (list): A list of asset IDs.

    Return
    ------
    A dictionary containing data about assets and mods from the Steam API.
    """

    ids = list(ids)
    post_data = {'itemcount': len(ids)}
    post_data.update(
        {f'publishedfileids[{i}]': ids[i] for i in range(len(ids))})
    post_data.update({'format': 'json'})  # type: ignore

    data = []
    try:
        if _settings.steam_api_url:
            with rq.post(_settings.steam_api_url, data=post_data,
                         timeout=_settings.longtimeout) as req:
                data = req.json()['response']['publishedfiledetails']
    except (ValueError, KeyError) as error:
        _logger.critical('The connection was not established. %s', error)

    result = {
        item['publishedfileid']: {
            field: datetime.fromtimestamp(item[field]) if 'time' in field
            else item[field] for field in _settings.needed_fields if field
            in item
        } for item in data
    }
    return result


def delete_files_in_dir(path, exception: Optional[list[str]] = None):
    """
    swautomatic > utils > `delete_files_in_dir()`
    ---------------------------------------------
    Ensures if `data` is `datetime`.
    """

    if not exception:
        exception = []
    for entry in os.scandir(path):
        if entry.is_file() and entry.name not in exception:
            try:
                os.remove(entry.path)
            except OSError as error:
                _logger.error(
                    'Error occurred while deleting preview file %s: %s',
                    entry.name, str(error))


def check_datetime(data: Any) -> datetime:
    """
    swautomatic > utils > `check_datetime()`
    ----------------------------------------
    Ensures if `data` is `datetime`.
    """

    if data is None or not isinstance(data, datetime):
        return DFLT_DATE
    return data


def info_steam(ids: list[int] | set[int]) -> dict[int, dict]:
    """
    swautomatic > utils > `info_steam()`
    ------------------------------------
    Returns the formated dictionary with the data from Steam.

    Parameters
    ----------
    -   `ids` (list): A list of asset IDs.

    Return
    ------
    A dictionary containing the formatted Steam data for the assets.
    """

    data = {}
    steam_data = steam_api_data(ids)
    for key, value in steam_data.items():
        steam_id = int(key)
        if value.get('publishedfileid', 0):
            # === name ===
            name = value.get('title', None)
            if name is None:
                _logger.error(
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
                    _logger.error(
                        'Failed to retrieve tags for asset with Steam ID %s: %s',
                        steam_id, error)
            # === preview ===
            preview_url = value.get('preview_url')
            # === file_size ===
            file_size: int = value.get('file_size', 0)
            # === time ===
            time_created = check_datetime(value.get('time_created'))
            time_updated = check_datetime(value.get('time_updated'))
            # === author ===
            try:
                author = SWAAuthor(int(value['creator'])).to_dict()
            except KeyError as error:
                _logger.error('Failed to retrieve author data for asset with\
                              Steam ID %s: %s', steam_id, error)
                author = None

            data.update({
                steam_id: {
                    'steamid': steam_id,
                    'name': name,
                    'tags': tags,
                    'preview_url': preview_url,
                    'file_size': file_size,
                    'time_created': time_created,
                    'time_updated': time_updated,
                    'author': author,
                }})
    return data


def get_info(steamid: int, force_steam: bool = False) -> dict[str, Any] | None:
    """
    swautomatic > utils > `get_info()`
    ----------------------------------
    This is the main method to get the asset's or mod's data.

    Parameters
    ----------
    -   `steamid`: (integer) - Steam ID of the asset.
    -   `force_steam`: (bool) - The flag which is forcing the loading from
        Steam. If `True`, the data will always be fetched from Steam, if
        `False`, the database will be checked.

    Return
    ------
    A dictionary with data about asset.
    """

    info = None
    if not force_steam:
        info = _assets_coll.find_one({'steamid': steamid})
    if not info:
        info = info_steam([steamid]).get(steamid, None)
    return info
