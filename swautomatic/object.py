"""
swautomatic > `object`
======================
Module for class `SWAObject`.
"""

from .asset import ISWAAssets
from .connection import _client, _logger, _settings
from .results import CommonResult, StatisticsResult
from .tag import ISWATags
from .utils import get_directory_size, get_size_format

__all__ = ['SWAObject']


class SWAObject:
    """
    swautomatic > object > `SWAObject`
    ----------------------------------
    The main object of Swautomatic project.

    Attributes
    ----------
    - `client` (pymongo.MongoClient): A MongoDB client object.
    - `settings` (SWASettings): An object representing Swautomatic settings.

    Methods
    -------
    -   `get_statistics()`: Retrieves statistics about the database and returns
        a ~results.`StatisticsResult` object.
    -   `total_reset()`: DANGEROUS!!! Deletes all records in the assets
        collection in the database. Deletes all previews and assets.
    -   `close()`: Closes the database client.
    """

    def __init__(self):
        self.client = _client
        self.settings = _settings
        self.tags = ISWATags()
        self.assets = ISWAAssets()

    def get_statistics(self):
        """
        swautomatic > object > SWAObject.`get_statistics()`
        ---------------------------------------------------
        Retrieves statistics about the database and returns a StatisticsResult
        object.

        Return
        ------
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
        # count = self.assets_coll.count_documents({})
        count = self.assets.count_assets()
        tags = self.tags.list_tags()

        stats = {}
        for tag in tags:
            stats.update({tag: self.assets.count_assets(tags=tag)})

        installed = self.assets.count_assets(is_installed=True)
        not_installed = self.assets.count_assets(is_installed=False)

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

    def total_reset(self):
        """
        swautomatic > object > SWAObject.`total_reset()`
        ------------------------------------------------
        DANGEROUS!!! Deletes all records in the assets collection in the
        database. Deletes all previews and assets.

        Result
        ------
        A dictionary containing information about the reset operation.
        - `size` (integer): sum of assets` sizes.
        - `assets_count` (integer): count of deleted assets.
        - `previews_count` (integer): count of deleted previews.
        """

        return self.assets.delete_assets()

    def update_database(self):
        """
        swautomatic > object > SWAObject.`update_database()`
        ----------------------------------------------------
        Updates the database by performing operations for deleting, updating,
        and inserting assets. It also downloads the previews for newly inserted
        assets. The function uses MongoDB transactions for ensuring data
        consistency.
        """

        try:
            ids_steam = self.assets.list_assets_remote()
            ids_database = self.assets.list_assets_db()
            ids_local = self.assets.list_assets_local()
            ids_to_delete = (ids_local | ids_database) - ids_steam
            ids_to_insert = ids_steam - ids_database
            ids_to_update = ids_database

            deleted_count = self.assets.delete_assets(ids_to_delete)
            updated_count = self.assets.update_assets(ids_to_update)
            inserted_count = self.assets.insert_assets(ids_to_insert)

            message = f'The database updated, deleted: {deleted_count}, \
                updated: {updated_count}, inserted: {inserted_count}.'
            _logger.info(message)
            return CommonResult(deleted_count=deleted_count,
                                inserted_count=inserted_count,
                                updated_count=updated_count,
                                new_items=list(ids_to_insert)
                                )
        except Exception as error:
            _logger.critical('Updating was failed. %s', error)
            raise error

    # def close(self):
    #     """
    #     swautomatic > object > SWAObject.`close()`
    #     ------------------------------------------
    #     Closes the database client.
    #     """
    #     self.client.close()
