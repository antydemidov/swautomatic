# Steam Workshop Automatic

Current Version: v0.1

**Table of Contents**

- [Steam Workshop Automatic](#steam-workshop-automatic)
  - [License](#license)
  - [Installation](#installation)
  - [Objects](#objects)
    - [Class `SWAObject`](#class-swaobject)
    - [Class `SWAAsset`](#class-swaasset)

## License

MIT License

## Installation

1. Устанавливаем MongoDB community edition
2. Заходим в `mongosh`

```powershell
mongosh
```

3. Выписываем себе пользователя `admin` и записываем `MONGO_USERNAME`, `MONGO_PASSWORD` в `.env` файл (пример лежит в `.env.example`)

```mongosh
use admin
db.createUser(
  {
    user: "<MONGO_USERNAME>",
    pwd: "<MONGO_PASSWORD>",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
  }
)
```

4. Создаем базу

```mongosh
use CSws
```

5. Создаем коллекции `assets` и `tags`

```mongosh
db.createCollection("assets")
db.createCollection("tags")
```

6. Запускаем flask

```powershell
python3 run.py
```

И переходим по адресу <http://127.0.0.1:5000>

## Objects

### Class `SWAObject`

Description

### Class `SWAAsset`

The code defines a class called `SWAAsset`. It seems to be part of a larger project (maybe a game) and it is not clear from this code what exactly the purpose of the `SWAAsset` class is.

The class has an `__init__` method that sets several instance attributes based on the arguments passed. There is also a `from_source` class method that seems to allow for the creation of an instance of the `SWAAsset` class from a dictionary of keyword arguments.

The `to_dict` method returns a dictionary representation of the instance.

The `info_steam` method retrieves information about the asset from a Steam API and returns a `dAsset` instance. The `info_database` method searches for information about the asset in a database and also returns a `dAsset` instance. There is also a `get_info` method that first searches for information about the asset in the database, and if it is not found, retrieves it from the Steam API.

The `download_preview` method downloads a preview image of the asset if it exists and stores it in a local directory.

Finally, there is a `update_stats_full` method that seems to compare the information about the asset obtained from the database and the Steam API and updates the database if the information differs. However, the method is not well defined, it contains several `FIXME` and `TODO` comments indicating that it is not yet implemented correctly.

Overall, without more context about the project and how this `Asset` class is being used, it is difficult to provide a more detailed analysis of the code.
