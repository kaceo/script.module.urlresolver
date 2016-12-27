# -*- coding: utf-8 -*-
"""
openload.io urlresolver plugin
Copyright (C) 2015 tknorris

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import os
import json
import ol_gmu
from urlresolver import common
from urlresolver.common import i18n
from urlresolver.resolver import UrlResolver, ResolverError

API_BASE_URL = 'https://api.openload.co/1'
INFO_URL = API_BASE_URL + '/streaming/info'
GET_URL = API_BASE_URL + '/streaming/get?file={media_id}'
OL_PATH = os.path.join(common.plugins_path, 'ol_gmu.py')

class OpenLoadResolver(UrlResolver):
    name = "openload"
    domains = ["openload.io", "openload.co"]
    pattern = '(?://|\.)(openload\.(?:io|co))/(?:embed|f)/([0-9a-zA-Z-_]+)'

    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):
        try:
            self._auto_update(self.get_setting('url'), OL_PATH, self.get_setting('key'))
            reload(ol_gmu)
            return ol_gmu.get_media_url(self.get_url(host, media_id))
        except Exception as e:
            common.log_utils.log_debug('Exception during openload resolve parse: %s' % (e))
            try:
                video_url = self.__check_auth(media_id)
                if not video_url:
                    video_url = self.__auth_ip(media_id)
            except ResolverError:
                raise
            
            if video_url:
                return video_url
            else:
                raise ResolverError(i18n('no_ol_auth'))

    def get_url(self, host, media_id):
        return 'http://openload.co/embed/%s' % (media_id)

    def __auth_ip(self, media_id):
        js_data = self.__get_json(INFO_URL)
        pair_url = js_data.get('result', {}).get('auth_url', '')
        if pair_url:
            pair_url = pair_url.replace('\/', '/')
            header = i18n('ol_auth_header')
            line1 = i18n('auth_required')
            line2 = i18n('visit_link')
            line3 = i18n('click_pair') % (pair_url)
            with common.kodi.CountdownDialog(header, line1, line2, line3) as cd:
                return cd.start(self.__check_auth, [media_id])
        
    def __check_auth(self, media_id):
        try:
            js_data = self.__get_json(GET_URL.format(media_id=media_id))
        except ResolverError as e:
            status, msg = e
            if status == 403:
                return
            else:
                raise ResolverError(msg)
        
        return js_data.get('result', {}).get('url')
    
    def __get_json(self, url):
        result = self.net.http_GET(url).content
        js_result = json.loads(result)
        common.log_utils.log_debug(js_result)
        if js_result['status'] != 200:
            raise ResolverError(js_result['status'], js_result['msg'])
        return js_result

    @classmethod
    def get_settings_xml(cls):
        xml = super(cls, cls).get_settings_xml()
        xml.append('<setting id="%s_auto_update" type="bool" label="%s" default="true"/>' % (cls.__name__, i18n('auto_update')))
        xml.append('<setting id="%s_url" type="text" label="    %s" default="" visible="eq(-1,true)"/>' % (cls.__name__, i18n('update_url')))
        xml.append('<setting id="%s_key" type="text" label="    %s" default="" option="hidden" visible="eq(-2,true)"/>' % (cls.__name__, i18n('decrypt_key')))
        xml.append('<setting id="%s_etag" type="text" default="" visible="false"/>' % (cls.__name__))
        return xml
