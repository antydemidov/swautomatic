from flask_wtf import FlaskForm
from wtforms import FileField, RadioField, SubmitField
from wtforms.validators import InputRequired
from connection import tags_coll

tags = tags_coll.find({})
tags_names = [tag['tag'] for tag in tags]


class TagsForm(FlaskForm):
    tag_choices = RadioField(choices=tags, coerce=str)
    tag_submit = SubmitField()


class SettingsForm(FlaskForm):
    common_path = FileField(validators=[InputRequired()], )
    settings_submit = SubmitField()
