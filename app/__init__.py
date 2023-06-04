"""
app
===
The module to make the app.
"""

from flask import Flask
from swautomatic.object import SWAObject


swa_object = SWAObject()

class Config(object):
    SECRET_KEY = swa_object.settings.secret_key or 'you-will-never-guess'


config = Config()
app = Flask(__name__)
app.config.from_object(config)

from . import views
