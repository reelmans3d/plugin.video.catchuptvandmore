# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download

from bs4 import BeautifulSoup as bs

import re
import urlquick


# TO DO
# ....


URL_ROOT = 'https://www.rtc.be'

URL_LIVE = URL_ROOT + '/live'

URL_VIDEOS = URL_ROOT + '/videos'

URL_EMISSIONS = URL_ROOT + '/emissions'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id,
        next_url=URL_VIDEOS,
        page='0')
    yield item

    item = Listitem()
    item.label = plugin.localize(LABELS['All programs'])
    item.set_callback(
        list_programs,
        item_id=item_id)
    yield item


@Route.register
def list_programs(plugin, item_id):

    resp = resp = urlquick.get(URL_EMISSIONS)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='col-sm-4')

    for program_datas in list_programs_datas:

        program_title = program_datas.find('h3').text
        program_image = URL_ROOT + '/' + program_datas.find(
            'img').get('src')
        program_url = URL_ROOT + '/' + program_datas.find(
            "a").get("href")

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            next_url=program_url,
            page='0')
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, page):

    resp = urlquick.get(next_url + '?lim_un=%s' % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='col-sm-4')

    for video_datas in list_videos_datas:
        video_title = video_datas.find('h3').text
        video_image = video_datas.find('img').get('src')
        video_url = video_datas.find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        next_url=next_url,
        page=str(int(page) + 12))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url, max_age=-1)
    list_streams_datas = re.compile(
        r'source src="(.*?)"').findall(resp.text)
    stream_url = ''
    for stream_datas in list_streams_datas:
        if 'm3u8' in stream_datas or \
                'mp4' in stream_datas:
            stream_url = stream_datas

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE)
    root_soup = bs(resp.text, 'html.parser')
    stream_datas_url = 'https:' + root_soup.find(
        'iframe').get('src')
    resp2 = urlquick.get(stream_datas_url)
    root_soup2 = bs(resp2.text, 'html.parser')
    return 'https:' + root_soup2.find(
        'source').get('src')
