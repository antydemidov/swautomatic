"""Here must be the string"""
from flask import render_template, request, send_from_directory, url_for
from app import app
from connection import assets_coll, tags_coll#, client, settings,
from forms import SettingsForm, TagsForm, PerPageForm
from SWA_api import SWAAsset, SWAObject

swa_object = SWAObject()

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
    per_page = swa_object.settings.per_page
    need_upd = request.args.get('show_need_upd', default=0, type=int)
    library_filter = request.form.get('library_filters_choices', default=0, type=int)

    per_page_form = PerPageForm(request.form)
    if per_page_form.per_page_selector.data:
        per_page = int(per_page_form.per_page_selector.data)

    tags = [tag['tag'] for tag in list(tags_coll.find({}))]
    tags_form = TagsForm(request.form)
    selected_tag = tags_form.tag_choices.data or tag_name or request.form.get('tag')
    fltr = {}
    if selected_tag:
        tag = tags_coll.find_one({'tag': selected_tag})
        fltr.update({'tags': tag['_id']})
    if request.form.get('update_database') == 'true':
        swa_object.check_updates()
    if need_upd:
        fltr.update({'need_update': True})

    if library_filter == 2:
        fltr.update({'is_installed': True})
    if library_filter == 3:
        fltr.update({'is_installed': False})

    if need_upd == 1:
        no_need_upd = 0
    elif need_upd == 0:
        no_need_upd = 1

    assets_count = assets_coll.count_documents(fltr)
    last_page = assets_count // per_page + 1
    assets_list = [asset['steamid'] for asset in list(
        assets_coll.find(fltr, limit=per_page, skip=(page_num-1)*per_page))]
    assets_cl_list = [SWAAsset(asset, swa_object) for asset in assets_list]
    for asset in assets_cl_list:
        asset.get_info()
    datalist = []

    for asset in assets_cl_list:
        if asset.info['is_installed']:
            color = 'lightcoral'
            hover_title = 'Installed'
            display = 'flex'
        else:
            color = '#0000'
            hover_title = 'Not installed'
            display = 'none'
        datalist.append({
            'id': str(asset.steamid),
            'name': str(asset.info['name']),
            'is_installed': str(asset.info['is_installed']),
            'file_size': str(round(asset.info['file_size']/1024/1024, 3)) + ' MB',
            'author_steamID': str(asset.info['author']['steamID']),
            'author_avatarIcon': str(asset.info['author']['avatarIcon']),
            'hover_title': hover_title,
            'style': f'color: {color}; display: {display}',
            'need_update': str(asset.info['need_update']),
            'preview_path': url_for(
                'previews', assetid=asset.info['preview_path'].split('/')[-1])
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
                           no_show_need_upd=no_need_upd)


@app.route('/library/<id>', methods=['GET', 'POST'])
def library_page(id):
    asset = SWAAsset(int(id), swa_object)
    asset.get_info()
    if (request.method == 'POST' and request.form['download_asset'] == 'true'):
        asset.download()
        asset.get_info()
    asset_details = asset.info
    asset_details['preview_path'] = url_for(
        'previews',
        assetid=asset.info['preview_path'].split('/')[-1]
    )
    asset_details['file_size'] = round(asset_details['file_size']/1024/1024, 3)
    asset_details['tags'] = [tag.tag for tag in asset_details['tags']]
    return render_template('library_page.html',
                           asset_details=asset_details)


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
    path = assetid
    return send_from_directory('../previews', path)

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
