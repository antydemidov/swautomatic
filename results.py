"""desc"""

__version__ = '2023.01.09'
__author__ = 'Anton Demidov | @antydemidov'


class CommonResult:
    """# Class `CommonResult`
    Describes a result of some functions and methods.

    ## Attributes
    `status`: str
        A string representating a status of running.
    `status_bool`: bool
        Boolean variant of status.
    `details`: dict
        A dictionary containing detatils of running."""
    def __init__(
        self,
        status: str = '',
        status_bool: bool = True,
        details: dict = None,   # dict
        **kwargs
    ):
        self.status = status
        self.status_bool = status_bool
        self.details = details
        for key, value in kwargs.items():
            setattr(self, key, value)
