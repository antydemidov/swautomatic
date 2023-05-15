"""# swautomatic > `preview`

Module for class `SWAPreview`.
"""

import logging
import os
from urllib.request import urlopen

from PIL import Image, UnidentifiedImageError

from . import _settings


class SWAPreview:
    """## Swautomatic > SWA_api > `SWAPreview`
    An object representing a preview image for a Steam Workshop item.

    ### Attributes:
    - `url` (str): The URL of the preview image.
    - `path` (str): The path to the local file where the preview image is stored.
    - `format` (str): The file format of the preview image.

    ### Methods:
    - `download()`:
    Downloads the file from `self.url`, saves it to `self.path` and checks if
    the size of the downloaded file is equal to the expected Content-Length.

    ### Parameters:
    - `steam_id` (int): The Steam Workshop ID of the item to which this preview
    image belongs.
    - `preview_url` (str): The URL of the preview image."""

    def __init__(self, steam_id: int, preview_url: str):
        self.steam_id: int = steam_id
        self.url: str = preview_url

    def downloaded(self) -> bool:
        """### Swautomatic > SWA_api > SWAPreview.`to_dict()`
        Checks if preview is downloaded."""
        downloaded = False
        steam_id = str(self.steam_id)
        files = os.listdir(_settings.previews_path)
        for file in files:
            if steam_id in file:
                downloaded = True
        return downloaded

    def to_dict(self):
        """### Swautomatic > SWA_api > SWAPreview.`to_dict()`
        Returns a dict for database.

        #### Return
        - `dict` desc."""
        return {'preview_url': self.url}

    def download(self) -> int:
        """### Swautomatic > SWA_api > SWAPreview.`download()`

        Downloads and saves the preview image for the asset.

        This method retrieves the preview image for the asset from the provided
        URL, resizes it if necessary, and saves it to the appropriate location
        on the file system.

        Returns the size of the downloaded image file in bytes.

        #### Return
        The size of the downloaded image file in bytes, rtype: `int`."""
        # Use a thread pool: If you need to download multiple preview images,
        # you could use a thread pool to download them concurrently. This would
        # make better use of the available network bandwidth and improve overall
        # download speed. The concurrent.futures module provides a
        # ThreadPoolExecutor class that you could use for this.
        #
        # Use asynchronous I/O: If you're downloading a large number of preview
        # images, using asynchronous I/O could be more efficient than using a
        # thread pool. You could use a library like asyncio to implement this.

        try:
            with Image.open(urlopen(self.url, timeout=_settings.timeout)) as img:

                # Resize the image if its minimum dimension is greater than 512 pixels
                if min(img.size) > 512:
                    ratio = 512 / min(img.size)
                    width, height = img.size
                    img = img.resize(
                        size=(int(width * ratio), int(height * ratio)))

                # Determine the image format (default to 'PNG' if not available)
                pic_format = img.format or 'PNG'

                # Construct the path to save the image
                path = os.path.join(_settings.app_path, _settings.previews_path,
                                    f'{self.steam_id}.{pic_format.lower()}')

                # Save the image with optimization
                img.save(path, optimize=True)

            # Return the size of the downloaded image file
            return os.path.getsize(path)

        except FileNotFoundError as error:
            logging.critical(
                'The file for asset %s cannot be found', self.steam_id)
            logging.exception(error)
        except ValueError as error:
            logging.error(
                'ValueError occurred while downloading asset %s', self.steam_id)
            logging.exception(error)
        except TypeError as error:
            logging.error(
                'TypeError occurred while downloading asset %s', self.steam_id)
            logging.exception(error)
        except UnidentifiedImageError as error:
            logging.critical(
                'The image for asset %s cannot be opened and identified', self.steam_id)
            logging.exception(error)
        except AttributeError as error:
            logging.error(
                'AttributeError occurred while downloading asset %s', self.steam_id)
            logging.exception(error)
        return 0
