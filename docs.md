# Steam Workshop Automatic

Current Version: v0.1

## Table of Contents

- [Steam Workshop Automatic](#steam-workshop-automatic)
  - [Table of Contents](#table-of-contents)
  - [License](#license)
  - [Installation](#installation)
  - [Objects](#objects)
    - [Class `SWAObject`](#class-swaobject)
    - [Class `SWAAsset`](#class-swaasset)
      - [SWAAsset.`to_dict()`](#swaassetto_dict)
      - [SWAAsset.`download()`](#swaassetdownload)

## License

MIT License

## Installation

1. Устанавливаем MongoDB community edition
1. Заходим в `mongosh`

    ```powershell
    mongosh
    ```

1. Выписываем себе пользователя `admin` и записываем `MONGO_USERNAME`, `MONGO_PASSWORD` в `.env` файл (пример лежит в `.env.example`)

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

1. Создаем базу

    ```mongosh
    use CSws
    ```

1. Создаем коллекции `assets` и `tags`

    ```mongosh
    db.createCollection("assets")
    db.createCollection("tags")
    ```

1. Запускаем flask

    ```powershell
    python3 run.py
    ```

И переходим по адресу <http://127.0.0.1:5000> или <http://localhost:5000>

## Objects

### Class `SWAObject`

Description

### Class `SWAAsset`

The code defines a class called `SWAAsset`. It seems to be part of a larger project (maybe a game) and it is not clear from this code what exactly the purpose of the `SWAAsset` class is.

The class has an `__init__` method that sets several instance attributes based on the arguments passed. There is also a `from_source` class method that seems to allow for the creation of an instance of the `SWAAsset` class from a dictionary of keyword arguments.

#### SWAAsset.`to_dict()`

[Up](#steam-workshop-automatic)

Description

#### SWAAsset.`download()`

[Up](#steam-workshop-automatic)

Description
