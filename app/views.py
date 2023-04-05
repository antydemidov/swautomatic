from flask import (render_template, request, send_from_directory,
                   url_for)

from app import app
from connection import Connection
from forms import *
from settings import SWASettings
from SWA_api import Asset, SWAObject

swa_object = SWAObject()
settings = SWASettings().load().validate()
db = Connection(settings.database_name)
assets_db = db.get_coll('assets')
tags_db = db.get_coll('tags')

@app.route('/')
def index():
    title = 'Steam Workshop Automatic'
    heading = 'Welcome'
    content = 'Steam Workshop Automatic is an app to manage assets and mods.'
    return render_template('index.html',
                           title=title,
                           heading=heading,
                           content=content)

@app.route('/library', methods=['GET', 'POST'])
def library():
    title = 'SWA | Library'
    heading = ''
    page_num = request.args.get('p', default=1, type=int)
    tag_name = request.args.get('tag', default='', type=str)
    per_page = request.args.get('pp', default=20, type=int)
    need_upd = request.args.get('show_need_upd', default=0, type=int)
    library_filter = None

    if request.method == 'POST':
        library_filter = request.form.get('library_filters_choices', default=0, type=int)

    tags = [tag['tag'] for tag in list(tags_db.find({}))]
    tags_form = TagsForm(request.form)
    selected_tag = tags_form.tag_choices.data or tag_name or request.form.get('tag')
    show_need_upd = request.form.get('show_need_upd', type=int) or need_upd
    fltr = {}
    if selected_tag:
        tag = tags_db.find_one({'tag': selected_tag})
        fltr.update({'tags': tag['_id']})
    if (request.method == 'POST' and request.form.get('update') == 'true'):
        swa_object.check_updates()
    if show_need_upd:
        fltr.update({'need_update': True})

    if library_filter == 1:
        fltr.update({'need_update': True})
    if library_filter == 2:
        fltr.update({'is_installed': True})
    if library_filter == 3:
        fltr.update({'is_installed': False})

    if show_need_upd == 1: no_show_need_upd = 0
    elif show_need_upd == 0: no_show_need_upd = 1

    assets_count = assets_db.count_documents(fltr)
    last_page = assets_count // per_page + 1
    assets_list = [asset['steamid'] for asset in list(assets_db.find(fltr, limit=per_page, skip=(page_num-1)*per_page))]
    assets_cl_list = [Asset(asset) for asset in assets_list]
    for asset in assets_cl_list:
        asset.get_stats()
    datalist = []
    for i in range(len(assets_cl_list)):
        if assets_cl_list[i].info.is_installed == True:
            color = 'lightcoral'
            hover_title = 'Installed'
            display = 'flex'
        else:
            color = '#0000'
            hover_title = 'Not installed'
            display = 'none'
        datalist.append({
            'id': str(assets_cl_list[i].id),
            'name': str(assets_cl_list[i].info.name),
            'is_installed': str(assets_cl_list[i].info.is_installed),
            'file_size': str(round(assets_cl_list[i].info.file_size/1024/1024, 3)) + ' MB',
            'author_steamID': str(assets_cl_list[i].info.author.steamID),
            'author_avatarIcon': str(assets_cl_list[i].info.author.avatarIcon),
            'hover_title': hover_title,
            'style': 'color:' + color + '; display: ' + display,
            'need_update': str(assets_cl_list[i].info.need_update),
            'preview_path': url_for('previews', assetid=assets_cl_list[i].info.preview_path.split('/')[-1])
        })
            
    return render_template('library.html',
                           title=title,
                           heading=heading,
                           datalist=datalist,
                           page_num=page_num,
                           per_page=per_page,
                           last_page=last_page,
                           tags=tags,
                           tags_form=tags_form,
                           selected_tag=selected_tag,
                           show_need_upd=show_need_upd,
                           no_show_need_upd=no_show_need_upd)


@app.route('/library/<id>', methods=['GET', 'POST'])
def library_page(id):
    asset = Asset(id)
    asset.get_stats()
    if (request.method == 'POST' and request.form['download_asset'] == 'true'):
        asset.download()
        asset.get_stats()
    asset_details = asset.info
    asset_details.preview_path = url_for('previews', assetid=asset.info.preview_path.split('/')[-1])
    asset_details.file_size = round(asset_details.file_size/1024/1024, 3)
    asset_details.tags = [tag.tag for tag in asset_details.tags]
    return render_template('library_page.html',
        asset_details=asset_details)


@app.route('/about')
def about():
    title = 'SWA | About'
    heading = 'Welcome'
    content = ''
    return render_template('library.html',
                           title=title,
                           heading=heading,
                           content=content)


@app.route('/previews/<assetid>')
def previews(assetid):
    path = assetid
    return send_from_directory('../previews', path)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    title = 'SWA | Settings'
    heading = 'Settings'

    form = SettingsForm(request.form)
    path = ''

    if request.method == 'POST':
        path = form.common_path.data

    return render_template('settings.html',
                           title=title,
                           heading=heading,
                           path=path,
                           form=form)
