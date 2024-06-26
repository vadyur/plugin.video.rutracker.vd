# -*- coding: utf-8 -*-

import re
import time
import urllib

from urllib.parse import quote_plus

from xbmcup.net import HTTP
from xbmcup.cache import Cache
from xbmcup.html import Clear

import xbmc

from typing import Tuple
from operator import itemgetter

GENRE = {
    'anime': 1750,
    'biography': 22,
    'action': 3,
    'western': 13,
    'military': 19,
    'detective': 17,
    'children': 456,
    'for adults': 20,
    'documentary': 12,
    'drama': 8,
    'game': 27,
    'history': 23,
    'comedy': 6,
    'concert': 1747,
    'short': 15,
    'criminal': 16,
    'romance': 7,
    'music': 21,
    'cartoon': 14,
    'musical': 9,
    'news': 28,
    'adventures': 10,
    'realitytv': 25,
    'family': 11,
    'sports': 24,
    'talk shows': 26,
    'thriller': 4,
    'horror': 1,
    'fiction': 2,
    'filmnoir': 18,
    'fantasy': 5
}

COUNTRIES = (
    (0, u'Все'),
    (2, u'Россия'),
    (1, u'США'),
    (13, u'СССР'),
    (25, u'Австралия'),
    (57, u'Австрия'),
    (136, u'Азербайджан'),
    (120, u'Албания'),
    (20, u'Алжир'),
    (1026, u'Американские Виргинские острова'),
    (139, u'Ангола'),
    (159, u'Андорра'),
    (1044, u'Антарктида'),
    (1030, u'Антигуа и Барбуда'),
    (1009, u'Антильские Острова'),
    (24, u'Аргентина'),
    (89, u'Армения'),
    (175, u'Аруба'),
    (113, u'Афганистан'),
    (124, u'Багамы'),
    (75, u'Бангладеш'),
    (105, u'Барбадос'),
    (164, u'Бахрейн'),
    (69, u'Беларусь'),
    (173, u'Белиз'),
    (41, u'Бельгия'),
    (140, u'Бенин'),
    (109, u'Берег Слоновой кости'),
    (1004, u'Бермуды'),
    (148, u'Бирма'),
    (63, u'Болгария'),
    (118, u'Боливия'),
    (178, u'Босния'),
    (39, u'Босния-Герцеговина'),
    (145, u'Ботсвана'),
    (10, u'Бразилия'),
    (92, u'Буркина-Фасо'),
    (162, u'Бурунди'),
    (114, u'Бутан'),
    (1059, u'Вануату'),
    (11, u'Великобритания'),
    (49, u'Венгрия'),
    (72, u'Венесуэла'),
    (1043, u'Восточная Сахара'),
    (52, u'Вьетнам'),
    (170, u'Вьетнам Северный'),
    (127, u'Габон'),
    (99, u'Гаити'),
    (165, u'Гайана'),
    (1040, u'Гамбия'),
    (144, u'Гана'),
    (135, u'Гватемала'),
    (129, u'Гвинея'),
    (116, u'Гвинея-Бисау'),
    (3, u'Германия'),
    (60, u'Германия (ГДР)'),
    (18, u'Германия (ФРГ)'),
    (1022, u'Гибралтар'),
    (112, u'Гондурас'),
    (28, u'Гонконг'),
    (117, u'Гренландия'),
    (55, u'Греция'),
    (61, u'Грузия'),
    (142, u'Гуаделупа'),
    (1045, u'Гуам'),
    (4, u'Дания'),
    (1037, u'Демократическая Республика Конго'),
    (1028, u'Джибути'),
    (1031, u'Доминика'),
    (128, u'Доминикана'),
    (101, u'Египет'),
    (155, u'Заир'),
    (133, u'Замбия'),
    (104, u'Зимбабве'),
    (42, u'Израиль'),
    (29, u'Индия'),
    (73, u'Индонезия'),
    (154, u'Иордания'),
    (90, u'Ирак'),
    (48, u'Иран'),
    (38, u'Ирландия'),
    (37, u'Исландия'),
    (15, u'Испания'),
    (14, u'Италия'),
    (169, u'Йемен'),
    (146, u'Кабо-Верде'),
    (122, u'Казахстан'),
    (1051, u'Каймановы острова'),
    (84, u'Камбоджа'),
    (95, u'Камерун'),
    (6, u'Канада'),
    (1002, u'Катар'),
    (100, u'Кения'),
    (64, u'Кипр'),
    (1024, u'Кирибати'),
    (31, u'Китай'),
    (56, u'Колумбия'),
    (1058, u'Коморы'),
    (134, u'Конго'),
    (1014, u'Конго (ДРК)'),
    (156, u'Корея'),
    (137, u'Корея Северная'),
    (26, u'Корея Южная'),
    (1013, u'Косово'),
    (131, u'Коста-Рика'),
    (76, u'Куба'),
    (147, u'Кувейт'),
    (86, u'Кыргызстан'),
    (149, u'Лаос'),
    (54, u'Латвия'),
    (1015, u'Лесото'),
    (176, u'Либерия'),
    (97, u'Ливан'),
    (126, u'Ливия'),
    (123, u'Литва'),
    (125, u'Лихтенштейн'),
    (59, u'Люксембург'),
    (115, u'Маврикий'),
    (67, u'Мавритания'),
    (150, u'Мадагаскар'),
    (153, u'Макао'),
    (80, u'Македония'),
    (1025, u'Малави'),
    (83, u'Малайзия'),
    (151, u'Мали'),
    (1050, u'Мальдивы'),
    (111, u'Мальта'),
    (43, u'Марокко'),
    (102, u'Мартиника'),
    (1042, u'Масаи'),
    (17, u'Мексика'),
    (1041, u'Мелкие отдаленные острова США'),
    (81, u'Мозамбик'),
    (58, u'Молдова'),
    (22, u'Монако'),
    (132, u'Монголия'),
    (1034, u'Мьянма'),
    (91, u'Намибия'),
    (106, u'Непал'),
    (157, u'Нигер'),
    (110, u'Нигерия'),
    (12, u'Нидерланды'),
    (138, u'Никарагуа'),
    (35, u'Новая Зеландия'),
    (1006, u'Новая Каледония'),
    (33, u'Норвегия'),
    (119, u'ОАЭ'),
    (1019, u'Оккупированная Палестинская территория'),
    (1003, u'Оман'),
    (1052, u'Остров Мэн'),
    (1047, u'Остров Святой Елены'),
    (1007, u'острова Теркс и Кайкос'),
    (74, u'Пакистан'),
    (1057, u'Палау'),
    (78, u'Палестина'),
    (107, u'Панама'),
    (163, u'Папуа - Новая Гвинея'),
    (143, u'Парагвай'),
    (23, u'Перу'),
    (32, u'Польша'),
    (36, u'Португалия'),
    (82, u'Пуэрто Рико'),
    (1036, u'Реюньон'),
    (1033, u'Российская империя'),
    (2, u'Россия'),
    (103, u'Руанда'),
    (46, u'Румыния'),
    (121, u'Сальвадор'),
    (1039, u'Самоа'),
    (1011, u'Сан-Марино'),
    (158, u'Саудовская Аравия'),
    (1029, u'Свазиленд'),
    (1010, u'Сейшельские острова'),
    (65, u'Сенегал'),
    (1055, u'Сент-Винсент и Гренадины'),
    (1049, u'Сент-Люсия'),
    (177, u'Сербия'),
    (174, u'Сербия и Черногория'),
    (1021, u'Сиам'),
    (45, u'Сингапур'),
    (98, u'Сирия'),
    (94, u'Словакия'),
    (40, u'Словения'),
    (160, u'Сомали'),
    (13, u'СССР'),
    (167, u'Судан'),
    (171, u'Суринам'),
    (1, u'США'),
    (1023, u'Сьерра-Леоне'),
    (70, u'Таджикистан'),
    (44, u'Таиланд'),
    (27, u'Тайвань'),
    (130, u'Танзания'),
    (161, u'Того'),
    (1012, u'Тонго'),
    (88, u'Тринидад и Тобаго'),
    (1053, u'Тувалу'),
    (50, u'Тунис'),
    (152, u'Туркменистан'),
    (68, u'Турция'),
    (172, u'Уганда'),
    (71, u'Узбекистан'),
    (62, u'Украина'),
    (79, u'Уругвай'),
    (1008, u'Фарерские острова'),
    (1038, u'Федеративные Штаты Микронезии'),
    (166, u'Фиджи'),
    (47, u'Филиппины'),
    (7, u'Финляндия'),
    (8, u'Франция'),
    (1032, u'Французская Гвиана'),
    (1046, u'Французская Полинезия'),
    (85, u'Хорватия'),
    (141, u'ЦАР'),
    (77, u'Чад'),
    (1020, u'Черногория'),
    (34, u'Чехия'),
    (16, u'Чехословакия'),
    (51, u'Чили'),
    (21, u'Швейцария'),
    (5, u'Швеция'),
    (108, u'Шри-Ланка'),
    (96, u'Эквадор'),
    (87, u'Эритрея'),
    (53, u'Эстония'),
    (168, u'Эфиопия'),
    (30, u'ЮАР'),
    (19, u'Югославия'),
    (66, u'Югославия (ФР)'),
    (93, u'Ямайка'),
    (9, u'Япония')
)


class KinoPoisk:
    """

    API:
        scraper  - скрапер
        movie    - профайл фильма
        search   - поиск фильма
        best     - поиск лучших фильмов
        person   - поиск персон
        work     - информация о работах персоны

    """

    def __init__(self):
        self.cache = Cache('kinopoisk.db')
        self.html = Clear()

        self.http = HTTP()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Referer': 'http://www.kinopoisk.ru/level/7/'
        }



    # API

    def scraper(self, name, year=None, trailer_quality=None):

        try:
            tag = 'scraper:' + quote_plus(name.encode('windows-1251'))
        except:
            return None
        else:

            if year:
                tag += ':' + str(year)

            id = self.cache.get(tag, False, self._scraper, name, year)
            if not id:
                return None

            return self.movie(id, trailer_quality)


    def movie(self, id, trailer_quality=None):
        id = str(id)

        if trailer_quality is None:
            trailer_quality = 6

        movie = self.cache.get('movie:' + id, False, self._movie, id)
        if not movie:
            return None

        if movie['trailers']:
            # компилируем список с нужным нам качеством
            video = []
            for m in movie['trailers']:
                url = [x for x in m['video'] if x[0] <= trailer_quality]
                if url:
                    m['video'] = url[-1]
                    video.append(m)

            movie['trailers'] = video

            if movie['trailers']:
                # готовим главный трейлер
                r = [x for x in movie['trailers'] if x['trailer']]
                if r:
                    movie['info']['trailer'] = r[0]['video'][1]
                else:
                    # если трейлер не найден, то отдаем что попало...
                    movie['info']['trailer'] = movie['trailers'][0]['video'][1]

        return movie


    def search(self, name, trailer_quality=None):
        return self._search_movie(name)


    def best(self, **kwarg):
        page = kwarg.get('page', 1)
        limit = kwarg.get('limit', 50)

        url = 'http://www.kinopoisk.ru/top/navigator/m_act%5Bis_film%5D/on/m_act%5Bnum_vote%5D/' + str(kwarg.get('votes', 100)) + '/'

        if kwarg.get('dvd'):
            url += 'm_act%5Bis_dvd%5D/on/'

        if kwarg.get('decade'):
            url += 'm_act%5Bdecade%5D/' + str(kwarg['decade']) + '/'

        if kwarg.get('genre'):
            url += 'm_act%5Bgenre%5D/' + str(GENRE[kwarg['genre']]) + '/'

        if kwarg.get('country'):
            url += 'm_act%5Bcountry%5D/' + str(kwarg['country']) + '/'

        if kwarg.get('rate'):
            url += 'm_act%5Brating%5D/' + str(kwarg['rate']) + ':/'

        if kwarg.get('mpaa'):
            url += 'm_act%5Bmpaa%5D/' + str(kwarg['mpaa']) + '/'

        url += 'perpage/' + str(limit) + '/order/ex_rating/'

        if page > 1:
            url += 'page/' + str(page) + '/'

        response = self.http.fetch(url, headers=self.headers)
        if response.error:
            return None

        res = {'pages': (1, 0, 1, 0), 'data': []}

        r = re.compile('<div class="pagesFromTo(.+?)<div class="pagesFromTo', re.U|re.S).search(response.body_decode('windows-1251'))
        if r:

            body = r.group(1)

            # compile pagelist
            p = re.compile('>([0-9]+)&mdash;[0-9]+[^0-9]+?([0-9]+)', re.U).search(body)
            if p:
                page = (int(p.group(1))-1)/limit + 1
                total = int(p.group(2))
                pages = total/limit
                if limit*pages != total:
                    pages += 1
                res['pages'] = (pages, 0 if page == 1 else page-1, page, 0 if page==pages else page+1)
            # end compile

            for id in re.compile('<div id="tr_([0-9]+)"', re.U|re.S).findall(body):
                res['data'].append(int(id))

        return res


    def person(self, name):
        #response = self.http.fetch('https://www.kinopoisk.ru/index.php?level=7&from=forma&result=adv&m_act%5Bfrom%5D=forma&m_act%5Bwhat%5D=actor&m_act%5Bfind%5D=' + urllib.quote_plus(name.encode('windows-1251')), headers=self.headers)
        response = self.http.fetch('http://www.kinopoisk.ru/s/type/people/list/1/find/' + quote_plus(name.encode('windows-1251')) + '/order/relevant/', headers=self.headers)
        if response.error:
            return None

        res = []
        body = re.compile('<div class="navigator">(.+?)<div class="navigator">', re.U|re.S).search(response.body_decode('windows-1251'))
        if body:

            for block in re.compile('<p class="pic">(.+?)<div class="clear">', re.U|re.S).findall(body.group(1)):

                id, name, original, year, poster = None, None, None, None, None

                r = re.compile('<p class="name"><a href="/name/([0-9]+)[^>]+>([^<]+)</a>', re.U|re.S).search(block)
                if r:
                    id = r.group(1)
                    name = r.group(2).strip()

                    if id and name:

                        r = re.compile('<span class="gray">([^<]+)</span>', re.U|re.S).search(block)
                        if r:
                            original = r.group(1).strip()
                            if not original:
                                original = None

                        r = re.compile('<span class="year">([0-9]{4})</span>', re.U|re.S).search(block)
                        if r:
                            year = int(r.group(1))

                        if block.find('no-poster.gif') == -1:
                            poster = 'http://st.kinopoisk.ru/images/actor/' + id + '.jpg'

                        res.append({'id': int(id), 'name': name, 'originalname': original, 'year': year, 'poster': poster})

        return {'pages': (1, 0, 1, 0), 'data': res}


    def work(self, id):
        response = self.http.fetch('http://www.kinopoisk.ru/name/' + str(id) + '/', headers=self.headers)
        if response.error:
            return None

        res = {}

        r = re.compile('id="sort_block">(.+?)<div id="block_right"', re.U|re.S).search(response.body_decode('windows-1251'))
        if r:
            for block in r.group(1).split(u'<tr><td colspan="3" class="specializationBox')[1:]:

                work = None

                for w in ('actor', 'director', 'writer', 'producer', 'producer_ussr', 'composer', 'operator', 'editor', 'design', 'voice', 'voice_director'):
                    if block.find(u'id="' + w + u'"') != -1:
                        work = 'producer' if w == 'producer_ussr' else w
                        break

                if work:

                    movies = []

                    for id, name in re.compile('<span class="name"><a href="/film/([0-9]+)/[^>]+>([^<]+?)</a>', re.U).findall(block):
                        for tag in (u'(мини-сериал)', u'(сериал)'):
                            if name.find(tag) != -1:
                                break
                        else:
                            movies.append(int(id))

                    if movies:
                        res.setdefault(work, []).extend(movies)

        return res


    def review(self, id, query):
        query_s = 'all' if query == 'stat' else query
        data = self.cache.get('review:' + str(id) + ':' + query_s, False, self._review, id, query_s)
        if not data:
            return data
        return data[query]


    def countries(self):
        return COUNTRIES

    def country(self, id, default=None):
        country = [x[1] for x in COUNTRIES if x[0] == id]
        return country[0] if country else default


    # PRIVATE


    def _search_movie(self, name, year=None):
        url = 'http://www.kinopoisk.ru/s/type/film/list/1/find/' + quote_plus(name.encode('windows-1251')) + '/order/relevant'

        if year:
            url += '/m_act%5Byear%5D/' + str(year)
        url += '/m_act%5Btype%5D/film/'

        response = self.http.fetch(url, headers=self.headers)
        if response.error:
            return None

        res = []
        r = re.compile('<div class="navigator">(.+?)<div class="navigator">', re.U|re.S).search(response.body_decode('windows-1251'))
        if r:
            for id in re.compile('<p class="name"><a href="/level/1/film/([0-9]+)', re.U|re.S).findall(r.group(1)):
                res.append(int(id))

        return {'pages': (1, 0, 1, 0), 'data': res}


    def _scraper(self, name, year):
        timeout = True

        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year >= time.gmtime(time.time()).tm_year:
            timeout = 7*24*60*60 #week

        ids = self._search_movie(name, year)

        if ids is None:
            return False, None

        elif not ids['data']:
            # сохраняем пустой результат на 3-е суток
            return 259200, None

        else:
            return timeout, ids['data'][0]


    def _review(self, id, query):
        url = 'http://www.kinopoisk.ru/film/' + str(id) + '/ord/rating/'
        if query in ('good', 'bad', 'neutral'):
            url += 'status/' + query + '/'
        url += 'perpage/200/'

        response = self.http.fetch(url, headers=self.headers)
        if response.error:
            return False, None

        html = response.body_decode('windows-1251')

        res = {
            'stat': {'all': 0, 'good': 0, 'bad': 0, 'neutral': 0},
            query: []
        }

        r = re.compile('<ul class="resp_type">(.+?)</ul>', re.U|re.S).search(html)
        if r:
            ul = r.group(1)

            for q, t in (('pos', 'good'), ('neg', 'bad'), ('neut', 'neutral')):
                r = re.compile('<li class="' + q + '"><a href="[^>]+>[^<]+</a><b>([0-9]+)</b></li>', re.U).search(ul)
                if r:
                    res['stat'][t] = int(r.group(1))

            res['stat']['all'] = res['stat']['good'] + res['stat']['bad'] + res['stat']['neutral']

        r = re.compile('<div class="navigator">(.+?)<div class="navigator">', re.U|re.S).search(html)
        if r:

            for block in r.group(1).split('itemprop="reviews"'):

                review = {
                    'nick': None,
                    'count': None,
                    'title': None,
                    'review': None,
                    'time': None
                }


                r = re.compile('itemprop="reviewBody">(.+?)</div>', re.U|re.S).search(block)
                if r:

                    text = r.group(1)
                    for tag1, tag2 in ((u'<=end=>', u'\n'), (u'<b>', u'[B]'), (u'</b>', u'[/B]'), (u'<i>', u'[I]'), (u'</i>', u'[/I]'), (u'<u>', u'[U]'), (u'</u>', u'[/U]')):
                        text = text.replace(tag1, tag2)

                    r = self.html.text(text)
                    if r:
                        review['review'] = r    # type: ignore


                user = None
                r = re.compile('<p class="profile_name"><s></s><a href="[^>]+>([^<]+)</a></p>').search(block)
                if r:
                    user = self.html.string(r.group(1))
                else:
                    r = re.compile('<p class="profile_name"><s></s>([^<]+)</p>').search(block)
                    if r:
                        user = self.html.string(r.group(1))
                if user:
                    review['nick'] = user   # type: ignore


                r = re.compile('<p class="sub_title"[^>]+>([^<]+)</p>').search(block)
                if r:
                    title = self.html.string(r.group(1))
                    if title:
                        review['title'] = title # type: ignore


                r = re.compile('<span class="date">([^<]+)</span>', re.U|re.S).search(block)
                if r:
                    review['time'] = r.group(1).replace(u' |', u',')    # type: ignore


                r = re.compile(r'<a href="[^>]+>рецензии \(([0-9]+)\)</a>', re.U|re.S).search(block)
                if r:
                    review['count'] = int(r.group(1))   # type: ignore


                if review['nick'] and review['review']:
                    res[query].append(review)

        return 3600, res # one hour


    def _movie(self, id):
        response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/', headers=self.headers)
        if response.error:
            return False, None

        html = response.body_decode('windows-1251')

        res = {
            'id': int(id),
            'thumb': None,
            'fanart': None,
            'trailers': [],
            'info': {}
        }

        # имя, оригинальное имя, девиз, цензура, год, top250
        # runtime - длительность фильма (в отдельную переменную, иначе не видно размер файла)
        for tag, reg, cb in (
            ('title', r'<h1 class="moviename-big" itemprop="name">(.+?)</h1>', self.html.string),
            ('originaltitle', r'itemprop="alternativeHeadline">([^<]*)</span>', self.html.string),
            ('tagline', r'<td style="color\: #555">&laquo;(.+?)&raquo;</td></tr>', self.html.string),
            ('mpaa', r'images/mpaa/([^\.]+).gif', self.html.string),
            ('runtime', r'<td class="time" id="runtime">[^<]+<span style="color\: #999">/</span>([^<]+)</td>', self.html.string),
            ('year', r'<a href="/lists/m_act%5Byear%5D/([0-9]+)/"', int),
            ('top250', r'<a href="/level/20/#([0-9]+)', int)

            ):
            r = re.compile(reg, re.U).search(html)
            if r:
                value = r.group(1).strip()
                if value:
                    res['info'][tag] = cb(value)


        # режисеры, сценаристы, жанры
        for tag, reg in (
            ('director', u'<td itemprop="director">(.+?)</td>'),
            ('writer', u'<td class="type">сценарий</td><td[^>]*>(.+?)</td>'),
            ('genre', u'<span itemprop="genre">(.+?)</span>')
            ):
            r = re.compile(reg, re.U|re.S).search(html)
            if r:
                r2 = []
                for r in re.compile('<a href="[^"]+">([^<]+)</a>', re.U).findall(r.group(1)):
                    r = self.html.string(r)
                    if r and r != '...':
                        r2.append(r)
                if r2:
                    res['info'][tag] = u', '.join(r2)

        # описание фильма
        r = re.compile('<span class="_reachbanner_"><div class="brand_words film-synopsys" itemprop="description">(.+?)</div></span>', re.U).search(html)
        if r:
            plot = self.html.text(r.group(1).replace('<=end=>', '\n'))
            if plot:
                res['info']['plot'] = plot

        # IMDB
        r = re.compile(r'IMDb: ([0-9.]+) \(([0-9\s]+)\)</div>', re.U).search(html)
        if r:
            res['info']['rating'] = float(r.group(1).strip())
            res['info']['votes'] = r.group(2).strip()


        # премьера
        r = re.compile(r'премьера \(мир\)</td>(.+?)</tr>', re.U|re.S).search(html)
        if r:
            r = re.compile(r'data\-ical\-date="([^"]+)"', re.U|re.S).search(r.group(1))
            if r:
                data = r.group(1).split(' ')
                if len(data) == 3:
                    i = 0
                    for mon in (u'января', u'февраля', u'марта', u'апреля', u'мая', u'июня', u'июля', u'августа', u'сентября', u'октября', u'ноября', u'декабря'):
                        i += 1
                        if mon == data[1]:
                            mon = str(i)
                            if len(mon) == 1:
                                mon = '0' + mon
                            day = data[0]
                            if len(day) == 1:
                                day = '0' + day
                            res['info']['premiered'] = '-'.join([data[2], mon, day])
                            break


        # постер
        r = re.compile(r'onclick="openImgPopup\(([^\)]+)\)', re.U|re.S).search(html)
        if r:
            poster = r.group(1).replace("'", '').strip()
            if poster:
                res['thumb'] = 'http://kinopoisk.ru' + poster

        # актеры
        r = re.compile(u'<h4>В главных ролях:</h4>(.+?)</ul>', re.U|re.S).search(html)
        if r:
            actors = []
            for r in re.compile('<li itemprop="actors"><a [^>]+>([^<]+)</a></li>', re.U).findall(r.group(1)):
                r = self.html.string(r)
                if r and r != '...':
                    actors.append(r)
            if actors:
                res['info']['cast'] = actors[:]

        menu = re.compile(r'<ul id="newMenuSub" class="clearfix(.+?)<!\-\- /menu \-\->', re.U|re.S).search(html)
        if menu:
            menu = menu.group(1)

            # фанарт
            if menu.find('/film/' + id + '/wall/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/wall/', headers=self.headers)
                if not response.error:
                    html = response.body_decode('windows-1251')
                    fanart = re.compile(r'<a href="/picture/([0-9]+)/w_size/([0-9]+)/">', re.U).findall(html)
                    if fanart:
                        fanart.sort(key=itemgetter(1))

                        # пробуем взять максимально подходящее
                        fanart_best = [x for x in fanart if int(x[1]) <= 1280]
                        if fanart_best:
                            fanart = fanart_best

                        response = self.http.fetch('http://www.kinopoisk.ru/picture/' + fanart[-1][0] + '/w_size/' + fanart[-1][1] + '/', headers=self.headers)
                        if not response.error:
                            html = response.body_decode('windows-1251')
                            r = re.compile('id="image" src="([^"]+)"', re.U|re.S).search(html)
                            if r:
                                res['fanart'] = r.group(1).strip()
                                if res['fanart'].startswith('//'):
                                    res['fanart'] = 'http:' + res['fanart']


            # если нет фанарта (обоев), то пробуем получить кадры
            if not res['fanart'] and menu.find('/film/' + id + '/stills/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/stills/', headers=self.headers)
                if not response.error:
                    html = response.body_decode('windows-1251')
                    fanart = re.compile('<a href="/picture/([0-9]+)/"><img  src="[^<]+</a>[^<]+<b><i>([0-9]+)&times;([0-9]+)</i>', re.U).findall(html)
                    if fanart:
                        fanart.sort(key=itemgetter(1))

                        # пробуем взять максимально подходящее
                        fanart_best = [x for x in fanart if int(x[1]) <= 1280 and int(x[1]) > int(x[2])]
                        if fanart_best:
                            fanart = fanart_best

                        response = self.http.fetch('http://www.kinopoisk.ru/picture/' + fanart[-1][0] + '/', headers=self.headers)
                        if not response.error:
                            html = response.body_decode('windows-1251')
                            r = re.compile('id="image" src="([^"]+)"', re.U|re.S).search(html)
                            if r:
                                res['fanart'] = r.group(1).strip()
                                if res['fanart'].startswith('//'):
                                    res['fanart'] = 'http:' + res['fanart']


            # студии
            if menu.find('/film/' + id + '/studio/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/studio/', headers=self.headers)
                if not response.error:
                    html = response.body_decode('windows-1251')
                    r = re.compile(u'<b>Производство:</b>(.+?)</table>', re.U|re.S).search(html)
                    if r:
                        studio = []
                        for r in re.compile('<a href="/lists/m_act%5Bstudio%5D/[0-9]+/" class="all">(.+?)</a>', re.U).findall(r.group(1)):
                            r = self.html.string(r)
                            if r:
                                studio.append(r)
                        if studio:
                            res['info']['studio'] = u', '.join(studio)


            # трэйлеры

            trailers1 = [] # русские трейлеры
            trailers2 = [] # другие русские видео
            trailers3 = [] # трейлеры
            trailers4 = [] # другие видео

            if menu.find('/film/' + id + '/video/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/video/', headers=self.headers)
                if not response.error:
                    html = response.body_decode('windows-1251')

                    for row in re.compile(u'<!-- ролик -->(.+?)<!-- /ролик -->', re.U|re.S).findall(html):

                        # отсекаем лишние блоки
                        if row.find(u'>СМОТРЕТЬ</a>') != -1:

                            # русский ролик?
                            if row.find('class="flag flag2"') == -1:
                                is_ru = False
                            else:
                                is_ru = True

                            # получаем имя трейлера
                            r = re.compile('<a href="/film/' + id + '/video/[0-9]+/[^>]+ class="all">(.+?)</a>', re.U).search(row)
                            if r:
                                name = self.html.string(r.group(1))
                                if name:

                                    trailer = {
                                        'name': name,
                                        'time': None,
                                        'trailer': False,
                                        'ru': is_ru,
                                        'video': []
                                    }

                                    # трейлер или тизер?
                                    for token in (u'Трейлер', u'трейлер', u'Тизер', u'тизер'):
                                        if name.find(token) != -1:
                                            trailer['trailer'] = True
                                            break

                                    # получаем время трейлера
                                    r = re.compile(r'clock.gif"[^>]+></td>\s*<td style="color\: #777">[^0-9]*([0-9\:]+)</td>', re.U|re.S).search(row)
                                    if r:
                                        trailer['time'] = r.group(1).strip()

                                    # делим ролики по качеству
                                    for r in re.compile(r'trailer/([1-3])a.gif"(.+?)link=([^"]+)" class="continue">.+?<td style="color\:#777">([^<]+)</td>\s*</tr>', re.U|re.S).findall(row):
                                        quality = int(r[0])
                                        if r[1].find('icon-hd') != -1:
                                            quality += 3

                                        trailer['video'].append((quality, r[2].strip(), r[3]))

                                    if id == '462754':
                                        #raise
                                        pass

                                    if trailer['video']:
                                        if trailer['ru']:
                                            if trailer['trailer']:
                                                trailers1.append(trailer)
                                            else:
                                                trailers2.append(trailer)
                                        else:
                                            if trailer['trailer']:
                                                trailers3.append(trailer)
                                            else:
                                                trailers4.append(trailer)

            # склеиваем трейлеры
            res['trailers'].extend(trailers1)
            res['trailers'].extend(trailers2)
            res['trailers'].extend(trailers3)
            res['trailers'].extend(trailers4)

        timeout = True
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if 'year' not in res['info'] or int(res['info']['year']) >= time.gmtime(time.time()).tm_year:
            timeout = 7*24*60*60 #week

        return timeout, res


