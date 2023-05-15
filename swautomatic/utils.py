"""# swautomatic > `utils`

Module for some functions.
"""

import os


def get_size_format(size, factor=1024, suffix='B'):
    """
    Scale bytes to its proper byte format
    e.g:
    ```python
    >>> get_size_format(1253656)
    '1.196 MB'
    >>> get_size_format(1253656678)
    '1.168 GB'
    >>> get_size_format(2000, factor=1000, suffix='m')
    '2.000 Km'
    ```
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < factor:
            return f'{size:.3f} {unit}{suffix}'
        size /= factor
    return f'{size:.3f} Y{suffix}'


def get_directory_size(directory) -> int:
    """Returns the `directory` size in bytes."""
    total = 0
    try:
        # print("[+] Getting the size of", directory)
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                try:
                    total += get_directory_size(entry.path)
                except FileNotFoundError:
                    total += 0
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total
