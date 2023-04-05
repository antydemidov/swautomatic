from flask_wtf import FlaskForm
from wtforms import FileField, RadioField, SubmitField
from wtforms.validators import InputRequired

from settings import SWASettings
from connection import Connection

settings = SWASettings()

tags = [tag['tag'] for tag in Connection(settings.database_name).get_coll('tags').find({})]


class TagsForm(FlaskForm):
    tag_choices = RadioField(choices=tags, coerce=str)
    tag_submit = SubmitField()


class SettingsForm(FlaskForm):
    common_path = FileField(validators=[InputRequired()], )
    settings_submit = SubmitField()
