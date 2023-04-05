__version__ = '2023.01.09'
__author__ = 'Anton Demidov | @antydemidov'

class CommonResult:
    def __init__(
        self,
        status: str = '',
        status_bool: bool = True,
        details: dict = {},
        **kwargs
    ):
        self.status = status
        self.status_bool = status_bool
        self.details = details
        for key, value in kwargs.items():
            self.__setattr__(key, value)