"""# swautomatic > `results`

Module for results classes.
"""

from dataclasses import dataclass

__all__ = [
    'CommonResult',
    'StatisticsResult',
]


class CommonResult:
    """## swautomatic > results > `CommonResult`
    Describes a result of some functions and methods.

    ### Attributes
    - `status` (str): A string representating a status of running.
    - `status_bool` (bool): Boolean variant of status.
    """

    def __init__(
        self,
        status: str = 'Done',
        status_bool: bool = True,
        **kwargs
    ):
        self.status = status
        self.status_bool = status_bool
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class StatisticsResult:
    """## swautomatic > results > `StatisticsResult`
    Describes a result of SWAObject.`get_statistics()`
    """
    count: int
    count_by_tag: dict[str, int]
    installed: int
    not_installed: int
    assets_size: str
    mods_size: str
    total_size: str
