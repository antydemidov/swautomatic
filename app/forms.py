from flask_wtf import FlaskForm
from wtforms import (FileField, RadioField, SubmitField,
                     SelectField, StringField, IntegerField, URLField)
from wtforms.validators import InputRequired, URL
from swautomatic.connection import _tags_coll, _settings

tags = _tags_coll.find({})
tags_names = sorted([tag['tag'] for tag in tags])


class TagsForm(FlaskForm):
    tag_choices = RadioField(choices=tags_names, coerce=str)
    tag_submit = SubmitField()


class SettingsForm(FlaskForm):
    common_path = FileField(
        label='Common path', validators=[InputRequired()], default=_settings.common_path)
    authmechanism = StringField(
        label='Authmechanism', validators=[InputRequired()], default=_settings.authmechanism)
    authsource = StringField(
        label='Authsource', validators=[InputRequired()], default=_settings.authsource)
    appid = IntegerField(
        label='App ID', validators=[InputRequired()], default=_settings.appid)
    database_name = StringField(
        label='Database name', validators=[InputRequired()], default=_settings.database_name)
    app_path = StringField(
        label='App path', validators=[InputRequired()], default=_settings.app_path)
    common_path = FileField(
        label='Common path', validators=[], default=_settings.common_path)
    user_url_profiles = URLField(
        label='User URL Profiles', validators=[InputRequired(), URL()], default=_settings.user_url_profiles)
    user_url_id = URLField(
        label='User URL ID', validators=[InputRequired(), URL()], default=_settings.user_url_id)
    asset_url = URLField(
        label='Asset URL', validators=[InputRequired(), URL()], default=_settings.asset_url)
    user_favs_url = URLField(
        label='User Favourites URL', validators=[InputRequired(), URL()], default=_settings.user_favs_url)
    previews_path = FileField(
        label='Prviews path', validators=[], default=_settings.previews_path)
    steam_api_url = URLField(
        label='Steam API URL', validators=[InputRequired(), URL()], default=_settings.steam_api_url)
    timeout = SelectField(
        label='Timeout', coerce=float, choices=[5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 50.0], default=_settings.timeout)
    longtimeout = SelectField(
        label='Long timeout', coerce=float, choices=[20.0, 25.0, 30.0, 50.0, 100.0, 150.0, 200.0], default=_settings.longtimeout)
    per_page = SelectField(
        label='Cards per page', coerce=int, choices=[10, 20, 30, 50, 100], default=_settings.per_page)


class PerPageForm(FlaskForm):
    per_page_selector = SelectField(
        default=_settings.per_page, coerce=int, choices=[10, 20, 30, 50, 100])
