# -*- coding: utf-8 -*-

import os
import sys
import re
import time

from sqlite3 import dbapi2 as sqlite

from xbmcup.app import Handler, UrlLink, Link, Lang
from xbmcup.errors import _decode

import xbmc, xbmcgui, xbmcplugin, xbmcvfs
from typing import Tuple, List

#
#
contentname= { 'global': 'Фильмы, Сериалы и Мультипликация',
'movie': 'Фильмы',
'series': 'Сериалы',
'cartoon': 'Мультипликация',
'documentary': 'Документалистика и юмор',
'sport': 'Спорт',
'training': 'Обучающее видео',
'audiobook': 'Аудиокниги',
'avtomoto': 'Всё по авто и мото',
'music': 'Музыка',
'popmusic': 'Популярная музыка',
'jazmusic': 'Джазовая и Блюзовая музыка',
'rockmusic': 'Рок-музыка',
'electromusic': 'Электронная музыка',
}

contentsort = ( 'global',
'movie',
'series',
'cartoon',
'documentary',
'sport',
'training',
'audiobook',
'avtomoto',
'music',
'popmusic',
'jazmusic',
'rockmusic',
'electromusic'
)

class HistoryDB:
    def __init__(self, filename):
        self.filename = filename

        if not xbmcvfs.exists(self.filename):
            self._connect()
            self.cur.execute('pragma auto_vacuum=1')
            self.cur.execute('create table history(addtime integer, content varchar(32), id varchar(500))')
            self.cur.execute('create index time on history(addtime desc)')
            self.db.commit()
            self._close()

    def get(self):
        self._connect()
        self.cur.execute('select content,id from history order by addtime desc')
        res = [{'content': x[0], 'id': x[1]} for x in self.cur.fetchall()]
        self._close()
        return res

    def add(self, content, id):
        self.delete(content, id)
        self._connect()
        self.cur.execute('insert into history(addtime,content,id) values(?,?,?)', (int(time.time()), content, id))
        self.db.commit()
        self._close()

    def delete(self, content, id):
        self._connect()
        self.cur.execute('delete from history where content=? and id=?', (content, id))
        self.db.commit()
        self._close()

    def _connect(self):
        self.db = sqlite.connect(self.filename)
        self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()

class HistorySearchIn(Handler):
    def handle(self):
        search = self.argv.get('search')
        content = self.argv.get('content')
        dialog = xbmcgui.Dialog()
        index = dialog.select(self.lang[40039], [contentname[x] for x in contentsort] )
        if index <  0:
               return True
        else:
              self.argv['content'] = contentsort[index]
        if self.argv['content'] == content:
               return True
        HistoryAdd(self.argv['content'], search)
        self.run(Link('rutracker-search', self.argv))

class History(Handler):
    def handle(self):
        history = HistoryDB(self.path('history.db'))

        if 'content' in self.argv:
            history.delete(self.argv['content'], self.argv['id'])
            xbmcgui.Dialog().ok('RuTracker', self.lang[30022])


        data = history.get()
        if not data:
            xbmcgui.Dialog().ok('RuTracker', self.lang[30008])
            return True
        else:
            total = len(data)

            findall_thumb = os.path.join(self.addon.getAddonInfo('path'),'resources','media','findall.png')
            search_thumb = os.path.join(self.addon.getAddonInfo('path'),'resources','media','search.png')

            for d in data:

                # поиск по имени
                popup: List[Tuple] = [(
                    Link('rutracker-search', {'content': d['content'], 'textsearch': d['id']}, True), self.lang[30114]
                )]

                # искать в разделе
                popup.append( (
                    Link('history-searchin', {'content': d['content'], 'search': d['id']}),
                    self.lang[40038],
                    True,
                    True
                ) )
                # удалить из истории
                popup.append( (Link('history', {'content': d['content'], 'id': d['id']}), self.lang[40035], True, True) )

                # настройки плагина
                popup.append( (self.p_settings, self.lang[40015]) )

                title = d['id']+ u'  [COLOR green]['+_decode(contentname[d['content']])+u'][/COLOR]'

                thumb = findall_thumb if d['content'] == 'global' else search_thumb
                self.item(Link('rutracker-search', {'content': d['content'], 'search': d['id']}), title=title, media='video', popup=popup, popup_replace=True, thumb=thumb, total=total)


def HistoryAdd(content, search):
        HistoryDB(Handler().path('history.db')).add(content, _decode(search))
        return True

