"""Here must be the string"""
import os
from flask import render_template, request, send_from_directory, url_for
from app import app
from connection import assets_coll, tags_coll, settings
from forms import SettingsForm, TagsForm, PerPageForm
from swa_api import SWAAsset, SWAObject
from utils import get_size_format

swa_object = SWAObject()


@app.route('/')
def index():
    title = 'SWA | Main'
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
    per_page = swa_object.settings.per_page
    need_upd = request.form.get('show_need_upd', default=0, type=int)
    library_filter = request.form.get(
        'library_filters_choices', default=0, type=int)

    per_page_form = PerPageForm(request.form)
    if per_page_form.per_page_selector.data:
        per_page = int(per_page_form.per_page_selector.data)
        if per_page != settings.per_page:
            settings.update('per_page', per_page)

    tags = sorted([tag['tag'] for tag in list(tags_coll.find({}))])
    tags_form = TagsForm(request.form)
    selected_tag = tags_form.tag_choices.data or tag_name or request.form.get('tag')
    fltr = {}
    if selected_tag:
        tag = tags_coll.find_one({'tag': selected_tag})
        fltr.update({'tags': tag['tag']})
    # Update status
    if request.form.get('check_updates', 'false') == 'true':
        swa_object.check_updates()
    # DANGER ZONE FULL UPDATE
    if request.form.get('total_reset', 'false') == 'true':
        # swa_object.total_reset()
        pass
    if request.form.get('update_tags', 'false') == 'true':
        swa_object.update_tags()
    if request.form.get('update_database', 'false') == 'true':
        swa_object.update_database()

    if need_upd:
        fltr.update({'need_update': True})

    # if library_filter == 0: do nothing
    if library_filter == 1:
        fltr.update({'is_installed': True})
    if library_filter == 2:
        fltr.update({'is_installed': False})

    no_need_upd = 0 if need_upd == 1 else 1

    assets_count = assets_coll.count_documents(fltr)
    last_page = assets_count // per_page + 1
    assets_list = [asset['steamid'] for asset in list(
        assets_coll.find(fltr, limit=per_page, skip=(page_num-1)*per_page))]
    assets_cl_list = swa_object.get_assets(assets_list)
    datalist = []

    statistics = swa_object.get_statistics()

    for asset in assets_cl_list:
        datalist.append({
            'steamid': str(asset.steamid),
            'name': str(asset.name),
            'is_installed': asset.is_installed,
            'file_size': get_size_format(asset.file_size),
            'author_steamID': str(asset.author.steam_id),
            'author_avatarIcon': str(asset.author.avatar_icon),
            # 'need_update': asset.need_update,
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
                           per_page_form=per_page_form,
                           selected_tag=selected_tag,
                           show_need_upd=need_upd,
                           no_show_need_upd=no_need_upd,
                           statistics=statistics,
                           )


@app.route('/library/<steam_id>', methods=['GET', 'POST'])
def library_page(steam_id):
    asset = SWAAsset(int(steam_id), swa_object)
    if request.form.get('download_asset', 'false') == 'true':
        asset.download()
    if request.form.get('update_asset', 'false') == 'true':
        asset.update_record()

    preview_path = url_for('previews', assetid=steam_id)
    file_size = get_size_format(asset.file_size)
    files = {}
    i = 1
    for key, value in asset.get_files().items():
        files.update({key: {'id': i, 'size': get_size_format(value)}})
        i += 1
    files = files.items()
    return render_template('library_page.html',
                           asset=asset,
                           preview_path=preview_path,
                           file_size=file_size,
                           files=files,
                           )


@app.route('/about')
def about():
    title = 'SWA | About'
    heading = 'About the SWA Project'
    content = 'Test content'
    return render_template('about.html',
                           title=title,
                           heading=heading,
                           content=content)


@app.route('/previews/<assetid>')
def previews(assetid):
    path = 'empty.jpg'
    assetid = str(assetid)
    for file in os.listdir(settings.previews_path):
        if assetid in file:
            path = file
    return send_from_directory(f'../{settings.previews_path}', path)


@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    title = 'SWA | Settings'
    heading = 'Settings'

    form = SettingsForm(request.form)
    path = ''

    if request.method == 'POST':
        path = form.common_path.data
        data = form.data

    return render_template('settings.html',
                           title=title,
                           heading=heading,
                           path=path,
                           form=form)
