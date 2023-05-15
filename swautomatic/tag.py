"""# swautomatic > `tag`

Module for class `SWATag`.
"""

import logging

from . import _tags_coll


class SWATag:
    """## Swautomatic > SWA_api > `SWATag`
    Simple class storing id and name of the tag

    ### Attributes
    - `tag` (str): desc."""

    def __init__(self, tag):
        self.tag = tag
        data = _tags_coll.find_one({'tag': tag})
        if not data:
            _tags_coll.insert_one({'tag': tag})
        try:
            self.tag = data['tag']
        except TypeError:
            logging.critical('The tag with name "%s" not found.', tag)
