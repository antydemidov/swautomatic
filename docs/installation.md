# Installation

[↑ Up](index.md)

1. Устанавливаем MongoDB community edition::
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

1. Заходим в `settings.json`. Меняем там настройки:
   - `common_path`, тут должна лежать ваша игра;
   - `user_favs_url` - это ссылка на ваши избранные, откуда программа будет подтягивать необходимые ассеты.

И переходим по адресу <http://127.0.0.1:5000> или <http://localhost:5000>
