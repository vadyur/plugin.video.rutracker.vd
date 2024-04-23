# -*- coding: utf-8 -*-
# ver 1.2

__all__ = ['UrlLink', 'Link', 'Handler', 'Plugin', 'Setting', 'Lang', '_setting', '_lang']

import sys
import os
import urllib
import json

import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from urllib.parse import urlencode, quote_plus, unquote_plus, parse_qsl
from typing import Dict, Any

MODE = {
    'list':  50,
    'full':  51,
    'icon':  54,
    'round': 501,
    'thumb': 500
}

class UrlLink:
    def __init__(self, url):
        self.url = url

class Link(UrlLink):
    def __init__(self, route: str, argv=None, container=False, container_replace=False, ver=1):
        # if str(type(route)) == "<type 'classobj'>": route = route.__name__.lower()
        app: Dict[str, Any] = {'route': route}
        if argv is not None:
            if ver == 3 and isinstance(argv, dict):
                for key in argv:
                     app[key] = argv[key]
            else:
                app['argv'] = argv
        if container:
            app['container'] = container
        if container_replace:
            app['container_replace'] = container_replace
        if ver > 1:
            self.url = sys.argv[0] + '?' + urlencode(app)
        else:
            self.url = sys.argv[0] + '?' + quote_plus(json.dumps(app))


class Handler:
    def __init__(self, gsetting=None, link=None, argv=None):
        if argv is None: self.argv = {}
        else: self.argv = argv
        self.link = link
        self.plugin = sys.argv[0].replace('plugin://', '').replace('/', '')
        self.addon = xbmcaddon.Addon(id=self.plugin)
        self.nameaddon = xbmc.getInfoLabel('System.AddonTitle(%s)' % self.plugin)
        self.p_info = UrlLink('#Action(Info)')
        self.p_settings = UrlLink('#Addon.OpenSettings(%s)' % self.plugin)
        self.popup = [(self.p_info, 'Информация'), (self.p_settings, 'Настройки дополнения')]
        self.popupend = None
        self.setting = Setting()
        self.lang = Lang()
        self.is_listitem = False
        self.is_render = False
        if gsetting is None: self._gsetting = {}
        else: self._gsetting = gsetting
        self.busyrun = None
        self.busy = None
        self.progressrun = None
        self.progress = xbmcgui.DialogProgress()
        self.enable_progress = True
        self.enable_hide_all = True
        self.kodi_ver = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def item(self, link, **kwarg):
        item = xbmcgui.ListItem()

        if 'title' in kwarg and kwarg['title']:
            item.setLabel(kwarg['title'])

        if 'label' in kwarg and kwarg['label']:
            item.setLabel2(kwarg['label'])

        art = {}
        fanart = self._gsetting.get('fanart')
        if 'fanart' in kwarg and kwarg['fanart']:
            fanart = kwarg['fanart']
        if fanart:
            art['fanart'] = fanart
        if 'icon' in kwarg and kwarg['icon']:
            art['icon'] = kwarg['icon']
        if 'thumb' in kwarg and kwarg['thumb']:
            art['thumb'] = kwarg['thumb']
            art['poster'] = kwarg['thumb']
        if art:
            item.setArt(art)

        if 'popup' in kwarg and kwarg['popup']:
            replace = False
            if 'popup_replace' in kwarg and kwarg['popup_replace']:
                replace = True
            menu = []
            popups = kwarg['popup']
            if isinstance(popups, bool): popups = self.popupend if self.popupend else self.popup
            for m in popups:
                #if len(m) > 2:
                #    if len(m) > 3:
                #        menu.append((m[1], 'Container.Update(%s,replace)' % m[0].url))
                #    else:
                #        menu.append((m[1], 'Container.Update(%s)' % m[0].url))
                #else:
                #    menu.append((m[1], 'XBMC.runPlugin(%s)' % m[0].url))
                if m[0].url[0] == '#':
                     menu.append((m[1], '%s' % m[0].url[1:]))
                else:
                     menu.append((m[1], 'XBMC.runPlugin(%s)' % m[0].url))
            item.addContextMenuItems(menu, replace)


        if 'media' in kwarg and kwarg['media'] and 'info' in kwarg and kwarg['info']:
            item.setInfo(kwarg['media'], kwarg['info'])

        if 'cast' in kwarg and kwarg['cast']:
           if self.kodi_ver > 16:
                item.setCast(kwarg['cast'])

        if 'property' in kwarg and kwarg['property']:
            for key, value in kwarg['property']:
                item.setProperty(key, value)

        folder = True
        if 'folder' in kwarg and not kwarg['folder']:
            folder = False

        if 'playable' in kwarg and kwarg['playable']:
            folder = False
            item.setProperty('IsPlayable','true')

        total = None
        if 'total' in kwarg and kwarg['total']:
            total = kwarg['total']

        self.add(link.url, item, folder, total)


    def add(self, url, item, folder=True, total=None):
        if total is None:
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, item, folder)
        else:
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, item, folder, total)
        self.is_listitem = True

    def render(self, **kwarg):
        if self.is_listitem and not self.is_render:

            replace = False
            if 'replace' in kwarg and kwarg['replace']:
                replace = True

            xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=replace)

            if 'mode' in kwarg:
                xbmc.executebuiltin("Container.SetViewMode(%s)" % MODE[kwarg['mode']])

            if ('nextmode' in kwarg) and ('mode' not in kwarg):
                n = kwarg['nextmode']
                self.setviewmode(n)

        self.is_render = True


    def setviewmode(self, n):
        n = int(n)
        if n>0:
                xbmc.sleep(200)
                xbmc.executebuiltin("Container.SetViewMode(0)")
                for i in range(1,n):
                        xbmc.executebuiltin("Container.NextViewMode")


    def run(self, link, replace=False):
        if not xbmc.getCondVisibility('Window.IsMedia'):
            xbmc.executebuiltin('ActivateWindow(videos,%s,return)' % link.url)
        elif replace:
            xbmc.executebuiltin('Container.Update(%s,replace)' % link.url)
        else:
            xbmc.executebuiltin('Container.Update(%s)' % link.url)

    def message(self, title: str, msg: str, times=5000, icon=None):
        try:
            xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (title, msg, times, icon))
        except Exception as e:
            xbmc.log('XBMCup: Handler: ' + str(e), xbmc.LOGERROR)

    def path(self, *path):
        dirname = [xbmcvfs.translatePath('special://temp'), 'xbmcup', self.plugin, 'data']
        if path:
            dirname.extend(path)
        return os.path.join(*dirname)

    def handle(self):
        raise NotImplementedError()

    def kbdinput(self, title, textsearch=''):
        kb = xbmc.Keyboard(textsearch, title)
        kb.doModal()
        if kb.isConfirmed():
                return kb.getText()
        return None

    def popupreset(self):
        self.popupend = []
        self.popupend.extend(self.popup)

    def popupadd(self, link: str, text: str, resetpopup=False, start=False):
        if self.popupend is None or resetpopup:
            self.popupreset()
        if self.popupend is None:
            self.popupend = []
        if start:
            self.popupend[0] = ( link, text )
        else:
            self.popupend.insert(-1, ( link, text ) )

    def show_busy(self):
        if not self.busyrun:
             if self.kodi_ver > 17:
                 xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
             elif self.kodi_ver > 16:
                 xbmc.executebuiltin('ActivateWindow(busydialog)')
             else:
                 self.busy = xbmcgui.DialogProgress()
                 self.busy.create("Wait...")
             self.busyrun = True

    def hide_busy(self):
        if self.busyrun:
             if self.kodi_ver > 17:
                 xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
             elif self.kodi_ver > 16:
                 xbmc.executebuiltin('Dialog.Close(busydialog)')
             else:
                 self.busy.close()  # type: ignore
             self.busyrun = False

    def show_progress(self, title, text=''):
        if not self.progressrun and self.enable_progress:
              if isinstance(text, str):  text = [text]
              self.progress.create(title, *text)
              self.progressrun = True

    def update_progress(self, procent, text=''):
        if self.progressrun:
              if isinstance(text, str):  text = [text]
              self.progress.update(int(procent), *text)

    def iscanceled_progress(self):
        if self.progressrun:
          return self.progress.iscanceled()

    def hide_progress(self):
        if self.progressrun:
              self.progress.close()
              self.progressrun = False


    def __del__(self):
        if self.enable_hide_all:
             self.hide_busy()
             self.hide_progress()


class ThisIsNotClassError(BaseException):
    ...


class Plugin:
    def __init__(self, *handler):
        dirname = xbmcvfs.translatePath('special://temp')
        for subdir in ('xbmcup', sys.argv[0].replace('plugin://', '').replace('/', ''), 'data'):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)

        self._index = None
        self._route = []
        self._global_setting = {}

        if handler:
            self.route(handler[0])
            for i in range(1, len(handler), 2):
                self.route(handler[i], handler[i+1])

    def route(self, route, handler=None):
        if handler is None:
            self._index = route
        else:
            self._route.append((route, handler))

    def radd(self, route=None):
        def wrap(cls, route=route):
            if str(type(cls)) != "<type 'classobj'>": raise ThisIsNotClassError()
            if route is None: route = cls.__name__.lower()
            if route == '/' or route == 'menu': self.route(cls)
            else: self.route(route, cls)
            return cls
        return wrap

    def rcls(self, handler):
        if str(type(handler)) == "<type 'classobj'>":
                route = handler.__name__.lower()
                self.route(route, handler)
        else: raise ThisIsNotClassError()

    def run(self, **kwarg):
        xbmc.log('XBMCup: Plugin: sys.argv: ' + str(sys.argv), xbmc.LOGDEBUG)

        if len(sys.argv) > 2 and sys.argv[2]:
            if sys.argv[2][1] == '%':
               link_t = json.loads(unquote_plus(sys.argv[2][1:]))
            else:
               params =  parse_qsl(sys.argv[2][1:])
               link_t = {}
               for key, value in params:
                       if '{' in value or '[' in value:
                            try:
                                 link_t[key] = eval(value)
                            except:
                                 link_t[key] = value
                       elif value == 'True':
                            link_t[key] = True
                       elif value == 'False':
                            link_t[key] = False
                       elif value == 'None':
                            link_t[key] = None
                       else:
                            link_t[key] = value
               if 'route' not in link_t and 'usearch' in link_t:
                  link_t['route'] = 'usearch'
               if 'argv' not in link_t:
                  argv_t = {}
                  for key in link_t:
                       if key in ('route', 'container', 'container_replace'): continue
                       else:
                          argv_t[key] = link_t[key]
                  link_t['argv'] = argv_t
                  for key in argv_t: del link_t[key]
        else:
            link_t = {}

        link = {
            'route': link_t.get('route', None),
            'argv': link_t.get('argv', {}),
            'container': link_t.get('container', False),
            'container_replace': link_t.get('container_replace', False)
        }

        xbmc.log('XBMCup: Plugin: input param: ' + str(link), xbmc.LOGDEBUG)

        gsetting = {}


        s_content = 'movies'
        set_content = True
        if 'setcontent' in kwarg:
            if kwarg['setcontent'] and isinstance(kwarg['setcontent'], str):
                s_content = kwarg['setcontent']
            elif kwarg['setcontent'] == False:
                set_content = False
        if set_content: xbmcplugin.setContent(int(sys.argv[1]), s_content)

        if 'fanart' in kwarg:
            if kwarg['fanart'] and isinstance(kwarg['fanart'], str):
                fanart = kwarg['fanart']
            else:
                fanart = xbmcaddon.Addon(
                    id=sys.argv[0].replace('plugin://', '').replace('/', '')).getAddonInfo('fanart')
            if fanart:
                gsetting['fanart'] = fanart

        try:
            app = None
            if link['route'] is None and self._index is not None:
                app = self._index(gsetting=gsetting, link=None, argv=link['argv'])
            else:
                handler = [x[1] for x in self._route if x[0] == link['route']]
                if not handler:
                    xbmc.log('XBMCup: Plugin: handler not found: (sys.argv: ' + str(sys.argv) + ')', xbmc.LOGERROR)
                else:
                    if link['container']:
                      if not xbmc.getCondVisibility('Window.IsMedia'):
                          xbmc.executebuiltin('ActivateWindow(videos,%s,return)' % Link(link['route'], link['argv']).url)
                      else:
                        if link['container_replace']:
                            xbmc.executebuiltin('Container.Update(%s,replace)' % Link(link['route'], link['argv']).url)
                        else:
                            xbmc.executebuiltin('Container.Update(%s)' % Link(link['route'], link['argv']).url)
                    else:
                        app = handler[0](gsetting=gsetting, link=link['route'], argv=link['argv'])

            if app:
                app.handle()
                app.render()

        except Exception as e:
            xbmc.log('XBMCup: Plugin: error exec handler: ' + str(e) + '(sys.argv: ' + str(sys.argv) + ')', xbmc.LOGERROR)
            try:
                try:
                    if app:
                        app.hide_busy()
                        app.hide_progress()
                except: pass
                from errors import log
                log(e)
            except: pass
            raise



class Setting(object):
    def __init__(self):
        self._cache = {}
        self._addon = xbmcaddon.Addon(id=sys.argv[0].replace('plugin://', '').replace('/', ''))


    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            self._cache[key] = self._addon.getSetting(id=key)
            return self._cache[key]

    def __setitem__(self, key, value):
        self._cache[key] = value
        self._addon.setSetting(id=key, value=value)

    def dialog(self):
        self._cache = {}
        self._addon.openSettings()


_setting = Setting()

class Lang(object):
    def __init__(self):
        self._cache = {}
        self._addon = xbmcaddon.Addon(id=sys.argv[0].replace('plugin://', '').replace('/', ''))


    def __getitem__(self, token):
        try:
            return self._cache[token]
        except KeyError:
            self._cache[token] = self._addon.getLocalizedString(id=token)
            return self._cache[token]


_lang = Lang()
