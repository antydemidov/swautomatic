"""
swautomatic > `tag`
===================
Module for class `SWATag` and its interface `ISWATags`.
"""

import re

import requests as rq
from bs4 import BeautifulSoup as bs

from .connection import _logger, _settings, _tags_coll
from .results import CommonResult, DeleteResult

__all__ = [
    'SWATag',
    'ISWATags'
]


class SWATag:
    """
    swautomatic > tag > `SWATag`
    ----------------------------
    Simple class storing id and name of the tag.

    Attributes
    ----------
    -   `tag` (str): name of the tag.

    Methods
    -------
    -   `count_assets()`: Returns a number of assets with the tag.
    """

    def __init__(self, tag: str):
        self.tag = tag
        data = _tags_coll.find_one({'tag': tag})
        if not data:
            _tags_coll.insert_one({'tag': tag})

    def __str__(self) -> str:
        return self.tag

    def count_assets(self) -> int:
        """
        swautomatic > tag > SWATag.`count_assets()`
        -------------------------------------------
        Returns a number of assets with the tag.
        """

        return _tags_coll.count_documents({'tags': self.tag})


class ISWATags:
    """
    swautomatic > tag > `ISWATags`
    ------------------------------
    The interface for tags.
    """

    def __init__(self) -> None:
        self.coll = _tags_coll

    def get_tag(self, name: str) -> SWATag:
        """
        swautomatic > tag > ISWATags.`get_tag()`
        ----------------------------------------
        Returns a list of every tag in the database.
        """

        return SWATag(name)

    def get_tags(self, names: list[str]) -> list[SWATag]:
        """
        swautomatic > tag > ISWATags.`get_tags()`
        -----------------------------------------
        Returns a list of every tag in the database.
        """

        tags = [SWATag(tag) for tag in names]
        return tags

    def list_tags(self) -> set[str]:
        """
        swautomatic > tag > ISWATags.`list_tags()`
        ------------------------------------------
        Returns a set of tags in the database.
        """

        return set(tag['tag'] for tag in self.coll.find({}))

    def list_tags_remote(self) -> set[str]:
        """
        swautomatic > tag > ISWATags.`list_tags_remote()`
        -------------------------------------------------
        Returns a set of tags in the database.

        Return
        ------
        -   `set[str]`: set of tags or set with 'No tags' tag.
        """

        tags = set(['No tags'])
        try:
            response = rq.get(
                'https://steamcommunity.com/app/255710/workshop/',
                timeout=_settings.timeout)
            soup = bs(response.content, 'html.parser')
            tags_soup = soup.find_all('label', 'tag_label')
            tags = set(' '.join(re.findall(r'\S+', tag.text)[:-1])
                       for tag in tags_soup)
        except (rq.RequestException, ValueError) as error:
            _logger.critical('The tags could not be fetched. %s', str(error))
        return tags

    def delete_tags(self, names: list[str] | set[str]):
        """
        swautomatic > tag > ISWATags.`remove_tags()`
        --------------------------------------------
        Returns a list of every tag in the database.
        """

        # TODO: add checking if given tags are exist.
        names = list(names)
        count = self.coll.delete_many({'tag': {'$in': names}}).deleted_count
        return DeleteResult(
            message=f'{count} tags were deleted. Deleted tags: {names}',
            count=count, size=0)

    def insert_tags(self, names: list[str] | set[str]):
        """
        swautomatic > tag > ISWATags.`insert_tags()`
        --------------------------------------------
        Returns a list of every tag in the database.
        """

        names = list(names)
        tags = [{'tag': tag} for tag in names]
        if self.coll.find_one({'tag': 'No tags'}) is None:
            tags.append({'tag': 'No tags'})
        self.coll.insert_many(tags)

    # UPDATE
    def update_tags(self) -> CommonResult:
        """
        swautomatic > tag > ISWATags.`update_tags()`
        --------------------------------------------
        Update the tags from Steam Community by deleting outdated documents
        in the collection before updating.

        Return
        ------
        -   `CommonResult`: An object containing the status of the update
            operation.

        Raises
        ------
        -   `RequestException`: If there is an error in the HTTP request.
        -   `ValueError`: If there is a value error during the execution.
        """

        tags_at_steam = self.list_tags_remote()
        tags_in_db = self.list_tags()
        tags_to_del = tags_in_db - tags_at_steam
        tags_to_upd = tags_at_steam - tags_in_db

        if tags_to_del:
            self.delete_tags(tags_to_del)
        if tags_to_upd:
            self.insert_tags(tags_to_upd)

        if tags_to_del or tags_to_upd:
            status = f"Done! Deleted {len(tags_to_del)} tags \
                and {len(tags_to_upd)} tags were added."
        else:
            status = 'There are no new tags.'

        return CommonResult(
            status=status,
            status_bool=True,
            message=f'Deleted tags: {str(tags_to_del)}. \
                New tags: {str(tags_to_upd)}.',
            deleted_tags=tags_to_del,
            inserted_tags=tags_to_upd,
        )
