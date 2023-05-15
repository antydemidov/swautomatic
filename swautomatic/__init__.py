"""
# Swautomatic API Module

This module provides classes and functions for interacting with the Swautomatic
API. It allows users to retrieve, install, and manage Steam Workshop assets and
mods.

## Classes
- SWAObject: Represents the main API object for interacting with the Swautomatic API.
- SWAAsset: Represents a Steam Workshop asset or mod, which can be downloaded and installed.
- SWATag: Simple class storing the ID and name of a tag.
- SWAAuthor: Represents the author of a Steam Workshop asset or mod.
- SWAPreview: Represents a preview image for a Steam Workshop item.

## Functions
- validate: Validates the data against a provided JSON schema.

Note: This module requires the Swautomatic API to be properly configured and running.

## Usage

1. Create an instance of `SWAObject` by providing the base URL of the Swautomatic API.
2. Use the `SWAObject` instance to perform various operations such as retrieving
asset information, installing assets, and updating asset records in the database.

## Example

```python
# Create an instance of SWAObject
api = SWAObject()

# Retrieve asset information
asset_info = api.info_steam([12345])

# Create a SWAAsset object
asset = SWAAsset(12345, api, **asset_info[12345])

# Download and install the asset
asset.download()

# Check if the asset is installed
is_installed = asset.installed()
"""

from .asset import SWAAsset
from .author import SWAAuthor
from .connection import _assets_coll, _client, _db, _settings, _tags_coll
from .object import SWAObject
from .preview import SWAPreview
from .results import CommonResult
from .settings import SWASettings
from .tag import SWATag
from .utils import get_size_format, get_directory_size

__version__ = 'v0.1'
__author__ = 'Anton Demidov | @antydemidov'
