# Steam Workshop Automatic

Python & Flask web-app that automatically updates mods for the game.

## Подъем приложения локально
1. Устанавливаем MongoDB community edition
2. Заходим в `mongosh`
```
mongosh
```
3. Выписываем себе пользователя `admin` и записываем `MONGO_USERNAME`, `MONGO_PASSWORD` в `.env` файл (пример лежит в `.env.example`)
```
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
```
use CSws
```
5. Создаем коллекции `assets` и `tags`
```
db.createCollection("assets")
db.createCollection("tags")
```
6. Запускаем flask
```
python3 run.py
```
И переходим по адресу http://127.0.0.1:5000
