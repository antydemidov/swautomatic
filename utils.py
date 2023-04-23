# import os
# from datetime import datetime
# from stat import S_ISDIR, S_ISREG

import requests as rq
from bs4 import BeautifulSoup as bs

from connection import settings

__version__ = '2023.01.23'
__author__ = 'Anton Demidov | @antydemidov'


def get_author_data(author_steamid):
    """Parse the author page and returns the data in dict"""
    soup = None
    try:
        with rq.get(f'https://steamcommunity.com/profiles/{author_steamid}/?xml=1',
                    timeout=settings.timeout) as req:
            soup = bs(req.content, 'xml')
    except rq.RequestException as error:
        # TODO: Add an errors catcher. Closes #14
        print(f'An error occured for {author_steamid}: {str(error)}')
    data = {}
    if isinstance(soup, bs):
        for field in settings.author_needed_fields:
            value = soup.find(field)
            text = None
            if value:
                text = value.text
            data.update({field: text})
    return data


# class WalkTree:
#     def __init__(self, top: str):
#         self.path_tree = []
#         self.skipped_paths = []
#         self._walktree(top)
#         self.files_count = len(self.path_tree)

#     def _walktree(self, top):
#         '''recursively descend the directory tree rooted at top,
#         calling the callback function for each regular file'''

#         for file in os.listdir(top):
#             pathname = os.path.realpath(os.path.join(top, file))
#             mode = os.lstat(pathname).st_mode
#             if S_ISDIR(mode):
#                 self._walktree(pathname)
#             elif S_ISREG(mode):
#                 self.path_tree.append(pathname)
#             else:
#                 self.skipped_paths.append(pathname)

#     def get_stats(self) -> dict | None:
#         data = {}
#         for pathname in self.path_tree:
#             stat = os.stat(pathname)
#             data.update({
#                 pathname: {
#                     'size': stat.st_size,
#                     'ctime': stat.st_ctime,
#                     'atime': stat.st_atime,
#                     'mtime': stat.st_mtime,
#                 }
#             })
#         return data if data else None

#     def get_size(self) -> int:
#         size = 0
#         for path in self.path_tree:
#             size += os.path.getsize(path)
#         return size
