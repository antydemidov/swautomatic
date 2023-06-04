"""
swautomatic > `results`
=======================
Module for results classes.
"""

from dataclasses import dataclass
from typing import Any

__all__ = [
    'CommonResult',
    'StatisticsResult',
    'DeleteResult',
    'DownloadResult',
]


class CommonResult(object):
    """
    swautomatic > results > `CommonResult`
    --------------------------------------
    Describes a result of some functions and methods.

    Attributes
    ----------
    - `status` (str): A string representating a status of running.
    - `status_bool` (bool): Boolean variant of status.
    - `message` (str): A string which will be shown to the user.
    """

    def __init__(
        self,
        status: str = 'Done',
        status_bool: bool = True,
        message: str = '',
        **kwargs
    ):
        self.status = status
        self.status_bool = status_bool
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, __name: str, __value: Any) -> None: ...


@dataclass
class StatisticsResult:
    """
    swautomatic > results > `StatisticsResult`
    ------------------------------------------
    Describes a result of SWAObject.`get_statistics()`
    """
    count: int
    count_by_tag: dict[str, int]
    installed: int
    not_installed: int
    assets_size: str
    mods_size: str
    total_size: str


class DeleteResult(CommonResult):
    """
    swautomatic > results > `DeleteResult`
    --------------------------------------
    Describes a result of SWAObject.`delete_assets()`.
    """

    def __init__(self, status: str = 'Done', status_bool: bool = True,
                 message: str = '', **kwargs):
        super().__init__(status, status_bool, message, **kwargs)
        self.count = int(kwargs.get('count', 0))
        self.size = int(kwargs.get('size', 0))


class DownloadResult(CommonResult):
    """
    swautomatic > results > `DownloadResult`
    ----------------------------------------
    Describes a result of SWAAsset.`download()`.

    Parameters
    ----------
    -   `~results.CommonResult` parameters;
    -   `size` (integer): a size of the downloaded asset.
    """

    def __init__(self, status: str = 'Done', status_bool: bool = True,
                 message: str = '', **kwargs):
        super().__init__(status, status_bool, message, **kwargs)
        self.size = kwargs.get('size', 0)
