"""
The module for the Library Filter.
"""

from typing import Any


class LibraryFilter:
    """Constant filter for the library."""
    fltr = {}
    steam_ids = None
    tag = None
    need_update = None
    is_installed = None
    other_fltr = None

    def __init__(self, **kwargs: Any) -> None:
        steam_ids = kwargs.get('steam_ids')
        tag = kwargs.get('tag')
        need_update = kwargs.get('need_update')
        is_installed = kwargs.get('is_installed')
        other_fltr = kwargs.get('other_fltr')

        if isinstance(steam_ids, (list, set)):
            type(self).steam_ids = steam_ids
            self.fltr.update({'steamid': {'$in': steam_ids}})
        if isinstance(tag, str):
            type(self).tag = tag
            self.fltr.update({'tags': tag})
        if isinstance(need_update, bool):
            type(self).need_update = need_update
            self.fltr.update({'need_update': need_update})
        if isinstance(is_installed, bool):
            type(self).is_installed = is_installed
            self.fltr.update({'is_installed': is_installed})
        if isinstance(other_fltr, dict):
            type(self).other_fltr = other_fltr
            self.fltr.update(other_fltr)

    def to_dict(self):
        """Returns a dictionary instance of the filter."""
        return self.fltr

    @classmethod
    def reset(cls):
        """Cleans the filter."""
        cls.fltr.clear()
        cls.steam_ids = None
        cls.tag = None
        cls.need_update = None
        cls.is_installed = None
        cls.other_fltr = None

    def __eq__(self, __value: object) -> bool:
        return self.fltr == getattr(__value, 'fltr')


class FilterMonitor:
    """Contains the data about applied filters."""
    def __init__(self, **kwargs: Any) -> None:
        self.tag = {
            'message': kwargs.get('tag_message'),
            'applied': kwargs.get('tag_applied'),
        }
        self.need_update = {
            'message': kwargs.get('need_update_message'),
            'applied': kwargs.get('need_update_applied'),
        }
        self.is_installed = {
            'message': kwargs.get('is_installed_message'),
            'applied': kwargs.get('is_installed_applied'),
        }
        if (kwargs.get('tag_applied') or kwargs.get(
            'need_update_applied') or kwargs.get('is_installed_applied')):
            self.total = True
        else:
            self.total = False
