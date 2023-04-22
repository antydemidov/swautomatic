import os
from datetime import datetime
from stat import S_ISDIR, S_ISREG

import requests as rq
from bs4 import BeautifulSoup as bs

__version__ = '2023.01.23'
__author__ = 'Anton Demidov | @antydemidov'


def convert_time(time_string: str) -> datetime:
    """
    ## Convert a steam time string into a datetime
    time_string: string in steam format
    """
    if ', ' in time_string:
        date = datetime.strptime(time_string, '%d %b, %Y @ %I:%M%p')
    else:
        date = datetime.strptime(
            time_string, '%d %b @ %I:%M%p').replace(year=datetime.now().year)
    return date


def get_author_data(author_steamid):
    """Parse the author page and returns the data in dict"""
    with rq.get(f'https://steamcommunity.com/profiles/{author_steamid}/?xml=1') as req:
        soup = bs(req.content, 'xml')
    data = {}
    for field in ['steamID64', 'steamID', 'avatarIcon', 'avatarMedium', 'avatarFull', 'customURL']:
        field_value = soup.find(field)
        if field_value != None:
            field_value = field_value.text
        data.update({field: field_value})
    return data


class WalkTree:
    def __init__(self, top: str):
        self.path_tree = []
        self.skipped_paths = []
        self._walktree(top)
        self.files_count = len(self.path_tree)

    def _walktree(self, top):
        '''recursively descend the directory tree rooted at top,
        calling the callback function for each regular file'''

        for file in os.listdir(top):
            pathname = os.path.realpath(os.path.join(top, file))
            mode = os.lstat(pathname).st_mode
            if S_ISDIR(mode):
                self._walktree(pathname)
            elif S_ISREG(mode):
                self.path_tree.append(pathname)
            else:
                self.skipped_paths.append(pathname)

    def get_stats(self) -> dict | None:
        data = {}
        for pathname in self.path_tree:
            stat = os.stat(pathname)
            data.update({
                pathname: {
                    'size': stat.st_size,
                    'ctime': stat.st_ctime,
                    'atime': stat.st_atime,
                    'mtime': stat.st_mtime,
                }
            })
        return data if data else None

    def get_size(self) -> int:
        size = 0
        for path in self.path_tree:
            size += os.path.getsize(path)
        return size


if __name__ == '__main__':
    tree = WalkTree('E:/Games/Cities Skylines/Files/Mods')
    print(tree.data[list(tree.data.keys())[0]])
