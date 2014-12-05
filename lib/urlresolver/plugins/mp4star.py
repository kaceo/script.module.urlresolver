"""
    urlresolver Host Plugin for mp4star.com
    Copyright (C) 2014-2015 TheHighway

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
import urllib,urllib2,re,xbmc

class MP4StarResolver(Plugin,UrlResolver,PluginSettings):
    implements=[UrlResolver,PluginSettings]
    name="mp4star"
    domain="http://mp4star.com"
    
    def __init__(self):
        p=self.get_setting('priority') or 100
        self.priority=int(p)
        self.net=Net()
        self.pattern='http://((?:www.)?mp4star.com)/\D+/(\d+)'
    
    def get_url(self,host,media_id):
        return self.domain+'/vid/'+media_id
    
    def get_host_and_id(self,url):
        r=re.search(self.pattern,url)
        if r: return r.groups()
        else: return False
    
    def valid_url(self,url,host):
        if self.get_setting('enabled')=='false': return False
        return re.match(self.pattern,url) or self.name in host
    
    def get_media_url(self,host,media_id):
        web_url=self.get_url(host,media_id)
        post_url=web_url
        hostname=self.name
        common.addon.log(web_url)
        headers={'Referer':web_url}
        try:
            resp=self.net.http_GET(web_url)
            html=resp.content
        except urllib2.URLError,e:
            common.addon.log_error(hostname+': got http error %d fetching %s'%(e.code,web_url))
            return self.unresolvable(code=3,msg='Exception: %s'%e) #return False
        data={}
        r=re.findall(r'<input type="hidden"\s*value="(.*?)"\s*name="(.+?)"',html)
        if r:
            for value,name in r: data[name]=value
            print data
            #data.update({'referer': web_url})
            #headers={'Referer':web_url}
            xbmc.sleep(4)
            try:
                html=self.net.http_POST(post_url,data,headers=headers).content
            except urllib2.URLError,e:
                #print '* failed to post url'
                common.addon.log_error(hostname+': got http error %d posting %s'%(e.code,web_url))
                return self.unresolvable(code=3,msg='Exception: %s'%e) #return False
        #try: print html+': \n'+html
        #except: print '* failed to print html.'
        #common.addon.log(html)
        r=re.search('<source src="(\D+://.+?)" type="video',html)
        if r:
            #sleep(2)
            xbmc.sleep(4)
            stream_url=urllib.unquote_plus(r.group(1))
            print stream_url
        else:
            common.addon.log_error(hostname+': stream url not found')
            return self.unresolvable(code=0,msg='no file located') #return False
        return stream_url
	
