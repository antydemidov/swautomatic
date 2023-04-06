import os

import dotenv


dotenv.load_dotenv()


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    HOST = os.environ.get('HOST') or 'you-will-never-guess'
    PORT = os.environ.get('PORT') or 'you-will-never-guess'
    MONGO_USERNAME = os.environ.get('MONGO_USERNAME') or 'you-will-never-guess'
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD') or 'you-will-never-guess'
