# `SWAObject`

[↑ Up](index.md)

Description

## Swautomatic > SWA_api > `SWAObject`

The main object of Swautomatic project.

Attributes

- `client` (pymongo.MongoClient): A MongoDB client object.
- `settings` (SWASettings): An object representing Swautomatic settings.

Methods

- `get_asset()`: Retrieves a SWAAsset object for the specified asset steam ID.
- `get_assets()`: Retrieves a list of SWAAsset objects based on the provided parameters.
- `get_statistics()`: The method returns a CommonResult object that contains the retrieved statistics.

### Swautomatic > SWA_api > SWAObject.`get_asset()`

Retrieves a SWAAsset object for the specified asset steam ID.

Parameters

- `steam_id` (int): The steam ID of the asset.

Return

The SWAAsset object representing the asset.

### Swautomatic > SWA_api > SWAObject.`get_assets()`

> !!! It works only with assets in database. Assets which not exists will be empty.

Example

```python
swa_object = SWAObject()
swa_object.get_assets([123, 321])
```

Parameters

- `steam_ids` (list): a list of assets steam ids.
- `skip` (integer): a number of records to skip.
- `limit` (integer): a number of records to show.

Return

A list of SWAAsset objects.
