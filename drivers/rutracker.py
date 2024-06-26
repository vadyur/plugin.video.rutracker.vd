# -*- coding: utf-8 -*-

import re
# import cookielib
from typing import Any, Dict, Optional
import urllib
import threading as thr

from xbmcup.app import Setting
from xbmcup.net import HTTP
from xbmcup.cache import Cache
from xbmcup.html import Clear

from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlencode, quote, unquote, quote_plus, unquote_plus, urldefrag

import xbmc
import xbmcgui

file = open

class RuTracker:
    def __init__(self, expire=0, size=0):

        self.setting = Setting()
        self.lostpicq = self.setting['rutracker_lostpic']
        self.domain = self.setting['rutracker_domain']
        if '.lib' in self.domain:
            self.site_url = 'http://' + self.domain.replace(' ','').replace('https://','').replace('http://','').replace('/','')
        else:
            self.site_url = 'https://' + self.domain.replace(' ','').replace('https://','').replace('http://','').replace('/','')

        self.cache_catalog = Cache('rutracker_catalog.db')
        self.cache_profile = Cache('rutracker_profile.db', expire, size)

        self.http = RuTrackerHTTP()

        self.re = {
            'is_int': re.compile(r'^([0-9]+)', re.U),
            'is_float': re.compile(r'^([0-9]{1,10}\.[0-9]+)', re.U),
            'hash': re.compile(r'<span id="tor-hash">([0-9A-F]{40})</span>', re.U), #old
            'hash2': re.compile(r'magnet\:\?xt=urn\:btih\:([0-9A-F]{40})&tr', re.U)
        }

        self.html = Clear()

        self.status = {
            '%': 'check',
            'D': 'repeat',
            '!': 'nodesc',
            '&copy;': 'copyright',
            '&#8719;': 'moder',
            'x': 'close',
            '&sum;': 'absorb',

            '#': 'doubtful',
            '*': 'nocheck',
            '?': 'neededit',
            'T': 'temp',

            '&radic;': 'ok'
        }

    # API

    def favorites_get(self):
        html = self.http.get(self.site_url+'/forum/bookmarks.php')
        if not html:
            return None
        data = None
        form_token = None
        # file('/home/osmc/rutracker.txt', 'wb').write(html)
        r = re.compile(r'<tbody>(.+?)</tbody>',re.U|re.S).search(html)
        if r:
            d = r.group(1)
            # file('/home/osmc/rutracker1.txt', 'wb').write(d)
            r = re.compile(r'<tr class="hl-tr">(.+?)</tr>',re.U|re.S).findall(d)
            if r:
                data = []
                # file('/home/osmc/rutracker2.txt', 'wb').write(unicode(r))
                for i in r:
                    item = self._compile_topic(i, is_favorite=True)
                    if item:
                        data.append(item)
                # file('/home/osmc/rutracker3.txt', 'wb').write(unicode(data))
                r = re.compile(r"form_token:\s*?'(.+?)'\s*?,",re.U|re.S).search(html)
                if r:
                    form_token = str(r.group(1))
        return {'pages': (1, 0, 1, 0), 'data': data, 'form_token': form_token}

    def favorites_add(self, forum_id, topic_id):
        html = self.http.get(self.site_url+'/forum/viewtopic.php?t=' + str(topic_id))
        if not html:
            return None
        r = re.compile(r"form_token:\s*?'(.+?)'\s*?,",re.U|re.S).search(html)
        if r:
            form_token = str(r.group(1))
            html = self.http.post(self.site_url+'/forum/bookmarks.php', {'form_token':form_token, 'action': 'bookmark_add', 'topic_id': str(topic_id), 'forum_id': str(forum_id), 'request_origin': 'from_topic_page'})
            if not html:
                return None
            # file('/home/osmc/rutracker_add.txt', 'wb').write(unicode(html).encode('utf8'))
            if html.find(u">Тема добавлена в <a href='bookmarks.php'><b>Избранное<") != -1:
                return True
        return False

    def favorites_del(self, form_token, topic_id):
        html = self.http.post(self.site_url+'/forum/bookmarks.php', {'form_token':form_token, 'action': 'bookmark_delete', 'topic_ids_csv': str(topic_id), 'request_origin': 'from_bookmarks_page'})
        if not html:
            return None
        # file('/home/osmc/rutracker_del.txt', 'wb').write(unicode(html).encode('utf8'))
        if (html.find('<tbody>') != -1) or (html.find(u'>У вас нет избранных тем</div>') != -1):
            return True
        return False

    def get(self, id=None, page=1) -> Dict[str, Any]:
        """
            Получение списка директорий и раздач

            На вход функции надо подавать следующие параметры:
                id      - [int] id директории
                page    - [int] номер страницы

            Возвращает словарь, состоящий из следующих полей:
                pages  - [list] кортеж [int] для навигации = (кол-во страниц, предыдущая, текущая, следующая)
                data   - [list] данные выборки, состоящая из следующих полей:

                    id            - [int] id (для директорий и топиков ID могут совпадать)
                    name          - [str] имя записи
                    type          - [str] тип записи (torrent - торрент, folder - директория)

                    size          - [int] размер раздачи в байтах
                    seeder        - [int] кол-во сидов
                    leecher       - [int] кол-во личеров
                    download      - [int] кол-во скачиваний торрента
                    comment       - [int] кол-во комментариев
                    status        - [str] символ отметки модератора
                    status_human  - [str] отметка модератора в удобочитаемом виде (описание смотри ниже).

            Описание возвращаемых отметок status_human:
                Скачать торрент нельзя (красный):  moder - премодерация, check - проверяется, repeat - повтор, nodesc - не оформлено, copyright - закрыто правообладателем, close - закрыто, absorb - поглощено.
                Скачать торрент можно   (желтый):  nocheck - не проверено, neededit - недооформлено, doubtful - сомнительно, temp - временная
                Скачать торрент можно  (зеленый):  ok - проверено
        """

        # INDEX
        if id is None:
            html = self.http.get(self.site_url+'/forum/index.php')
            if not html:
                return {}

            res = []

            r = re.compile(r'<div\sid="forums_wrap">(.+)<div\sclass="bottom_info">', re.U|re.S).search(html)
            if r:

                r = re.compile(r'<h4\sclass="forumlink"><a\shref="viewforum\.php\?f=([0-9]+)">(.+?)</a></h4>', re.U|re.S).findall(r.group(1))
                if r:
                    res = [{'id': int(i), 'name': self.html.string(x), 'type': 'folder'} for i, x in r]

            if not res:
                return {}
            return {'pages': (1, 0, 1, 0), 'data': res}

        else:
            page_query = ''
            if page > 1:
                page_query = '&start=' + str(50*(page-1))

            html = self.http.get(self.site_url+'/forum/viewforum.php?f=' + str(id) + '&sort=2' + page_query)
            if not html:
                return {}

            pages = self._compile_pages(html)

            folder = []
            torrent = []

            group_list = re.compile(r'<table class="[^"]*forumline forum">(.+?)</table>', re.U|re.S).findall(html)
            if group_list:
                for group in group_list:

                    # вытаскиваем папки (если есть)
                    r = re.compile(r'<h4\sclass="forumlink"><a\shref="viewforum\.php\?f=([0-9]+)">(.+?)</a></h4>', re.U|re.S).findall(group)
                    if r:
                        folder.extend([{'id': int(i), 'name': self.html.string(x), 'type': 'folder'} for i, x in r])

                    # нарубаем на строчки топиков
                    topic_list = group.split(u'topicSep">')
                    if len(topic_list) > 1:
                        topic_list = topic_list[1:]

                    for html in topic_list:

                        # вытаскиваем id
                        for text in re.compile(r'<tr\sid="tr\-[0-9]+"(.+?)</tr>', re.U|re.S).findall(html):
                            item = self._compile_topic(text)
                            if item:
                                torrent.append(item)

            folder.extend(torrent)

            return {'pages': pages, 'data': folder}

    def search(self, search: str, folder=None, index=None, ignore=None, search_id=None, page=None, days=None, seeders=None, downloads=None):
        """
            Поиск по РуТрекеру

            На вход функции надо подавать следующие параметры:
                search  - [str] поисковая строка запроса (Unicode)
                folder  - [list] список ID директорий, в которых необходимо искать (None - искать везде)

            Возвращает словарь, аналогичный выводу метода GET
        """

        search_out = search
        search = search.replace(u'\u00c7',u' 199 ').replace(u'\u00c9',u' 201 ').replace(u'\u00df',u' 223 ').replace(u'\u00e0',u' 224 ').replace(u'\u00e4',u' 228 ').replace(u'\u00e5',u' 229 ').replace(u'\u00e7',u' 231 ').replace(u'\u00e8',u' 232 ').replace(u'\u00e9',u' 233 ').replace(u'\u00ea',u' 234 ').replace(u'\u00ec',u' 236 ').replace(u'\u00ed',u' 237 ').replace(u'\u00ee',u' 238 ').replace(u'\u00ef',u' 239 ').replace(u'\u00e1',u' 225 ').replace(u'\u015f',u' 351 ').replace(u'\u0160',u' 352 ').replace(u'\u0161',u' 353 ').replace(u'\u00e2',u'a 770 ').replace(u'\u00e3',u' 227 ').replace(u'\u00f1',u' 241 ').replace(u'\u00f2',u' 242 ').replace(u'\u00fc',u' 252 ').replace(u'\u00fd',u' 253 ').replace(u'\u00f6',u' 246 ').replace(u'\u00f3',u' 243 ').replace(u'\u00f4',u' 244 ').replace(u'\u00fa',u' 250 ').replace(u'\u011b',u' 283 ').replace(u'\u0130',u' 304 ').replace(u'\u0131',u' 305 ').replace(u'\u0142',u' 322 ').replace(u'\u0159',u' 345 ').replace(u'\u00e6',u' 230 ').replace(u'\u00f8',u' 248 ').replace(u'\u010d',u' 269 ').replace(u'\u00d6',u' 214 ').replace(u'\u011f',u' 287 ').replace(u'\u015e',u' 350 ').replace(u'\u00dc',u' 220 ').replace(u'\u200e',u'')
        bsearch = search.encode('windows-1251')
        # search = search.encode('utf8') #или это тоже работает

        # проверяем авторизацию
        html = self.http.get(self.site_url+'/forum/index.php')
        if not html:
            return None

        if search_id:
            page_query = ""
            if page and page > 1:
                page_query = "&start=" + str(50 * (page - 1))
            search_query = ""
            if bsearch:
                search_query = "&nm=" + quote_plus(bsearch)
            html = self.http.get(
                self.site_url
                + "/forum/tracker.php?search_id="
                + search_id
                + page_query
                + search_query
            )
        else:
            # готовим запрос для получения дерева разделов
            if folder:
                if not isinstance(folder, list) and not isinstance(folder, tuple):
                    folder = [folder]
            else:
                if index is not None:
                    if not isinstance(index, list) and not isinstance(index, tuple):
                        index = [index]
                if ignore is not None:
                    if not isinstance(ignore, list) and not isinstance(ignore, tuple):
                        ignore = [ignore]
                if not index and not ignore:
                    folder = []
                else:
                    folder = self._load_catalog(index, ignore)
                    if not folder:
                        folder = index
                        # return folder

            # готовим запрос
            if search:
                params = [
                    ("nm", search),
                    ("o", 10),
                    ("s", 2),
                    ("prev_my", 0),
                    ("prev_new", 0),
                    ("prev_oop", 0),
                    ("submit", r"Поиск"),
                ]
            elif days:
                params = [
                    ("o", 1),
                    ("s", 2),
                    ("tm", days),
                    ("prev_my", 0),
                    ("prev_new", 0),
                    ("prev_oop", 0),
                    ("submit", r"Поиск"),
                ]
            elif seeders:
                params = [
                    ("o", 10),
                    ("s", 2),
                    ("prev_my", 0),
                    ("prev_new", 0),
                    ("prev_oop", 0),
                    ("submit", r"Поиск"),
                ]
            elif downloads:
                params = [
                    ("o", 4),
                    ("s", 2),
                    ("prev_my", 0),
                    ("prev_new", 0),
                    ("prev_oop", 0),
                    ("submit", r"Поиск"),
                ]
            else:
                params = [
                    ("o", 1),
                    ("s", 2),
                    ("prev_my", 0),
                    ("prev_new", 0),
                    ("prev_oop", 0),
                    ("submit", r"Поиск"),
                ]

            if folder:
                params.extend([("f[]", x) for x in folder])

            # делаем поиск
            html = self.http.post(self.site_url + "/forum/tracker.php", params)
        #        file('/home/osmc/rutracker_search.txt', 'wb').write(unicode(html).encode('utf8'))
        if not html:
            return None

        pages = self._compile_pages(html)
        search_id = None
        r = re.compile(r'href="tracker.php\?search_id=(.*?)(?:&|">)',re.U|re.S).search(html)
        if r: search_id = r.group(1)

        res = []
        table = re.compile(r'id="tor\-tbl">(.+?)</table>', re.U|re.S).search(html)
        if table:
            for tr in re.compile(r'<tr\sid=".+?"\sclass="tCenter\shl\-tr"[^>]*>(.+?)</tr>', re.U|re.S).findall(table.group(1)):
                item = self._compile_topic(tr, True)
                if item:
                    res.append(item)

        return {'pages': pages, 'data': res, 'search_id': search_id, 'search': search_out}

    def profile(self, id, update=False, screens=True, onlycache=False):
        """
            Получение дополнительной информации о раздачи

            На вход функции надо подавать следующие параметры:
                id      - [int] id топика с раздачей
                update  - [True] обновить кэш принудительно
                screens - [True] обрабатывать ссылки на скриншоты

            Возвращает словарь, состоящий из:
                descript    - [str] описание на RuTracker
                cover       - [str] url обложки
                screenshot  - [list] Список url скриншотов
        """
        return self.cache_profile.get('profile:' + str(id), update, self._profile, id, screens, onlycache)

    def comment(self, id, page=1):
        """
            Получение комментариев раздачи

            На вход функции надо подавать следующие параметры:
                id      - [int] id топика
                page    - [int] номер страницы

            Возвращает словарь, состоящий из следующих полей:
                pages  - [list] кортеж [int] для навигации = (кол-во страниц, предыдущая, текущая, следующая)
                data   - [list] данные выборки - список словарей, состоящих из следующих полей:

                    nick      - [str] ник автора комментария
                    usertime  - [str] стаж юзера
                    count     - [str] кол-во сообщений у юзера
                    location  - [str] откуда юзер
                    time      - [str] время добавления комментария
                    message   - [str] комментарий
        """
        page_query = ''
        if page > 1:
            page_query = '&start=' + str(30*(page-1))

        html = self.http.get(self.site_url+'/forum/viewtopic.php?t=' + str(id) + page_query)
        if not html:
            return None

        res = {
            'pages': self._compile_pages(html),
            'comments': []
        }

        # нарубаем страницу по постам <!\-\-/post_body\-\->
        rows = re.compile('<tbody id="post_[0-9]+" class="row(?:1|2)">(.+?)</tbody>', re.U|re.S).findall(html)
        if rows:
            if page == 1:
                rows.pop(0)
            if rows:

                # функция для очистки комментариев
                def _def_subn1(m):
                    return u'<div class="q-wrap"><div class="q">' + self.html.string(m.group(1)) + u':\n'

                def _def_subn2(m):
                    r = u'[BR][I]' + m.group(1).replace(u'[I]', u'').replace(u'[/I]', u'') + u'[/I][BR]'
                    n = 1
                    while n:
                        r, n = re.compile(r'\[BR\]\[BR\]', re.U|re.S).subn(u'[BR]', r)
                    return r

                for html in rows:

                    comment = {
                        'nick': None,
                        'usertime': None,
                        'count': None,
                        'location': u'',
                        'time': None,
                        'message': None
                    }

                    # вытаскиваем ник
                    r = re.compile('<p class="nick[^>]+>(.+?)</p>', re.U).search(html)
                    if r:
                        comment['nick'] = self.html.string(r.group(1).strip())

                    # смотрим стаж
                    r = re.compile(u'<p class="joined"><em>Стаж:</em>([^<]+)</p>', re.U).search(html)
                    if r:
                        comment['usertime'] = r.group(1).strip()

                    # смотрим кол-во коментов у юзера
                    r = re.compile(u'<p class="posts"><em>Сообщений:</em>([^<]+)</p>', re.U).search(html)
                    if r:
                        comment['count'] = r.group(1).strip()

                    # смотрим город юзера
                    r = re.compile(u'<p class="from"><em>Откуда:</em>([^<]+)</p>', re.U).search(html)
                    if r:
                        comment['location'] = r.group(1).strip()

                    # смотрим страну юзера
                    r = re.compile('<p class="flag"><img [^>]*title="([^"]+)"[^>]*></p>', re.U).search(html)
                    if r:
                        if comment['location']:
                            comment['location'] += u', '
                        comment['location'] += r.group(1).strip()

                    # смотрим время коммента
                    r = re.compile(r'<a class="small" href="\./viewtopic.php\?p=[^>]+>([0-9]{1,2}\-[^\-]+\-[0-9]{2} [0-9]{1,2}\:[0-9]{1,2})</a>', re.U).search(html)
                    if r:
                        comment['time'] = r.group(1).strip()

                    # вытаскиваем тело коммента $
                    r = re.compile('<div class="post_body"[^>]+>(.+?)(?:<div class="signature hide-for-print">|<td class="poster_btn td3 hide-for-print">)', re.U|re.S).search(html)
                    if r:
                        html = r.group(1).strip()
                        if html:

                            # заменяем что можем...
                            for reg, rep in (
                                    (r'<span class="post\-b">([^(?:</span>)]+)</span>', r'[B]\g<1>[/B]'),
                                ):
                                html = re.compile(reg, re.U|re.S).sub(rep, html)

                            # конвертируем цитаты
                            html, n = re.compile(r'<div class="q-wrap">\s*<div class="q" head="([^"]+)">', re.U|re.S).subn(_def_subn1, html)
                            n = 1
                            while n:
                                html, n = re.compile(r'<div class="q-wrap">\s*<div class="q">(.+?)</div>\s*</div>', re.U|re.S).subn(_def_subn2, html)

                            # прогоняем через полную очистку
                            comment['message'] = self.html.text(html)

                    if comment['nick'] and comment['message']:
                        res['comments'].append(comment)

        return res

    def download(self, id):
        """
            Скачивание торрента раздачи

            На вход функции надо подавать следующие параметры:
                id        - [str] топика с раздачей

            Возвращает торрент или None (в случае неудачи)
        """
        return self.http.download(id)

    def hash(self, id, update=False):
        """
            Получение инфо-хеша раздачи

            На вход функции надо подавать следующие параметры:
                id        - [str] топика с раздачей

            Возвращает шеснадцатеричное число хэша (в виде строки) или None (в случае неудачи)
        """
        return self.cache_profile.get('hash:' + str(id), update, self._hash, id)

    def magnet(self, id, cache=False):
        """
            Получение инфо-хеша раздачи

            На вход функции надо подавать следующие параметры:
                id        - [str] топика с раздачей

            Возвращает шеснадцатеричное число хэша (в виде строки) или None (в случае неудачи)
        """
        if cache:
            hash = self.hash(id)
        else:
            result, hash = self._hash(id)
        if hash:
            return 'magnet:?xt=urn:btih:' + hash
        return hash

    # PRIVATE

    def _compile_pages(self, text):
        r = re.compile(r'<p style="float\: left">Страница <b>([0-9]+)</b> из <b>([0-9]+)</b></p>', re.U|re.S).search(text)
        if r:
            current = int(r.group(1))
            total = int(r.group(2))
            next = current + 1
            if next > total:
                next = 0
            return total, current-1, current, next
        return 1, 0, 1, 0

    def _compile_topic(self, text, is_search=False, is_favorite=False):
        r = re.compile(r'<a\s[^>]*href="viewtopic\.php\?t=([0-9]+)"[^>]*>(.+?)</a>', re.U|re.S).search(text)
        if r:
            id = r.group(1)
            name = self.html.string(r.group(2))

            r = re.compile(r'<a[^>]+href="dl\.php\?t=' + id + '"[^>]*>(.+?)</a>', re.U|re.S).search(text)
            if r:
                size = self._compile_size(r.group(1))
                if size and name:

                    item = self._create_torrent(int(id), name)

                    item['size'] = size

                    r = re.compile(r'"tor-icon[^>]+>([^<]+)<', re.U|re.S).search(text)
                    if r:
                        stat = r.group(1)
                        try:
                            status = self.status[stat]
                        except KeyError:
                            pass
                        else:
                            item['status'] = self.html.char(stat)
                            item['status_human'] = status

                    if is_search:
                        r = re.compile(r'<a\s[^>]*href="tracker\.php\?f=([0-9]+)"[^>]*>(.+?)</a>', re.U|re.S).search(text)
                        if r:
                            f_id = r.group(1)
                            item['f_id'] = int(f_id)
                            f_name = self.html.string(r.group(2))
                            item['f_name'] = f_name
                        item['comment'] = -1
                        query = (('download', r'<td\sclass="row4\ssmall number-format">([0-9]+)</td>'), ('seeder', '<b class="seedmed">([0-9]+)</b>[^<]+</td>'), ('leecher', r'<td\sclass="row4 leechmed bold"[^>]+>([0-9]+)</td>'))
                    elif is_favorite:
                        r = re.compile(r'<a\s[^>]*href="viewforum\.php\?f=([0-9]+)"[^>]*>(.+?)</a>', re.U|re.S).search(text)
                        if r:
                            f_id = r.group(1)
                            item['f_id'] = int(f_id)
                            f_name = self.html.string(r.group(2))
                            item['f_name'] = f_name
                        item['download'] = -1
                        query = (('comment', r'<td class="t-replies-cell">\s*?([0-9]+)\s*?</td>'), ('seeder', u'title="Сиды"><b>([0-9]+)</b></span>'), ('leecher', u'title="Личи"><b>([0-9]+)</b></span>'))
                    else:
                        query = (('comment', r'<span title="Ответов">([0-9]+)</span>'), ('download', u'title="Торрент скачан">[^<]*<b>([0-9,]+)</b>[^<]*</p>'), ('seeder', 'title="Seeders"><b>([0-9]+)</b></span>'), ('leecher', 'title="Leechers"><b>([0-9]+)</b></span>'))

                    for tag, reg in query:
                        r = re.compile(reg, re.U|re.S).search(text)
                        if r:
                            item[tag] = int(r.group(1).replace(',',''))

                    return item

        return None

    def _create_torrent(self, id, name):
        return {
            'id': id,
            'name': name,
            'type': 'torrent',
            'size': 0,
            'seeder': 0,
            'leecher': 0,
            'download': 0,
            'comment': 0,
            'status': None,
            'status_human': None
        }

    def _compile_size(self, text):
        text = self.html.string(text.replace(u'&#8595;', u''))
        if text:
            text = text.lower()
            prefix = 1
            for p, v in ((u'kb', 1024), (u'mb', 1024*1024), (u'gb', 1024*1024*1024), (u'tb', 1024*1024*1024*1024)):
                if text.find(p) != -1:
                    prefix = v
                    text = text.replace(p, u'').strip()
                    break

            num = self.re['is_float'].search(text)
            if num:
                return int(float(prefix)*float(num.group(1)))

            num = self.re['is_int'].search(text)
            if num:
                return prefix*int(num.group(1))

        return None

    def _hash(self, id):
        html = self.http.get(self.site_url+'/forum/viewtopic.php?t=' + str(id))
        # file('home/osmc/rutracker_magnet.txt','wb').write(unicode(html).encode('utf8'))
        if not html:
            return False, html
        r = self.re['hash'].search(html)
        if not r: r = self.re['hash2'].search(html)
        if not r:
            return False, None
        return True, str(r.group(1))

    def _profile(self, id, screens=True, onlycache=False):
        # html = self.http.guest(self.site_url+'/forum/viewtopic.php?t=' + str(id))
        if not onlycache:
            html = self.http.get(self.site_url+'/forum/viewtopic.php?t=' + str(id))
            if not html:
                return False, html
        # file('home/osmc/rutracker_profile.txt', 'wb').write(unicode(html).encode('utf8'))

        res = {
            'descript': None,
            'cover': None,
            'screenshot': None
        }
        if onlycache: return False, res
        # r = re.compile('<div class="post_body"[^>]+>(.+?)<legend>Download</legend>', re.U|re.S).search(html)
        r = re.compile('<div class="post_body"[^>]+>(.+?)<table class="attach bordered med">', re.U|re.S).search(html)
        if r:

            html = r.group(1)

            # def _r1():
            # ищем коверы (перебирая все возможные варианты хостингов картинок)
            for api in (self.pic_hosting_fastpic, self.pic_hosting_imageban, self.pic_hosting_lostpic, self.pic_hosting_radikal, self.pic_hosting_vfl, self.pic_hosting_funkyimg, self.pic_hosting_yapx, self.pic_hosting__unknow):
                cover = api('cover', html)
                if cover:
                    res['cover'] = cover    # type: ignore
                    break

            # t1 = thr.Thread(target=_r1)

            # вытаскиваем блок со скриншотами </div>
            if screens:
                r = re.compile(r'<span>(?:\wкриншоты|\wадры из фильма|\wкриншоты мультфильма)[&#0-9;]*</span></div>(.+?)</div>', re.U|re.S).search(html)
                if r:
                    c = re.compile(r'http\://|https\://', re.U|re.S).search(r.group(1))
                    if c is None:
                        r = re.compile(r'<span>(?:\wкриншоты|\wадры из фильма|\wкриншоты мультфильма)[&#0-9;]*</span></div>(.+?)$', re.U|re.S).search(html)

                if r:
                    body = r.group(1)

                    # ищем скрины (перебирая все возможные варианты хостингов картинок)
                    for api in (self.pic_hosting_fastpic, self.pic_hosting_imageban, self.pic_hosting_lostpic, self.pic_hosting_radikal, self.pic_hosting_vfl, self.pic_hosting_funkyimg, self.pic_hosting_yapx, self.pic_hosting_postpic4, self.pic_hosting_directupload, self.pic_hosting_youpicture, self.pic_hosting_imgbox, self.pic_hosting_imagebam, self.pic_hosting_ufanet, self.pic_hosting__unknow):
                        screenshot = api('screenshot', body)
                        if screenshot:
                            res['screenshot'] = screenshot  # type: ignore
                            break
                else: # ищем хоть какие-нибудь картинки
                    r = re.compile(r'<a[^>]*href="(?:http|https)\://.+?"[^>]*>[.]*?<var[^>]+title="', re.U|re.S).search(html)
                    if r:
                        body = html
                        # ищем скрины (перебирая все возможные варианты хостингов картинок)
                        for api in (self.pic_hosting_fastpic, self.pic_hosting_imageban, self.pic_hosting_lostpic, self.pic_hosting_radikal, self.pic_hosting_vfl, self.pic_hosting_funkyimg, self.pic_hosting_yapx, self.pic_hosting_postpic4, self.pic_hosting_directupload, self.pic_hosting_youpicture, self.pic_hosting_imgbox, self.pic_hosting__unknow):
                            screenshot = api('screenshot', body)
                            if screenshot:
                                res['screenshot'] = screenshot  # type: ignore
                                break

            # t1.start()
            # пытаемся получить текст описания
            # режем и заменяем все что можем...
            for reg, rep in (

                    (r'<div class="sp\-wrap">.+?<div class="sp-body">.+?</div>', u''), # удаляем все спойлеры
                    (r'<var[^>]+>[^<]+</var>', u''), # удаляем все изображения
                    (r'<span class="post\-hr">\-</span>', u'\n'), # удаляем HR
#                    (u'<span class="post\-b">([^<]+)</span>\:', u'\n[COLOR FF0DA09E]\g<1>[/COLOR]:'), # заменяем болды
                    (r'<span class="post\-b">([^<]+)\:</span>', r'\n[COLOR FF0DA09E]\g<1>:[/COLOR]'), # заменяем болды
                    (r'<span class="post\-b">([^<]+)</span>', r'[COLOR FF0DA09E]\g<1>[/COLOR]') # заменяем болды

                ):
                html = re.compile(reg, re.U|re.S).sub(rep, html)

            # прогоняем через полную очистку
            html = self.html.text(html)
            html = re.compile(r'(\[COLOR FF0DA09E\][^\[]+\[/COLOR\]\:)', re.U|re.S).sub(r'\n\g<1>', html)
            html = re.compile(r'[\n]{2,}', re.U|re.S).sub(u'\n', html)
            if html:
                res['descript'] = html  # type: ignore

            # t1.join()

        return True, res

    # CATALOG
    def _load_catalog(self, index, ignore):
        catalog = self.cache_catalog.get('catalog', False, self._load_catalog_http)
        if not catalog:
            return []

        res = []
        for key, folders in catalog.items():
            if index is None or key in index:
                res.extend([x for x in folders if x not in ignore])

        return res

    def _load_catalog_http(self):
        html = self.http.get(self.site_url+'/forum/tracker.php')
        if not html:
            return False, html

        r = re.compile('<select id="fs-main"(.+?)</select>', re.U|re.S).search(html)
        if not r:
            return False, None

        res = {}
        root = None
        for cat, is_root_forum in re.compile(r'<option id="fs\-([0-9]+)"([^>]+)>', re.U).findall(r.group(1)):
            cat = int(cat)
            if is_root_forum.find('root_forum') != -1:
                root = cat
                res[root] = [cat]
            elif root:
                res[root].append(cat)

        return (86400 if res else False), res # day

    # SCREENSHOT

    def pic_hosting_fastpic(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-z]+\.fastpic\.(?:org|ru)/big/[0-9a-f/_]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                # for r in re.compile('<a[^>]*href="(?:http|https)\://fastpic\.ru/(?:view|fullview)/[0-9a-z/_]+\.([a-z]{3,4})\.html(?:"|\?noht=1")[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.fastpic\.ru/thumb/[0-9a-f/_]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                #    res.append('.'.join([r[1].replace('thumb', 'big'), r[0]])+'?r=1') # '?noht=1')
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://fastpic\.(?:org|ru)/(?:view|fullview)/[0-9a-z/_]+\.[a-z]{3,4}\.html[\?nohtr=1]*)"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.fastpic\.(?:org|ru)/thumb/[0-9a-f/_]+\.[a-z]{3,4}[\?r=1]*)"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[1])
            # for r in re.compile('<a[^>]*href="((?:http|https)\://[a-z0-9]+\.fastpic\.ru/big/[0-9a-f/_]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.fastpic\.ru/big/[0-9a-f/_]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]+'?noht=1') # учтено ниже
            # for r in re.compile('<a[^>]*href="((?:http|https)\://[a-z0-9]+\.fastpic\.ru/big/[0-9a-f/_]+\.[a-z]{3,4}\?noht=1)"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.fastpic\.ru/thumb/[0-9a-f/_]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]) # учтено ниже
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://[a-z0-9]+\.fastpic\.(?:org|ru)/big/[0-9a-f/_]+\.[a-z]{3,4})(?:\?noht=1"|")[^>]*>[.]*?<var[^>]+title="([^"]+?)"', re.U|re.S).findall(html):
                    res.append(r[1]) #r+'?noht=1')
            def _r3():
                for r in re.compile(r'<var\s+class="postImg"\s+title="(http[s]{0,1}\://[a-z0-9]+\.fastpic\.(?:org|ru)/big/[0-9a-f/_]+\.[a-z]{3,4})">', re.U|re.S).findall(html):
                    res.append(r) #r+'?noht=1')
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t3 = thr.Thread(target=_r3)
            t1.start()
            t2.start()
            t3.start()
            t1.join()
            t2.join()
            t3.join()
            return res if res else None

    def pic_hosting_imageban(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-z]+\.imageban\.ru/out/[0-9a-z/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://(?:imageban|www\.imageban)\.ru/show/([0-9/]+)/[0-9a-z]+/([a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.imageban\.ru/thumbs/)[0-9\.]+(/[0-9a-z]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[2].replace('thumbs', 'out')+r[0]+'.'.join([r[3], r[1]]))
            # for r in re.compile('<a[^>]*href="((?:http|https)\://[a-z0-9]+\.imageban\.ru/out/[0-9/]+/[0-9a-f]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.imageban\.ru/thumbs/)[0-9\.]+(/[0-9a-z]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]) # учтено ниже
            # for r in re.compile('<a[^>]*href="((?:http|https)\://[a-z0-9]+\.imageban\.ru/out/[0-9/]+/[0-9a-f]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.imageban\.ru/out/)[0-9/]+([0-9a-f]+)\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]) # учтено ниже
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://[a-z0-9]+\.imageban\.ru/out/[0-9/]+/[0-9a-f/\.]+[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="', re.U|re.S).findall(html):
                    res.append(r)
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    # radikal.ru не отдает сразу полноразмерные картинки по прямой ссылке...
    def pic_hosting_radikal(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-z]+\.radikal\.ru/[0-9a-z/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            # for r in re.compile('<a[^>]*href="((?:http|https)\://)radikal\.ru/F/([0-9a-z]+\.radikal\.ru/[0-9a-z/]+\.[a-z]{3,4})\.html"[^>]*>[.]*?<var[^>]+title="(?:http|https)\://[0-9a-z]+\.radikal\.ru/[0-9a-f/]+\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]+r[1])
            def _r1():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://[0-9a-zA-Z@\./_-]+)"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.radikal\.ru/[0-9a-z/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[1])
            def _r2():
                for r in re.compile(r'<var\s+class="postImg"\s+title="((?:http|https)\://[a-z0-9]+\.radikal\.ru/[0-9a-i/]+\.[a-z]{3,4})">', re.U|re.S).findall(html):
                    res.append(r)
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    def pic_hosting_lostpic(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-z]+\.lostpic\.net/[0-9a-f/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            qt = self.lostpicq
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://(?:lostpic\.net|[0-9a-z]+\.lostpic\.net)/image/[0-9A-Za-z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://(?:[0-9a-z]+\.lostpic\.net|lostpic\.net)/[0-9a-z/]+)\.th(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    if qt == '1':
                        res.append(r[0]+r[1].replace('.','.md.'))
                    elif qt == '2':
                        res.append(r[0]+r[1].replace('.','.th.'))
                    else:
                        res.append(r[0]+r[1])
            # for r in re.compile('<a[^>]*href="(?:http|https)\://[a-z0-9]+\.lostpic\.net/[0-9a-f/]+\.[a-z]{3,4}"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.lostpic\.net/[0-9a-f/]+)\.th(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]+r[1]) # учтено ниже
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://[a-z0-9]+\.lostpic\.net/[0-9a-f/]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="', re.U|re.S).findall(html):
                    res.append(r)
            def _r3():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://lostpic\.net/\?photo=[0-9]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://lostpic\.net/thumbs_images/[0-9a-f/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r.replace('thumbs_','orig_'))
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t3 = thr.Thread(target=_r3)
            t1.start()
            t2.start()
            t3.start()
            t1.join()
            t2.join()
            t3.join()
            return res if res else None

    def pic_hosting_vfl(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://images\.vfl\.ru/[a-z]+/[0-9a-f/]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://vfl\.ru/fotos/[0-9a-z/_]+\.html"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://images\.vfl\.ru/[a-z]+/[0-9a-f/]+)_[sm](\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[0]+r[1])
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://images\.vfl\.ru/ii/[0-9a-f/]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://images\.vfl\.ru/ii/[0-9a-f/_sm]+)(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[0])
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    def pic_hosting_funkyimg(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://funkyimg\.com/i/[0-9a-zA-Z]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://funkyimg\.com/view/[0-9a-zA-Z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://funkyimg\.com/)p(/[0-9a-zA-Z]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[0]+'i'+r[1])
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://funkyimg\.com/i/[0-9a-zA-Z]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://funkyimg\.com/)i(/[0-9a-zA-Z]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r[0])
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    def pic_hosting_yapx(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://i\.yapx\.ru/[0-9a-zA-Z]{5}\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            for r in re.compile(r'<a[^>]*href="(?:http|https)\://yapx\.ru/v/[0-9a-zA-Z]{5}"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://i\.yapx\.ru/[0-9a-zA-Z]{5})s(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                res.append(r[0]+r[1])
            return res if res else None

    def pic_hosting_postpic4(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            for r in re.compile(r'<a[^>]*href="(?:http|https)\://postpic4\.me/[0-9A-Za-z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://postpic4\.me/thumbnails/[0-9a-f/prviw_]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                res.append(r.replace('thumbnails','images').replace('preview_',''))
            return res if res else None

    def pic_hosting_directupload(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            for r in re.compile(r'<a[^>]*href="((?:http|https)\://[0-9a-z]+\.directupload\.net/[0-9A-Za-z/]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="(?:http|https)\://[0-9a-z]+\.directupload\.net/[0-9a-zA-Z/]+\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                res.append(r)
            return res if res else None

    def pic_hosting_youpicture(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            for r in re.compile(r'<a[^>]*href="(?:http|https)\://youpicture\.org/[0-9A-Za-z/\-\?_=]+\.[a-z]{3,4}"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://youpicture\.org/images/[0-9a-zA-Z/]+)[\.th]*?(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                res.append(r[0]+r[1])
            return res if res else None

    def pic_hosting_imgbox(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://imgbox\.com/[0-9A-Za-z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://thumbs[0-9]*?\.imgbox\.com/[0-9a-zA-Z/_]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r.replace('thumbs','images').replace('_t','_o'))
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://images[0-9]*?\.imgbox\.com/[0-9a-zA-Z/]+_o\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="(?:http|https)\://images[0-9]*?\.imgbox\.com/[0-9a-zA-Z/_]+\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                    res.append(r)
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    def pic_hosting_imagebam(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            def _r1():
                for r in re.compile(r'<a[^>]*href="(?:http|https)\://www\.imagebam\.com/(?:image|view)/[0-9A-Za-z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://thumb[a-z0-9]*?\.imagebam\.com/[0-9a-zA-Z/_]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
                    res.append(r)
            def _r2():
                for r in re.compile(r'<a[^>]*href="((?:http|https)\://images[0-9]*?\.imagebam\.com/[0-9a-zA-Z/]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="(?:http|https)\://thumbs[0-9]*?\.imagebam\.com/[0-9a-zA-Z/_]+\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                    res.append(r)
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return res if res else None

    def pic_hosting_ufanet(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            for r in re.compile(r'<a[^>]*href="((?:http|https)\://linkme\.ufanet\.ru/[0-9A-Za-z/\-\?_=]+\.[a-z]{3,4})"[^>]*>[.]*?<var[^>]+title="(?:http|https)\://linkme\.ufanet\.ru/box/[0-9a-zA-Z/]+\.[a-z]{3,4}"[^>]*>', re.U|re.S).findall(html):
                res.append(r)
            return res if res else None

    def pic_hosting__unknow(self, img, html):
        if img == 'cover':
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-right"[^>]+title="((?:http|https)\://[0-9a-zA-Z%@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            r = re.compile(r'<var[^>]+class="postImg postImgAligned img\-left"[^>]+title="((?:http|https)\://[0-9a-zA-Z%@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            r = re.compile(r'<var[^>]+class="postImg"[^>]+title="((?:http|https)\://[0-9a-zA-Z%@\./_-]+\.[a-z]{3,4})"[^>]*>', re.U|re.S).search(html)
            if r:
                return r.group(1)
            return None
        else:
            res = []
            # for r in re.compile('<a[^>]*href="(?:http|https)\://lostpic\.net/image/[0-9A-Za-z]+"[^>]*>[.]*?<var[^>]+title="((?:http|https)\://[0-9a-z]+\.lostpic\.net/[0-9a-f/]+)\.th(\.[a-z]{3,4})"[^>]*>', re.U|re.S).findall(html):
            #    res.append(r[0]+r[1])
            return res if res else None


class RuTrackerHTTP:
    captcha_code: Optional[str]

    def __init__(self):
        self.setting = Setting()
        self.domain = self.setting['rutracker_domain']
        if '.lib' in self.domain:
            self.site_url = 'http://' + self.domain.replace(' ','').replace('https://','').replace('http://','').replace('/','')
        else:
            self.site_url = 'https://' + self.domain.replace(' ','').replace('https://','').replace('http://','').replace('/','')
        self.re_auth = re.compile(r'profile\.php\?mode=sendpassword"')
        # self.re_captcha = re.compile(r'<img src="(\/\/[^\/]+/captcha/[^"]+)"')
        # self.re_captcha_sid = re.compile(r'<input type="hidden" name="cap_sid" value="([^"]+)">')
        # self.re_captcha_code = re.compile(r'<input type="text" name="(cap_code_[^"]+)"')
        self.re_captcha = re.compile(r'<img src="(.+?/captcha/[^"]+)"')
        self.re_captcha_sid = re.compile(r'<input type="hidden" name="cap_sid" value="([^"]+)">')
        self.re_captcha_code = re.compile(r'<input class="reg-input" type="text" name="(cap_code_[^"]+)"')
        self.captcha_sid = None
        self.captcha_code = None
        self.captcha_code_value = None
        self.http = HTTP()
        self.unblock = int(self.setting['rutracker_unblock'])
        if self.unblock ==1:
            self.proxy_protocol = 'https'
            proxy_serv = self.setting['proxy_serv'].split(':')
            self.proxy_host = proxy_serv[0]
            self.proxy_port = int(proxy_serv[1])
        if self.unblock ==2:
            self.proxy_protocol = 'https'
            self.proxy_host = self.setting['rutracker_proxy_host']
            self.proxy_port = int(self.setting['rutracker_proxy_port'])
        if self.unblock ==3:
            self.proxy_protocol = 'socks5'
            self.proxy_host = self.setting['rutracker_socks5_host']
            self.proxy_port = int(self.setting['rutracker_socks5_port'])

        self.headers = {
#            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Referer': self.site_url+'/forum/index.php'
        }
        if '.lib' in self.domain or self.domain in ('rutracker.net', 'rutracker.nl'): self.headers['Accept-Encoding'] = 'gzip' # фикс бага сервера

    def guest(self, url):
        if self.unblock ==0: response = self.http.fetch(url, headers=self.headers)
        if self.unblock >=1: response = self.http.fetch(url, headers=self.headers, proxy_protocol=self.proxy_protocol, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
        if response.error:
            return None
        else:
            body = response.body_decode('windows-1251', 'ignore')
            if body.find(u'>По техническим причинам форум временно недоступен</div>') != -1:
                return 0
            return body

    def get(self, url):
        return self._fetch('GET', url)

    def post(self, url, params):
        return self._fetch('POST', url, params)

    def download(self, id):
        id = str(id)

        # проверяем авторизацию
        html = self.get(self.site_url+'/forum/viewtopic.php?t=' + id)
        if not html:
            return None

        # хакаем куки
        from http.cookiejar import MozillaCookieJar, Cookie # fast
        cookies = MozillaCookieJar()
        cookies.load(self.http.request.cookies)
        cookies.set_cookie(
            Cookie(
                version=0,
                name="bb_dl",
                value=id,
                port=None,
                port_specified=False,
                domain="."
                + self.site_url.replace("https://", "").replace("http://", ""),
                domain_specified=False,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={"HttpOnly": ''},
                rfc2109=False,
            )
        )
        cookies.save(self.http.request.cookies, ignore_discard=True, ignore_expires=True)

        # тянем торрент
        if self.unblock ==0: response = self.http.fetch(self.site_url+'/forum/dl.php?t=' + id, cookies='rutracker.moz', headers=self.headers, method='POST')
        if self.unblock >=1: response = self.http.fetch(self.site_url+'/forum/dl.php?t=' + id, cookies='rutracker.moz', headers=self.headers, method='POST', proxy_protocol=self.proxy_protocol, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
        if response.error:
            return None
        else:
            return response.body

    def _fetch(self, method, url, params=None):
        while True:
            if self.unblock ==0: response = self.http.fetch(url, cookies='rutracker.moz', headers=self.headers, method=method, params=params)
            if self.unblock >=1: response = self.http.fetch(url, cookies='rutracker.moz', headers=self.headers, method=method, params=params, proxy_protocol=self.proxy_protocol, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
            # file('home/osmc/rutracker_fetch.txt', 'wb').write(response.body_decode('cp1251').encode('utf8'))
            if response.error:
                return None
            else:
                body = response.body_decode('windows-1251', 'replace')
                if body.find(u'>По техническим причинам форум временно недоступен</div>') != -1:
                    return 0
                if not self.re_auth.search(body):
                    return body
                xbmc.log('RUTRACKER: Request auth', xbmc.LOGDEBUG)
                auth = self._auth()
                if not auth:
                    return auth

    def _auth(self):
        self.captcha_sid, self.captcha_code, self.captcha_code_value = None, None, None
        while True:
            login = self.setting['rutracker_login']
            password = self.setting['rutracker_password']
            if not login or not password:
                self.setting.dialog()
                login = self.setting['rutracker_login']
                password = self.setting['rutracker_password']
                if not login or not password:
                    return None

            params = {'login_username': login, 'login_password': password, 'login': r'вход'}
            if self.captcha_sid:
                params['login'] = r'Вход'
                params['cap_sid'] = self.captcha_sid
                if self.captcha_code:
                    params[self.captcha_code] = self.captcha_code_value

            if self.unblock ==0: response = self.http.fetch(self.site_url+'/forum/login.php', cookies='rutracker.moz', headers=self.headers, method='POST', params=params)
            if self.unblock >=1: response = self.http.fetch(self.site_url+'/forum/login.php', cookies='rutracker.moz', headers=self.headers, method='POST', params=params, proxy_protocol=self.proxy_protocol, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
            self.captcha_sid, self.captcha_code, self.captcha_code_value = None, None, None
            if response.error:
                return None

            body = response.body_decode('windows-1251')

            if body.find(u'>По техническим причинам форум временно недоступен</div>') != -1:
                return 0

            if not self.re_auth.search(body):
                return True

            # проверяем капчу
            r = self.re_captcha.search(body)
            if r:
                r_sid = self.re_captcha_sid.search(body)
                if not r_sid:
                    return None
                self.captcha_sid = r_sid.group(1)
                r_code = self.re_captcha_code.search(body)
                if not r_code:
                    return None
                self.captcha_code = r_code.group(1)
                self.captcha_code_value = self._captcha(r.group(1))
                if not self.captcha_code_value:
                    return None

            # get login
            k = xbmc.Keyboard('', 'Введите логин ( Enter login )')
            k.doModal()
            if k.isConfirmed():
                login = k.getText()
            else:
                return None

            # get password
            k = xbmc.Keyboard('', 'Введите пароль ( Enter password )', True)
            k.doModal()
            if k.isConfirmed():
                password = k.getText()
            else:
                return None

            if not login or not password:
                return None

            self.setting['rutracker_login'] = login
            self.setting['rutracker_password'] = password

    def _captcha(self, captcha):
        if self.unblock ==0: response = self.http.fetch(captcha, headers=self.headers, method='GET')
        if self.unblock >=1: response = self.http.fetch(captcha, headers=self.headers, method='GET', proxy_protocol=self.proxy_protocol, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
        if response.error:
            return

        import tempfile
        filename = tempfile.gettempdir() + '/captcha'
        if response.body:
            file(filename, 'wb').write(response.body)

        win = xbmcgui.Window(xbmcgui.getCurrentWindowId())

        # width = 120px, height = 72px
        x: int = int(win.getWidth() / 2 - 120 / 2)
        image = xbmcgui.ControlImage(x, 20, 120, 72, filename)
        win.addControl(image)
        k = xbmc.Keyboard('', 'Введите код капчи ( Enter captcha code )')
        k.doModal()
        code = k.getText() if k.isConfirmed() else None
        win.removeControl(image)
        return code if code else None
