from flask_wtf import FlaskForm
from wtforms import FileField, RadioField, SubmitField, SelectField, StringField, IntegerField, URLField
from wtforms.validators import InputRequired, URL
from connection import tags_coll, settings

tags = tags_coll.find({})
tags_names = [tag['tag'] for tag in tags]


class TagsForm(FlaskForm):
    tag_choices = RadioField(choices=tags_names, coerce=str)
    tag_submit = SubmitField()


class SettingsForm(FlaskForm):
    common_path = FileField(label='Common path', validators=[InputRequired()], default=settings.common_path)
    authmechanism = StringField(label='Authmechanism', validators=[InputRequired()], default=settings.authmechanism)
    authsource = StringField(label='Authsource', validators=[InputRequired()], default=settings.authsource)
    appid = IntegerField(label='App ID', validators=[InputRequired()], default=settings.appid)
    database_name = StringField(label='Database name', validators=[InputRequired()], default=settings.database_name)
    app_path = StringField(label='App path', validators=[InputRequired()], default=settings.app_path)
    common_path = FileField(label='Common path', validators=[], default=settings.common_path)
    user_url_profiles = URLField(label='User URL Profiles', validators=[InputRequired(), URL()], default=settings.user_url_profiles)
    user_url_id = URLField(label='User URL ID', validators=[InputRequired(), URL()], default=settings.user_url_id)
    asset_url = URLField(label='Asset URL', validators=[InputRequired(), URL()], default=settings.asset_url)
    user_favs_url = URLField(label='User Favourites URL', validators=[InputRequired(), URL()], default=settings.user_favs_url)
    links_file_path = StringField(label='Links file path', validators=[InputRequired()], default=settings.links_file_path)
    previews_path = FileField(label='Prviews path', validators=[], default=settings.previews_path)
    steam_api_url = URLField(label='Steam API URL', validators=[InputRequired(), URL()], default=settings.steam_api_url)
    timeout = SelectField(label='Timeout', coerce=float, choices=[5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 50.0], default=settings.timeout)
    longtimeout = SelectField(label='Long timeout', coerce=float, choices=[20.0, 25.0, 30.0, 50.0, 100.0, 150.0, 200.0], default=settings.longtimeout)
    per_page = SelectField(label='Cards per page', coerce=int, choices=[10, 20, 30, 50, 100], default=settings.per_page)
    settings_submit = SubmitField()


class PerPageForm(FlaskForm):
    per_page_selector = SelectField(default=settings.per_page, coerce=int, choices=[10, 20, 30, 50, 100])
