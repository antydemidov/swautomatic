"""# swautomatic > `author`

Module for class `SWAAuthor`.
"""

import logging

import requests as rq
from bs4 import BeautifulSoup as bs

from . import _settings


class SWAAuthor:
    """## Swautomatic > SWA_api > `SWAAuthor`
        Desc.

    ### Parameters:
        - `steamid` (integer): A Steam ID of the author.
        - `**kwargs` (dict): The data to fill the fields of this object.
    """

    def __init__(self, steamid: int = 0, **kwargs) -> None:
        # validate(kwargs, swa_author_schema)
        if not steamid:
            logging.error('SteamID of the author was not received.')
        else:
            self.steam_id64 = steamid
            data = kwargs or self.get_author_data()
            self.steam_id: str = data.get('steam_id', None)
            self.avatar_icon: str = data.get('avatar_icon', None)
            self.avatar_medium: str = data.get('avatar_medium', None)
            self.avatar_full: str = data.get('avatar_full', None)
            self.custom_url: str = data.get('custom_url', None)

    def to_dict(self) -> dict:
        """### Swautomatic > SWA_api > SWAAuthor.`to_dict()`
            Coverts the object to dictionary.

        #### Return
            A dictionary (desc).
                - `steam_id64` (int): desc;
                - `steam_id` (str): desc;
                - `avatar_icon` (str): desc;
                - `avatar_medium` (str): desc;
                - `avatar_full` (str): desc;
                - `custom_url` (str): desc.
        """

        return {'steam_id64': self.steam_id64,
                'steam_id': self.steam_id,
                'avatar_icon': self.avatar_icon,
                'avatar_medium': self.avatar_medium,
                'avatar_full': self.avatar_full,
                'custom_url': self.custom_url,
                }

    def get_author_data(self) -> dict:
        """### Swautomatic > SWA_api > SWAAuthor.`get_author_data()`
            Parse the author page and returns the data in dict.

        #### Return
            A dictionary with a data about the author.
        """
        soup = None
        try:
            with rq.get(
                f'https://steamcommunity.com/profiles/{self.steam_id64}/?xml=1',
                    timeout=_settings.timeout) as req:
                soup = bs(req.content, 'xml')
        except rq.RequestException as error:
            logging.error(
                'An error occured for %s: %s',
                self.steam_id64, str(error))
        data = {}
        if isinstance(soup, bs):
            for field in _settings.author_needed_fields:
                value = soup.find(field)
                text = None
                if value:
                    text = value.text
                data.update({_settings.mapping_fields[field]: text})
        return data
