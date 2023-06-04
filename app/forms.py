"""
forms
=====
Contatains the froms for the app.
"""

from flask_wtf import FlaskForm
from wtforms import (FileField, IntegerField, RadioField, SelectField,
                     StringField, SubmitField, URLField)
from wtforms.validators import URL, InputRequired

from . import swa_object

__all__ = ['TagsForm',
           'SettingsForm',
           'PerPageForm',
           ]

tags = sorted(list(swa_object.tags.list_tags()))
timeout_choices = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 50.0]
longtimeout_choices = [20.0, 25.0, 30.0, 50.0, 100.0, 150.0, 200.0]
per_page_choices = [10, 20, 30, 50, 100]


class TagsForm(FlaskForm):
    """
    app > forms > `TagsForm`
    ------------------------
    Description.
    """
    tag_choices = RadioField(choices=tags, coerce=str)
    tag_submit = SubmitField()


class SettingsForm(FlaskForm):
    """
    app > forms > `SettingsForm`
    ----------------------------
    The form for settings of the app.
    """
    common_path       = FileField(label='Common path',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.common_path)
    authmechanism     = StringField(label='Authmechanism',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.authmechanism)
    authsource        = StringField(label='Authsource',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.authsource)
    appid             = IntegerField(label='App ID',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.appid)
    database_name     = StringField(label='Database name',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.database_name)
    app_path          = StringField(label='App path',
                                  validators=[InputRequired()],
                                  default=swa_object.settings.app_path)
    common_path       = FileField(label='Common path',
                                  validators=[],
                                  default=swa_object.settings.common_path)
    user_url_profiles = URLField(label='User URL Profiles',
                                  validators=[InputRequired(), URL()],
                                  default=swa_object.settings.user_url_profiles)
    user_url_id       = URLField(label='User URL ID',
                                  validators=[InputRequired(), URL()],
                                  default=swa_object.settings.user_url_id)
    asset_url         = URLField(label='Asset URL',
                                  validators=[InputRequired(), URL()],
                                  default=swa_object.settings.asset_url)
    user_favs_url     = URLField(label='User Favourites URL',
                                  validators=[InputRequired(), URL()],
                                  default=swa_object.settings.user_favs_url)
    previews_path     = FileField(label='Prviews path',
                                  validators=[],
                                  default=swa_object.settings.previews_path)
    steam_api_url     = URLField(label='Steam API URL',
                                  validators=[InputRequired(), URL()],
                                  default=swa_object.settings.steam_api_url)
    timeout           = SelectField(label='Timeout',
                                  choices=timeout_choices,
                                  default=swa_object.settings.timeout)
    longtimeout       = SelectField(label='Long timeout',
                                  choices=longtimeout_choices,
                                  default=swa_object.settings.longtimeout)
    per_page          = SelectField(label='Cards per page',
                                  choices=per_page_choices,
                                  default=swa_object.settings.per_page)


class PerPageForm(FlaskForm):
    """
    app > forms > `PerPageForm`
    ---------------------------
    Description.
    """
    per_page_selector = SelectField(
        default=swa_object.settings.per_page, choices=per_page_choices)
