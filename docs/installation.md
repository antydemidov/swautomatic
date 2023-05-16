# Installation

[↑ Up](index.md)

1. Устанавливаем MongoDB community edition::
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

И переходим по адресу <http://127.0.0.1:5000> или <http://localhost:5000>
