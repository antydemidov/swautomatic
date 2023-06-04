"""Here must be the string"""
from flask import (render_template, request, send_from_directory,  # redirect,
                   url_for)
from app.filter import LibraryFilter, FilterMonitor

from swautomatic import SWAObject, find_preview, get_size_format

from . import app
from .forms import PerPageForm, SettingsForm, TagsForm

swa_object = SWAObject()


@app.route('/')
def index():
    title = 'Swautomatic | Main'
    heading = 'Welcome'
    content = 'Steam Workshop Automatic is an app to manage assets and mods.'
    return render_template('index.html',
                           title=title,
                           heading=heading,
                           content=content,
                           )


@app.route('/library', methods=['GET', 'POST'])
def library():
    title = 'Swautomatic | Library'
    result = None
    per_page_form = PerPageForm(request.form)
    tags_form = TagsForm(request.form)

    page_num = request.args.get('p', default=1, type=int)
    tag_name = request.args.get('tag', default='', type=str)
    per_page = swa_object.settings.per_page or 20
    need_upd = request.form.get('need_upd', default=0, type=int) or request.args.get(
        'need_upd', default=0, type=int)
    library_filter = request.form.get(
        'library_filters_choices', default=0, type=int)

    if per_page_form.per_page_selector.data:
        per_page = int(per_page_form.per_page_selector.data)
        if per_page != swa_object.settings.per_page:
            swa_object.settings.update('per_page', per_page)

    tags = sorted(list(swa_object.tags.list_tags()))  # TODO: Cash it.
    tag = tags_form.tag_choices.data or tag_name or request.form.get('tag')

    # Update status
    if request.form.get('check_updates', 'false') == 'true':
        result = swa_object.assets.check_updates()
    # DANGER ZONE FULL UPDATE
    if request.form.get('total_reset', 'false') == 'true':
        result = swa_object.total_reset()
    # Update tags
    if request.form.get('update_tags', 'false') == 'true':
        result = swa_object.tags.update_tags()
    # Update database with downloading previews
    if request.form.get('update_database', 'false') == 'true':
        result = swa_object.update_database()

    is_installed = None if not library_filter else library_filter == 1
    no_need_upd = 0 if need_upd == 1 else 1

    statistics = swa_object.get_statistics()

    if (tag or need_upd != 0 or is_installed is not None or page_num != 1):
        fltr = LibraryFilter(tag=str(tag) if tag else None,
                             need_update=True if need_upd else None,
                             is_installed=is_installed)
    else:
        fltr = LibraryFilter()
        fltr.reset()

    assets_count = swa_object.assets.count_assets(tag=fltr.tag,
                                                  need_update=fltr.need_update,
                                                  is_installed=fltr.is_installed,
                                                  )

    assets_cl_list = swa_object.assets.get_assets(tag=fltr.tag,
                                                  need_update=fltr.need_update,
                                                  is_installed=fltr.is_installed,
                                                  skip=(page_num-1)*per_page,
                                                  limit=per_page
                                                  )
    last_page = assets_count // per_page + 1
    datalist = []

    for asset in assets_cl_list:
        datalist.append({
            'steamid': str(asset.steamid),
            'name': str(asset.name),
            'is_installed': asset.is_installed,
            'file_size': get_size_format(asset.file_size),
            'author_steamID': str(asset.author.steam_id),
            'author_avatarIcon': str(asset.author.avatar_icon),
        })

    filter_monitor = FilterMonitor(
        tag_message=fltr.tag if fltr.tag else 'Tag filter is not applied',
        tag_applied=fltr.tag is not None,
        need_update_message='Assets which need update' if fltr.need_update else 'Filter is not applied',
        need_update_applied=fltr.need_update != 0 and fltr.need_update is not None,
        is_installed_message='Installed assets' if fltr.is_installed else 'Filter is not applied',
        is_installed_applied=fltr.is_installed is not None,
    )

    return render_template('library.html',
                           title=title,
                           datalist=datalist,
                           page_num=page_num,
                           per_page=per_page,
                           last_page=last_page,
                           tags=tags,
                           tags_form=tags_form,
                           per_page_form=per_page_form,
                           selected_tag=tag,
                           need_upd=need_upd,
                           no_need_upd=no_need_upd,
                           statistics=statistics,
                           result=result,
                           filter_monitor=filter_monitor,
                           )


@app.route('/library/<int:steam_id>', methods=['GET', 'POST'])
def library_page(steam_id):
    asset = swa_object.assets.get_asset(int(steam_id))
    title = f"Swautomatic | {asset.name}"
    if request.form.get('download_asset', 'false') == 'true':
        asset.download()
    if request.form.get('update_asset', 'false') == 'true':
        asset.update_record()
    if request.form.get('delete_asset', 'false') == 'true':
        swa_object.assets.delete_assets([asset.steamid])

    preview_path = url_for('previews', assetid=steam_id)
    file_size = get_size_format(asset.file_size)
    files = {}
    i = 1
    for key, value in asset.get_files().items():
        files.update({key: {'id': i, 'size': get_size_format(value)}})
        i += 1
    files = files.items()
    show_time_local = asset.time_local.date().toordinal() != 719163
    return render_template('library_page.html',
                           title=title,
                           asset=asset,
                           show_time_local=show_time_local,
                           preview_path=preview_path,
                           file_size=file_size,
                           files=files,
                           )


# @app.route('/library/<int:steam_id>/download')
# def download_asset(steam_id):
#     swa_object.assets.get_asset(steam_id).download()
#     return redirect(url_for(f'library/{steam_id}'))


# @app.route('/library/<int:steam_id>/update_record')
# def update_record(steam_id):
#     swa_object.assets.get_asset(steam_id).update_record()
#     return redirect(url_for(f'library/{steam_id}'))


@app.route('/about')
def about():
    title = 'Swautomatic | About'
    heading = 'About the Swautomatic Project'
    content = 'Test content'
    return render_template('about.html',
                           title=title,
                           heading=heading,
                           content=content,
                           )


@app.route('/previews/<assetid>')
def previews(assetid):
    if swa_object.settings.previews_path:
        path = find_preview(swa_object.settings.previews_path, assetid)
    else:
        path = None
    if path is None:
        path = 'empty.jpg'
    return send_from_directory(f'../{swa_object.settings.previews_path}', path)


@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    title = 'Swautomatic | Settings'
    heading = 'Settings'

    form = SettingsForm(request.form)
    path = ''

    if request.method == 'POST':
        path = form.common_path.data
        # data = form.data

    return render_template('settings.html',
                           title=title,
                           heading=heading,
                           path=path,
                           form=form,
                           )


@app.route('/assets/<path>')
def assets(path):
    return send_from_directory('./assets/', path)
