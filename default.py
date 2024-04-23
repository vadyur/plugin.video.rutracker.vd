#!/usr/bin/python
# -*- coding: utf-8 -*-
# import cProfile
# pr = cProfile.Profile()
# pr.enable()

import os
import sys
import re
import time
import threading as thr
import gc

from urllib.parse import parse_qs, quote_plus, urlencode

from typing import List, Optional, Dict, Any, Tuple, Union

from sqlite3 import dbapi2 as sqlite

from xbmcup.app import Plugin, Handler, Link, Lang, Setting as AppSetting
from xbmcup.cache import Cache
from xbmcup.errors import log as _log

import xbmc, xbmcgui, xbmcplugin, xbmcvfs

from drivers.rutracker import RuTracker
from drivers.kinopoisk import KinoPoisk
from drivers.tvdb import TvDb
from drivers.tmdb import TmDb

from history import History, HistoryAdd, HistorySearchIn
from torrserveradd import AddTorrserverBase

file = open

_setting_ = AppSetting()


def mkStr(s1: str, s2: str, s3="") -> str:
    if s2 and s3:
        return s1 + "\n" + s2 + "\n" + s3
    if s2:
        return s1 + "\n" + s2
    else:
        return s1


def cmp(x, y):
    if x < y:
        return -1
    elif x > y:
        return 1
    else:
        return 0


SCRAPERS_MOVIE = (
    "tmdb_movie",
    "rutrackermovies",
    "rutrackermovies_tmdb_rating",
    "rutrackermovies_tmdb_rating_fanart",
    "tmdb_movie_tracker_plot",
)
SCRAPERS_SERIES = (
    "tvdb",
    "rutrackerseries",
    "rutrackerseries_tmdb_rating",
    "rutrackerseries_tmdb_rating_fanart",
    "tmdb_series_tracker_plot",
    "tmdb_series",
)
SCRAPERS_CARTOON = (
    "tmdb_cartoon",
    "rutrackercartoon",
    "rutrackercartoon_tmdb_rating",
    "rutrackercartoon_tmdb_rating_fanart",
    "tmdb_cartoon_tracker_plot",
)


CONTENT = {
    "movie": {
        "index": (7, 22, 124, 93, 2198, 352, 511),
        "ignore": (
            1640,
            1692,
            1454,
            2374,
            2373,
            185,
            254,
            771,
            44,
            906,
            69,
            267,
            65,
            772,
            789,
            531,
            125,
            149,
            186,
            96,
            94,
            653,
            2344,
            514,
            2097,
            540,
            513,
        ),  # 3D - спорт, музыка (TODO - надо их куда-нибудь пристроить...)
        "media": "video",
        "scraper": SCRAPERS_MOVIE[
            int(_setting_["rutracker_movies"])
        ],  # 'rutrackermovies', # 'kinopoisk' отключен. Может кто возьмется его починить...:)
        "rating": "%1.1f",
        "stream": True,
    },
    "series": {
        "index": (9, 189, 2366, 911, 2100),
        "ignore": (
            26,
            32,
            67,
            1147,
            191,
            190,
            2369,
            1493,
            1500,
            914,
            915,
            913,
            2101,
            2103,
        ),
        "media": "video",
        "scraper": SCRAPERS_SERIES[int(_setting_["rutracker_series"])],  # 'tvdb',
        "rating": "%1.1f",
        "stream": True,
    },
    "cartoon": {
        "index": (4, 921, 33),
        "ignore": (665, 86, 931, 932, 705, 1385, 535, 551, 1386, 1388, 282),
        "media": "video",
        "scraper": SCRAPERS_CARTOON[
            int(_setting_["rutracker_cartoon"])
        ],  # 'rutrackercartoon', # None,
        "rating": "%1.1f",  # False,
        "stream": True,
    },
    "documentary": {
        "index": (670, 46, 314, 24),
        "ignore": (73, 77, 891, 518, 523, 2172),
        "media": "video",
        "scraper": "rutrackerdocumentary",  # None,
        "rating": False,
        "stream": True,
    },
    "sport": {
        "index": (1315, 255, 1608, 2004, 2009, 845),
        "ignore": (261, 1609, 1999, 2000, 2312, 1476, 964, 1610),
        "media": "video",
        "scraper": "rutrackersport",  # None,
        "rating": False,
        "stream": True,
    },
    "training": {
        "index": (610, 1581, 1556),
        "ignore": (628, 1582, 1583, 1557),
        "media": "video",
        "scraper": "rutrackertraining",  # None,
        "rating": False,
        "stream": True,
    },
    "audiobook": {
        "index": (2326, 2389, 2327, 2324, 2328),
        "ignore": (0, 0),
        "media": "video",
        "scraper": "rutrackeraudiobook",  # None,
        "rating": False,
        "stream": True,
    },
    "avtomoto": {
        "index": (1202, None),
        "ignore": (0, 0),
        "media": "video",
        "scraper": "rutrackeravtomoto",  # None,
        "rating": False,
        "stream": True,
    },
    "music": {
        "index": (409, 1125, 1849, 408, 1760, 416, 1215, 413),
        "ignore": (792, 435, 443, 1140, 1846, 448, 1761, 473, 1218),
        "media": "video",
        "scraper": "rutrackermusic",  # None,
        "rating": False,
        "stream": True,
    },
    "popmusic": {
        "index": (2495, 2497, 2499, 2507),
        "ignore": (2496, 2498, 2506, 2511),
        "media": "video",
        "scraper": "rutrackerpopmusic",  # None,
        "rating": False,
        "stream": True,
    },
    "jazmusic": {
        "index": (2267, 2268, 2269, 2271),
        "ignore": (2272, 2273, 2274, 2276),
        "media": "video",
        "scraper": "rutrackerjazmusic",  # None,
        "rating": False,
        "stream": True,
    },
    "rockmusic": {
        "index": (1698, 1716, 1732, 722, 1781),
        "ignore": (733, 1717, 1718, 1733, 736, 1784),
        "media": "video",
        "scraper": "rutrackerrockmusic",  # None,
        "rating": False,
        "stream": True,
    },
    "electromusic": {
        "index": (1821, 1807, 1808, 1809, 1810, 1811, 1842, 1648, 1812),
        "ignore": (1845, 1848, 1851, 1854, 1870, 1883, 1892),
        "media": "video",
        "scraper": "rutrackerelectromusic",  # None,
        "rating": False,
        "stream": True,
    },
}
#


def GetProxyList():
    from http.client import HTTPConnection

    conn = HTTPConnection("antizapret.prostovpn.org")
    conn.request(
        "GET",
        "/proxy.pac",
        headers={
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)"
        },
    )
    r1 = conn.getresponse()
    data = r1.read().decode()
    conn.close()
    proxylist = re.compile(r"PROXY (.+?); DIRECT").findall(data)
    return proxylist


def proxy_update():
    proxy = GetProxyList()[0]
    _setting_["proxy_serv"] = proxy
    _setting_["proxy_time"] = str(time.time())


if _setting_["rutracker_unblock"] == "1":
    try:
        pt = float(_setting_["proxy_time"])
    except:
        pt = 0
    if time.time() - pt > 36000:
        proxy_update()


# для глобального поиска по фильмам, сериалам, мультипликации

index = []
ignore = []
tempru = RuTracker()
first_start = bool(_setting_["rutracker_login"] == "")
for i in ("movie", "series", "cartoon"):
    index.extend(CONTENT[i]["index"])
    ignore.extend(CONTENT[i]["ignore"])
    if not first_start:
        CONTENT[i]["tree"] = tempru._load_catalog(
            CONTENT[i]["index"], CONTENT[i]["ignore"]
        )
for i in range(index.count(None)):
    index.remove(None)
for i in range(ignore.count(0)):
    ignore.remove(0)
del tempru
index.sort()
ignore.sort()
CONTENT["global"] = {
    "index": index,
    "ignore": ignore,
    "media": "video",
    "scraper": "rutrackerglobal",
    "rating": False,
    "stream": True,
}

#

STATUS = {
    "moder": (40501, "FFFF0000"),
    "check": (40502, "FFFF0000"),
    "repeat": (40503, "FFFF0000"),
    "nodesc": (40504, "FFFF0000"),
    "copyright": (40505, "FFFF0000"),
    "close": (40506, "FFFF0000"),
    "absorb": (40507, "FFFF0000"),
    "nocheck": (40508, "FFFF9900"),
    "neededit": (40509, "FFFF9900"),
    "doubtful": (40510, "FFFF9900"),
    "temp": (40511, "FFFF9900"),
    "ok": (40512, "FF339933"),
}

GENRE = (
    ("anime", 80102),
    ("biography", 80103),
    ("action", 80104),
    ("western", 80105),
    ("military", 80106),
    ("detective", 80107),
    ("children", 80108),
    ("documentary", 80109),
    ("drama", 80110),
    ("game", 80111),
    ("history", 80112),
    ("comedy", 80113),
    ("concert", 80114),
    ("short", 80115),
    ("criminal", 80116),
    ("romance", 80117),
    ("music", 80118),
    ("cartoon", 80119),
    ("musical", 80120),
    ("news", 80121),
    ("adventures", 80122),
    ("realitytv", 80123),
    ("family", 80124),
    ("sports", 80125),
    ("talkshows", 80126),
    ("thriller", 80127),
    ("horror", 80128),
    ("fiction", 80129),
    ("filmnoir", 80130),
    ("fantasy", 80131),
)

WORK = (
    ("actor", "Актер"),
    ("director", "Режиссер"),
    ("writer", "Сценарист"),
    ("producer", "Продюсер"),
    ("composer", "Композитор"),
    ("operator", "Оператор"),
    ("editor", "Монтажер"),
    ("design", "Художник"),
    ("voice", "Актер дубляжа"),
    ("voice_director", "Режиссер дубляжа"),
)

MPAA = ("G", "PG", "PG-13", "R", "NC-17", "C", "GP")


# ########################
#
#   COMMON
#
# ########################


class TrailerParser:
    def __init__(self) -> None:
        self.lang = Lang()

    def trailer_parser(self, trailers):
        popup = []

        # готовим список для попап-меню
        for r in trailers:
            name = r["name"] + " [COLOR FFFFFFCC]["
            if r["ru"]:
                name += "RU, "
            if r["video"][0] > 3:
                name += "HD, "
            if r["time"]:
                name += r["time"] + ", "
            name += r["video"][2] + "][/COLOR]"
            popup.append((name, r["video"][1]))

        label = self.lang[40101] + " (" + str(len(popup)) + ")"
        if [1 for x in trailers if x["ru"]]:
            label += " RU"

        return label, popup


class Scrapers(TrailerParser):
    RE = {
        "year": re.compile(r"([1-2]{1}[0-9]{3})", re.U),
        "second": re.compile(r"^([^\[]*)\[(.+)\]([^\]]*)$", re.U),
    }
    kinopoisk = KinoPoisk()
    tvdb = TvDb()
    tmdb = TmDb()

    setting = AppSetting()

    def scraper(self, content, item, profile=None):
        # если есть специализированный скрабер, то запускаем его...
        if content == "kinopoisk":
            return self.scraper_kinopoisk(item)

        elif content == "tvdb":
            scraper = self.scraper_tvdb(item)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_series(item, profile)
            return scraper

        elif content == "rutrackermovies":
            return self.scraper_rutracker_movies(item, profile)

        elif content == "rutrackermovies_tmdb_rating":
            return self.scraper_rutracker_movies(item, profile, 1)

        elif content == "rutrackermovies_tmdb_rating_fanart":
            return self.scraper_rutracker_movies(item, profile, 2)

        elif content == "rutrackerseries":
            return self.scraper_rutracker_series(item, profile)

        elif content == "rutrackerseries_tmdb_rating":
            return self.scraper_rutracker_series(item, profile, 1)

        elif content == "rutrackerseries_tmdb_rating_fanart":
            return self.scraper_rutracker_series(item, profile, 2)

        elif content == "rutrackercartoon":
            return self.scraper_rutracker_cartoon(item, profile)

        elif content == "rutrackercartoon_tmdb_rating":
            return self.scraper_rutracker_cartoon(item, profile, 1)

        elif content == "rutrackercartoon_tmdb_rating_fanart":
            return self.scraper_rutracker_cartoon(item, profile, 2)

        elif content == "rutrackerdocumentary":
            return self.scraper_rutracker_documentary(item, profile)

        elif content == "rutrackersport":
            return self.scraper_rutracker_sport(item, profile)

        elif content == "rutrackertraining":
            return self.scraper_rutracker_training(item, profile)

        elif content == "rutrackeraudiobook":
            return self.scraper_rutracker_audiobook(item, profile)

        elif content == "rutrackeravtomoto":
            return self.scraper_rutracker_avtomoto(item, profile)

        elif content == "rutrackermusic":
            return self.scraper_rutracker_music(item, profile)

        elif content == "rutrackerpopmusic":
            return self.scraper_rutracker_popmusic(item, profile)

        elif content == "rutrackerjazmusic":
            return self.scraper_rutracker_jazmusic(item, profile)

        elif content == "rutrackerrockmusic":
            return self.scraper_rutracker_rockmusic(item, profile)

        elif content == "rutrackerelectromusic":
            return self.scraper_rutracker_electromusic(item, profile)

        elif content == "rutrackerglobal":
            return self.scraper_rutracker_global(item, profile)

        elif content == "tmdb_movie":
            scraper = self.scraper_tmdb_movie(item, profile)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_movies(item, profile)
            return scraper

        elif content == "tmdb_movie_tracker_plot":
            scraper = self.scraper_tmdb_movie(item, profile, 1)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_movies(item, profile)
            return scraper

        elif content == "tmdb_series":
            scraper = self.scraper_tmdb_series(item, profile)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_series(item, profile)
            return scraper

        elif content == "tmdb_series_tracker_plot":
            scraper = self.scraper_tmdb_series(item, profile, 1)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_series(item, profile)
            return scraper

        elif content == "tmdb_cartoon":
            scraper = self.scraper_tmdb_cartoon(item, profile)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_cartoon(item, profile)
            return scraper

        elif content == "tmdb_cartoon_tracker_plot":
            scraper = self.scraper_tmdb_cartoon(item, profile, 1)
            if scraper["notfind"]:
                scraper = self.scraper_rutracker_cartoon(item, profile)
            return scraper

        else:
            # иначе, используем стандартное отображение
            return self.scraper_rutracker(item)  # self.scraper_default(item)

    def scraper_kinopoisk(self, item):
        scraper = self.scraper_default(item)

        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in ("/", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            return scraper

        first = item["name"][0:index].strip()
        second = item["name"][index:].strip()
        r = self.RE["second"].search(second)
        if r:
            g = []
            for i in range(1, 4):
                if r.group(i):
                    if i == 2:
                        g.append("[" + r.group(i).strip() + "]")
                    else:
                        g.append(r.group(i).strip())
                else:
                    g.append("")
            split = first, g[0], g[1], g[2]
        else:
            split = first, second, "", ""

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        # компилируем имя
        name = "[COLOR FFEEEEEE][B]" + split[0] + "[/B][/COLOR]"
        if split[1]:
            name += " " + split[1]
        if split[2]:
            name += " [COLOR FFFFFFCC]" + split[2] + "[/COLOR]"
        if split[3]:
            name += " " + split[3]

        # запрос для поиска
        search = split[0]

        # пробуем вытащить дату
        r = self.RE["year"].search(split[2])
        if r:
            year = int(r.group(1))
        else:
            year = None

        kinopoisk = self.kinopoisk.scraper(
            search, year, int(self.setting["kinopoisk_quality"]) + 1
        )
        if not kinopoisk:
            return scraper

        # закладки
        scraper["bookmark"] = ("kinopoisk", kinopoisk["id"])

        # ХАК
        # добавляем runtime (длительность фильма) в описание (в скинах не видно)
        if "runtime" in kinopoisk["info"] and kinopoisk["info"]["runtime"]:
            if "plot" not in kinopoisk["info"]:
                kinopoisk["info"]["plot"] = ""
            kinopoisk["info"]["plot"] = "".join(
                [
                    self.lang[40102],
                    ": [B]",
                    kinopoisk["info"]["runtime"],
                    "[/B] ",
                    self.lang[40103],
                    "\n",
                    kinopoisk["info"]["plot"],
                ]
            )
            del kinopoisk["info"]["runtime"]
        # ХАК

        scraper["title"] = name
        scraper["thumb"] = kinopoisk["thumb"]
        scraper["fanart"] = kinopoisk["fanart"]
        scraper["info"].update(kinopoisk["info"])

        # для поиска похожих раздач
        if kinopoisk["info"].get("originaltitle"):
            scraper["search"] = kinopoisk["info"]["originaltitle"]
        elif kinopoisk["info"].get("title"):
            scraper["search"] = kinopoisk["info"]["title"]

        # для создания поддиректорий
        scraper["subdir"] = scraper["search"]
        if kinopoisk["info"].get("year"):
            scraper["subdir"] = ".".join(
                [scraper["subdir"], str(kinopoisk["info"]["year"])]
            )

        # трейлеры
        if kinopoisk["trailers"]:
            label, trailer_list = self.trailer_parser(kinopoisk["trailers"])
            scraper["popup"].append((Link("trailer", trailer_list), label))

        # рецензии
        scraper["popup"].append(
            (Link("review", {"id": kinopoisk["id"]}), self.lang[40007])
        )

        return scraper

    def scraper_tvdb(self, item):
        scraper = self.scraper_default(item)

        # пробуем получить сезон
        r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
        if r:
            scraper["info"]["season"] = int(r.group(1))

        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in ("/", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            return scraper

        first = item["name"][0:index].strip()
        second = item["name"][index:].strip()
        r = self.RE["second"].search(second)
        if r:
            g = []
            for i in range(1, 4):
                if r.group(i):
                    if i == 2:
                        g.append("[" + r.group(i).strip() + "]")
                    else:
                        g.append(r.group(i).strip())
                else:
                    g.append("")
            split = first, g[0], g[1], g[2]
        else:
            split = first, second, "", ""

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        # компилируем имя
        name = "[COLOR FFEEEEEE][B]" + split[0] + "[/B][/COLOR]"
        if split[1]:
            name += " " + split[1]
        if split[2]:
            name += " [COLOR FFFFFFCC]" + split[2] + "[/COLOR]"
        if split[3]:
            name += " " + split[3]

        # запрос для поиска
        search = split[0]

        # если название английское, ищем русское
        e = re.compile(r"[a-zA-Z]+", re.U | re.S).search(split[0])
        if e:
            for i in range(1, len(split)):
                c = re.compile(r"/([ 0-9а-яА-ЯёЁ,-]+)", re.U | re.S).search(split[i])
                if c:
                    c = c.group(1).strip()
                    if not c.isdigit():
                        search = c
                        break

        # пробуем вытащить дату
        r = self.RE["year"].search(split[2])
        if r:
            year = int(r.group(1))
        else:
            year = None

        scraper["tvdbsearch"] = search
        scraper["notfind"] = True

        tvdb = self.tvdb.scraper(search, year)
        if not tvdb:
            return scraper

        if tvdb["info"].get("originaltitle"):
            title_2 = tvdb["info"]["originaltitle"]
        elif tvdb["info"].get("title"):
            title_2 = tvdb["info"]["title"]
        if len(search) != len(title_2.strip()):
            for i in range(1, len(split)):
                c = re.compile(r"/([ 0-9а-яА-ЯёЁ,-]+)", re.U | re.S).search(split[i])
                if c:
                    c = c.group(1).strip()
                    if not c.isdigit():
                        if len(c) != len(title_2.strip()):
                            return scraper
                        break
                else:
                    return scraper

        scraper["notfind"] = False

        # закладки
        scraper["bookmark"] = ("tvdb", tvdb["id"])

        # ХАК
        # добавляем runtime (длительность фильма) в описание (в скинах не видно)
        if "runtime" in tvdb["info"] and tvdb["info"]["runtime"]:
            if "plot" not in tvdb["info"]:
                tvdb["info"]["plot"] = ""
            tvdb["info"]["plot"] = "".join(
                [
                    self.lang[40102],
                    ": [B]",
                    tvdb["info"]["runtime"],
                    "[/B] ",
                    self.lang[40103],
                    "\n",
                    tvdb["info"]["plot"],
                ]
            )
            del tvdb["info"]["runtime"]
        # ХАК

        scraper["title"] = name
        scraper["thumb"] = tvdb["thumb"]
        scraper["fanart"] = tvdb["fanart"]
        scraper["info"].update(tvdb["info"])

        # для поиска похожих раздач
        if tvdb["info"].get("originaltitle"):
            scraper["search"] = tvdb["info"]["originaltitle"]
        elif tvdb["info"].get("title"):
            scraper["search"] = tvdb["info"]["title"]

        # для создания поддиректорий
        # scraper['subdir'] = scraper['search']

        # трейлеры
        # if kinopoisk['trailers']:
        #    label, trailer_list = self.trailer_parser(kinopoisk['trailers'])
        #    scraper['popup'].append((Link('trailer', trailer_list), label))

        # рецензии
        # scraper['popup'].append((Link('review', {'id': kinopoisk['id']}), self.lang[40007]))

        return scraper

    def scraper_rutracker(self, item):
        scraper = self.scraper_default(item)

        # пробуем получить сезон
        r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
        if r:
            scraper["info"]["season"] = int(r.group(1))

        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in ("/", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            return scraper

        first = item["name"][0:index].strip()
        second = item["name"][index:].strip()
        r = self.RE["second"].search(second)
        if r:
            g = []
            for i in range(1, 4):
                if r.group(i):
                    if i == 2:
                        g.append("[" + r.group(i).strip() + "]")
                    else:
                        g.append(r.group(i).strip())
                else:
                    g.append("")
            split = first, g[0], g[1], g[2]
        else:
            split = first, second, "", ""

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        return scraper

    def scraper_rutracker_movies(self, item, profile, mode=0):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackermovies", item["id"])
        if mode > 0:
            year = None
            if scraper["info"].get("year"):
                year = scraper["info"]["year"]
            tmdb = self.tmdb.search_movie(scraper["search"], year)
            if tmdb:
                if tmdb["info"].get("rating"):
                    scraper["info"]["rating"] = tmdb["info"]["rating"]
                if tmdb["info"].get("votes"):
                    scraper["info"]["votes"] = tmdb["info"]["votes"]
        if mode > 1:
            if tmdb:
                if "thumb" in tmdb and tmdb["thumb"]:
                    scraper["thumb"] = tmdb["thumb"]
                if "fanart" in tmdb and tmdb["fanart"]:
                    scraper["fanart"] = tmdb["fanart"]
        return scraper

    def scraper_rutracker_series(self, item, profile, mode=0):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackerseries", item["id"])
        if mode > 0:
            onlytv = False
            r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
            if r:
                onlytv = True
            else:
                r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item["name"])
                if r:
                    onlytv = True
            year = None
            if scraper["info"].get("year"):
                year = scraper["info"]["year"]
            tmdb = self.tmdb.search_multi(
                scraper["search"], year, year_delta=1, only_tv=onlytv
            )
            if tmdb:
                if tmdb["info"].get("rating"):
                    scraper["info"]["rating"] = tmdb["info"]["rating"]
                if tmdb["info"].get("votes"):
                    scraper["info"]["votes"] = tmdb["info"]["votes"]
        if mode > 1:
            if tmdb:
                if "thumb" in tmdb and tmdb["thumb"]:
                    scraper["thumb"] = tmdb["thumb"]
                if "fanart" in tmdb and tmdb["fanart"]:
                    scraper["fanart"] = tmdb["fanart"]
        return scraper

    def scraper_rutracker_cartoon(self, item, profile, mode=0):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackercartoon", item["id"])
        if mode > 0:
            onlytv = False
            r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
            if r:
                onlytv = True
            else:
                r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item["name"])
                if r:
                    onlytv = True
            year = None
            if scraper["info"].get("year"):
                year = scraper["info"]["year"]
            tmdb = self.tmdb.search_multi(
                scraper["search"], year, year_delta=1, only_tv=onlytv
            )
            if tmdb:
                if tmdb["info"].get("rating"):
                    scraper["info"]["rating"] = tmdb["info"]["rating"]
                if tmdb["info"].get("votes"):
                    scraper["info"]["votes"] = tmdb["info"]["votes"]
        if mode > 1:
            if tmdb:
                if "thumb" in tmdb and tmdb["thumb"]:
                    scraper["thumb"] = tmdb["thumb"]
                if "fanart" in tmdb and tmdb["fanart"]:
                    scraper["fanart"] = tmdb["fanart"]
        return scraper

    def scraper_rutracker_documentary(self, item, profile):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackerdocumentary", item["id"])
        return scraper

    def scraper_rutracker_sport(self, item, profile):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackersport", item["id"])
        return scraper

    def scraper_rutracker_training(self, item, profile):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackertraining", item["id"])
        if scraper["search"] == "":
            r = re.compile(r"\] (.+?) \[", re.U | re.S).search(item["name"])
            if r:
                scraper["search"] = scraper["subdir"] = scraper["info"][
                    "originaltitle"
                ] = r.group(1).strip()
        return scraper

    def scraper_rutracker_audiobook(self, item, profile):
        scraper = self.scraper_default(item)

        # пробуем отделить основную часть имени
        index = 1000000
        for token in (" /", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            return scraper

        first = item["name"][0:index].strip()
        if first == "":
            r = re.compile(r"\] (.+?) \[", re.U | re.S).search(item["name"])
            if r:
                first = r.group(1).strip()
        second = item["name"][index:].strip()
        r = self.RE["second"].search(second)
        if r:
            g = []
            for i in range(1, 4):
                if r.group(i):
                    if i == 2:
                        g.append("[" + r.group(i).strip() + "]")
                    else:
                        g.append(r.group(i).strip())
                else:
                    g.append("")
            split = first, g[0], g[1], g[2]
        else:
            split = first, second, "", ""

        scraper["split"] = split

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        index = 1000000
        for token in (r" \u2013", r" \u2014", " -"):
            i = split[0].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            scraper["info"]["originaltitle"] = split[0]
        else:
            writer = split[0][0:index].strip()
            scraper["info"]["writer"] = writer
            index += 2
            bookname = split[0][index:].strip()
            scraper["info"]["originaltitle"] = bookname

        # если название русское, ищем английское
        r = re.compile(r"[а-яА-ЯёЁ]+", re.U | re.S).search(split[0])
        if r:
            # for i in range(1,len(split)):
            for c in re.compile(
                r"""/ ([ 0-9a-zA-Z'"/!:,&\-\.\?]+?)(?: /|\[|\()""", re.U | re.S
            ).findall(split[1] + split[2] + split[3]):
                if c:
                    c = c.strip()
                    if c and not c.isdigit():
                        scraper["search"] = c
                        scraper["info"]["originaltitle"] = c
                        break
                        # break

        if profile and profile["descript"]:
            descript = (
                profile["descript"]
                .replace("[/COLOR]", "")
                .replace("[COLOR FF0DA09E]", "")
            )

            def _r1():
                r = re.compile(
                    r"(?:Описание.*?|Рецензия.*?|Аннотация.*?):(.+?)(?:Доп. информация|Дополнительная информация|Качество|Тип релиза|Перевод|Релиз|Релиз группы):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["plot"] = r.group(1).strip(
                        "\n"
                    )  # .replace(u'\n',u'')
                else:
                    r = re.compile(r"\wписание:(.+?)$", re.U | re.S).search(descript)
                    if r is None:
                        r = re.compile(r"(Режисс\wр:.+?)$", re.U | re.S).search(
                            descript
                        )
                    if not r:
                        r = re.compile(r"(От издателя:.+?)$", re.U | re.S).search(
                            descript
                        )
                    if r:
                        scraper["info"]["plot"] = r.group(1).strip("\n")

            def _r2():
                r = re.compile(
                    r"Год выпуска:([0-9 \n]+?)(?:Имя автора|Автор|Фамилия автора):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
                else:  # пробуем вытащить год из названия
                    r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(
                        split[1] + split[2]
                    )
                    if r:
                        if r.group(1) != "1080":
                            scraper["info"]["year"] = (
                                r.group(1).replace("\n", "").strip()
                            )

            def _r3():
                r = re.compile(
                    r"Имя автора:(.+?)(?:Исполнител\w|Цикл/серия|Переводчик|Жанр):",
                    re.U | re.S,
                ).search(descript)
                c = re.compile(r"Фамилия автора:(.+?)Имя автора:", re.U | re.S).search(
                    descript
                )
                if r and c:
                    scraper["info"]["writer"] = (
                        r.group(1).replace("\n", "").strip()
                        + " "
                        + c.group(1).replace("\n", "").strip()
                    )
                else:
                    r = re.compile(
                        r"(?:Автор|Авторы):(.+?)(?:Исполнитель|Исполнители|Цикл/серия):",
                        re.U | re.S,
                    ).search(descript)
                    if r:
                        scraper["info"]["writer"] = r.group(1).replace("\n", "").strip()

            def _r4():
                r = re.compile(
                    r"Исполнител\w:(.+?)(?:Жанр|Цикл/серия|Серия/Цикл|Постер|Работа со звуком|Корректор|Обложк\w|Музыкальное оформление|Муз. оформление|Ремастеринг|Номер книги|Отредактировано|Иллюстрация|Режисс\wр проекта|Цикл|Издательство|Год издания|Прочитано по изданию|Тип издания|Категория|Переводчик|Серия|Перевод|Возрастное ограничение|Жанр/направление):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["director"] = r.group(1).replace("\n", "").strip()
                r = re.compile(
                    r"Жанр[/направление]*:(.+?)(?:Издательство|Тип издания\s?|Прочитано по изданию|Цикл/серия|Перевод|Категория|Выпущено|Издатель|Звукорежисс\wр|Автор|Обложка|Работа над обложкой|Отредактировано|Рейтинг|Музыка|Оцифровано|Исполнитель|Переводчик|Студия|Продолжительность|Серия|Адаптация|Серия/Цикл|Тип аудиокниги|Формат|Тип|Обработано|Цикл|Составитель|Теги|Музыка[ ]*|Дизайнер обложки|Постер|Музыкальное оформление):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["genre"] = r.group(1).replace("\n", "").strip()

            r = re.compile(
                r"(?:Время звучания|Продолжительность):[ ~]*?(\d{1,2}:\d\d:\d\d)",
                re.U | re.S,
            ).search(descript)
            if r:
                d = r.group(1)  # .split(':')
                scraper["info"]["tagline"] = (
                    "Время звучания: " + d
                )  # (int(d[0])*60+int(d[1]))*60+int(d[2])
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t3 = thr.Thread(target=_r3)
            t4 = thr.Thread(target=_r4)
            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t1.join()
            t2.join()
            t3.join()
            t4.join()
        else:
            r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(split[1] + split[2])
            if r:
                if r.group(1) != "1080":
                    scraper["info"]["year"] = r.group(1).replace("\n", "").strip()

        if profile and profile["cover"]:
            scraper["thumb"] = profile["cover"]
        if profile and profile["screenshot"]:
            scraper["fanart"] = profile["screenshot"][0]

        scraper["rutracker"] = True

        scraper["bookmark"] = ("rutrackeraudiobook", item["id"])
        return scraper

    def scraper_rutracker_avtomoto(self, item, profile):
        scraper = self.scraper_rutracker_video(item, profile)
        scraper["bookmark"] = ("rutrackeravtomoto", item["id"])
        return scraper

    def scraper_rutracker_music(self, item, profile):
        scraper = self.scraper_rutracker_audio(item, profile)
        scraper["bookmark"] = ("rutrackermusic", item["id"])
        return scraper

    def scraper_rutracker_popmusic(self, item, profile):
        scraper = self.scraper_rutracker_audio(item, profile)
        scraper["bookmark"] = ("rutrackerpopmusic", item["id"])
        return scraper

    def scraper_rutracker_jazmusic(self, item, profile):
        scraper = self.scraper_rutracker_audio(item, profile)
        scraper["bookmark"] = ("rutrackerjazmusic", item["id"])
        return scraper

    def scraper_rutracker_rockmusic(self, item, profile):
        scraper = self.scraper_rutracker_audio(item, profile)
        scraper["bookmark"] = ("rutrackerrockmusic", item["id"])
        return scraper

    def scraper_rutracker_electromusic(self, item, profile):
        scraper = self.scraper_rutracker_audio(item, profile)
        scraper["bookmark"] = ("rutrackerelectromusic", item["id"])
        return scraper

    def scraper_rutracker_global(self, item, profile):
        scraper = self.scraper_rutracker_video(item, profile)
        if item["f_id"] in CONTENT["movie"]["tree"]:
            scraper["bookmark"] = ("rutrackermovies", item["id"])
            scraper["content"] = "movie"
        elif item["f_id"] in CONTENT["series"]["tree"]:
            scraper["bookmark"] = ("rutrackerseries", item["id"])
            scraper["content"] = "series"
        elif item["f_id"] in CONTENT["cartoon"]["tree"]:
            scraper["bookmark"] = ("rutrackercartoon", item["id"])
            scraper["content"] = "cartoon"
        else:
            scraper["bookmark"] = ("rutrackerglobal", item["id"])
            scraper["content"] = "global"
        return scraper

    def scraper_rutracker_audio(self, item, profile):
        scraper = self.scraper_default(item)

        # пробуем получить сезон
        # r = re.compile(r'Сезон[\:]{0,1}[\s]{1,}([0-9]+)', re.U).search(item['name'])
        # if r:
        # scraper['info']['season'] = int(r.group(1))
        # scraper['info']['mediatype'] = 'episode'

        # пробуем отделить основную часть имени фильма
        year = None
        index = 1000000
        for token in (" /", "(", " ["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            split = item["name"].strip() + " ", "", "", ""

        else:
            first = item["name"][0:index].strip()
            second = item["name"][index:].strip()
            if first == "":
                r = re.compile(
                    r"\)(.+?)(?:\-|\u2013|\u2014)* [\[\(]*([1-2]{1}\d\d\d)[\-\d\(\)/ \w]*(?:,| \[|\]|\),)",
                    re.U,
                ).search(item["name"])
                if r:
                    first = (
                        r.group(1)
                        .replace("[CDR]", "")
                        .replace("[CD]", "")
                        .replace("[WEB]", "")
                        .strip()
                    )
                    year = r.group(2)
                else:
                    r = re.compile(r"\)(.+?)\[", re.U).search(item["name"])
                    if not r:
                        r = re.compile(r"\)(.+?)\) \(", re.U).search(item["name"])
                    if not r:
                        r = re.compile(r"([1-2]{1}\d\d\d)", re.U).search(item["name"])
                        if r:
                            year = r.group(1)
                        r = re.compile(r"\)(.+?) \(", re.U).search(item["name"])
                    if r:
                        first = (
                            r.group(1)
                            .replace("[CDR]", "")
                            .replace("[CD]", "")
                            .replace("[WEB]", "")
                            .strip()
                        )
                        r = re.compile(r"([1-2]{1}\d\d\d)", re.U).search(first)
                        if r:
                            year = r.group(1)
            if first != "":
                i = first.find(" (")
                if i > 1:
                    first = first[:i]
            r = self.RE["second"].search(second)
            if r:
                g = []
                for i in range(1, 4):
                    if r.group(i):
                        if i == 2:
                            g.append("[" + r.group(i).strip() + "]")
                        else:
                            g.append(r.group(i).strip())
                    else:
                        g.append("")
                split = first, g[0], g[1], g[2]
            else:
                split = first, second, "", ""

        scraper["split"] = split

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        # scraper['info']['tvshowtitle'] = split[0]
        scraper["info"]["originaltitle"] = split[0]
        # если название русское, ищем английское
        r = re.compile(r"[а-яА-ЯёЁ]+", re.U | re.S).search(split[0])
        if r:
            index = 1000000
            find_str_org = split[1] + split[2] + split[3]
            # отключено из-за косяка с названиями вида  Русское (тут еще) / English  ( ) [ ]
            """
                for token in (u'(', u'['):
                            i = find_str_org.find(token)
                            if i != -1 and i < index:
                                index = i
                if index != 1000000:
                        find_str_org = find_str_org[0:index+1].strip()
                """
            #
            for c in re.compile(
                r"""/ ([ 0-9a-zA-Z'"/!:,&\-\.\?]+?)(?: /|\[|\()""", re.U | re.S
            ).findall(find_str_org):
                if c:
                    c = c.strip()
                    if c and not c.isdigit():
                        scraper["search"] = c
                        scraper["info"]["originaltitle"] = c
                        # scraper['info']['tvshowtitle'] = c
                        break
                        # break

        if profile and profile["descript"]:
            descript = (
                profile["descript"]
                .replace("[/COLOR]", "")
                .replace("[COLOR FF0DA09E]", "")
            )

            r = re.compile(
                r"(?:\wписание|О фильме|Рецензия.*?|Аннотация.*?|О спектакле):(.+?)(?:Доп. информация|Дополнительная информация|С\wмпл|Качество видео|Качество|Тип релиза|Video|Перевод|Релиз|Релиз группы|Информационные ссылки):",
                re.U | re.S,
            ).search(descript)
            if r:
                scraper["info"]["plot"] = r.group(1).strip("\n")  # .replace(u'\n',u'')
            else:
                r = re.compile(r"\wписание:(.+?)$", re.U | re.S).search(descript)
                if r:
                    scraper["info"]["plot"] = r.group(1).strip("\n")
                else:
                    r = re.compile(
                        r"(?:\wписание|ОПИСАНИЕ|Содержание:)(.+?)(?:Доп. информация|Качество видео|Качество:)",
                        re.U | re.S,
                    ).search(descript)
                    if r:
                        scraper["info"]["plot"] = r.group(1).strip("\n")
                    else:
                        r = re.compile(r"Тр\wклист:(.+?)$", re.U | re.S).search(
                            descript
                        )
                        if r:
                            scraper["info"]["plot"] = r.group(1).strip("\n")
            r = re.compile(
                r"(?:Жанр|Жанры):(.+?)(?:Год .*?|Продолжительность|Перевод|Страна|Тип|Продолжительность серии|Студия|Серии.*?|Язык|Рейтинг MPAA|Субтитры|Производство|Годы выпуска.*?|Режисс\wр|Носитель|Лейбл|Страна-производитель диска|Страна исполнителя.*?):",
                re.U | re.S,
            ).search(descript)
            if r is None:
                r = re.compile(
                    r"Тематика:(.+?)(?:Тип раздаваемого материала|Тип материала):",
                    re.U | re.S,
                ).search(descript)
            if r:
                scraper["info"]["genre"] = r.group(1).replace("\n", "").strip()
            r = re.compile(
                r"(?:Год выпуска|Год выхода):([0-9 \n]+?)(?:Продолжительность|Перевод|Страна):",
                re.U | re.S,
            ).search(descript)
            if r:
                scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
            else:  # пробуем вытащить год из названия
                r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(split[2])
                if r:
                    if r.group(1) != "1080":
                        scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
                elif year:
                    if int(year) > 1900:
                        scraper["info"]["year"] = year.strip()
            r = re.compile(
                r"(?:Режисс\wр|Режисс\wры|Режисс\wр-постановщик):(.+?)(?:В ролях|Сценарий|Сценарист|Студия|Описание|Роли озвучивали|Роли дублировали|Снято по манге|Автор оригинала|Телеканал|Источник|Композитор|Ведущий|Режисс\wр дубляжа|Субтитры|Перевод|Композиторы|Продолжительность|Роли озвучивают|Название|Тематика):",
                re.U | re.S,
            ).search(descript)
            if r:
                scraper["info"]["director"] = r.group(1).replace("\n", "").strip()
            r = re.compile(
                r"(?:Страна|Выпущено|Страны):(.+?)(?:Жанр|Студия|Слоган|Производство|Год выпуска|Продолжительность|Тип|Премьера|Жанры|Тематика|Язык|Режисс\wр|Сезон|Аудиокодек|Год издания):",
                re.U | re.S,
            ).search(descript)
            if not r:
                r = re.compile(
                    r"(?:Страна-производитель диска|Страна исполнителя.*?):(.+?)(?:Год издания диска|Год издания):",
                    re.U | re.S,
                ).search(descript)
            c = re.compile(
                r"(?:Студия|Производство):(.+?)(?:Жанр|Описание|Премьера|Субтитры|Режисс\wр|Режисс\wры|Перевод|Озвучка|Продолжительность|В ролях|Год выпуска|Роли озвучивали.*?|Язык):",
                re.U | re.S,
            ).search(descript)
            if not c:
                c = re.compile(
                    r"(?:Производитель диска|Производитель дисков|Издатель \(лейбл\)):(.+?)(?:Аудио кодек|Номер по каталогу|Аудиокодек|Дата записи):",
                    re.U | re.S,
                ).search(descript)
            if r and c:
                separatorstr = ", "
                if c.group(1).replace("\n", "").strip() == "":
                    separatorstr = ""
                scraper["info"]["studio"] = (
                    r.group(1).replace("\n", "").strip()
                    + separatorstr
                    + c.group(1).replace("\n", "").strip().replace("Без озвучки", "")
                )
                scraper["info"]["writer"] = scraper["info"]["studio"]
            elif r:
                scraper["info"]["studio"] = (
                    r.group(1)
                    .replace("\n", "")
                    .strip()
                    .replace("Выпущено:", ",")
                    .replace("Киностудии:", ",")
                    .replace("Кинокомпания:", ",")
                    .replace("Студии:", ",")
                    .replace("Лейбл:", ",")
                )
                scraper["info"]["writer"] = scraper["info"]["studio"]
            elif c:
                scraper["info"]["studio"] = (
                    c.group(1).replace("\n", "").strip().replace("Дистрибьютеры:", ",")
                )
                scraper["info"]["writer"] = scraper["info"]["studio"]
            r = re.compile(
                r"В ролях:(.+?)(?:\wписание.*?|О фильме|IMDB):", re.U | re.S
            ).search(descript)
            if r:
                scraper["info"]["cast"] = [
                    i.strip()
                    for i in r.group(1).replace("\n", ",").strip().split(",")
                    if i
                ]
            if r is None:
                r = re.compile(
                    r"(?:Роли озвучивали|Роли озвучивают):(.+?)(?:\wписание|Роли дублировали|Содержание):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["cast"] = [
                        i.strip()
                        for i in r.group(1).replace("\n", ",").strip().split(",")
                        if i
                    ]
        else:
            r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(split[2])
            if r:
                if r.group(1) != "1080":
                    scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
        if profile and profile["cover"]:
            scraper["thumb"] = profile["cover"]
        if profile and profile["screenshot"]:
            scraper["fanart"] = profile["screenshot"][0]

        scraper["rutracker"] = True

        return scraper

    def scraper_rutracker_video(self, item, profile):
        scraper = self.scraper_default(item)

        # пробуем получить сезон
        r = re.compile(
            r"((?:/(?:\s{1,}Сезон[ы\:]{0,2}[\s]{1,}[0-9\-, \(\)]+[\sиз0-9]*\s{1,}/\s{1,}|\s{1,})Серии[\:]{0,1}\s{1,}[0-9\u2013\u2014\-]+[\sиз0-9\(\)\?\-]*|\[[0-9\-\+ ]+ из [0-9XХ\+\?]+\]))",
            re.U,
        ).search(item["name"])
        if r:
            scraper["info"]["plotoutline"] = (
                r.group(1)
                .replace("[", "Серии: ")
                .strip("]")
                .strip("/")
                .strip("(")
                .strip()
            )
        # r = re.compile(r'Сезон[\:]{0,1}[\s]{1,}([0-9]+)', re.U).search(item['name'])
        # if r:
        # scraper['info']['season'] = int(r.group(1))
        # scraper['info']['mediatype'] = 'episode'
        if item["name"].startswith("["):
            item["name"] = item["name"][item["name"].find("]") + 1 :]
        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in (" /", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            split = item["name"].strip() + " ", "", "", ""

        else:
            first = item["name"][0:index].strip()
            second = item["name"][index:].strip()
            r = self.RE["second"].search(second)
            if r:
                g = []
                for i in range(1, 4):
                    if r.group(i):
                        if i == 2:
                            g.append("[" + r.group(i).strip() + "]")
                        else:
                            g.append(r.group(i).strip())
                    else:
                        g.append("")
                split = first, g[0], g[1], g[2]
            else:
                split = first, second, "", ""

        scraper["split"] = split

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        # scraper['info']['tvshowtitle'] = split[0]
        scraper["info"]["originaltitle"] = split[0]
        # если название русское, ищем английское
        r = re.compile(r"[а-яА-ЯёЁ]+", re.U | re.S).search(split[0])
        if r:
            index = 1000000
            find_str_org = split[1] + split[2] + split[3]
            # отключено из-за косяка с названиями вида  Русское (тут еще) / English  ( ) [ ]
            """
                for token in (u'(', u'['):
                            i = find_str_org.find(token)
                            if i != -1 and i < index:
                                index = i
                if index != 1000000:
                        find_str_org = find_str_org[0:index+1].strip()
                """
            # XXX
            for c in re.compile(
                r"""/ ([ 0-9a-zA-Z`\u2026\u2013\u2014\u00c7\u00c9\u00d6\u00dc\u00df\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6\u00e7\u00e8\u00ea\u2019\u00e9\u00ec\u00ed\u00ee\u00ef\u00f1\u00f2\u00f6\u00f3\u00f4\u00f8\u00fa\u00fc\u00fd\u010d\u011b\u011f\u0130\u0131\u0159\u015e\u015f\u0160\u0161'"~/!:,&#\-\.\?\*]+?)(?: /|\[|\()""",
                re.U | re.S,
            ).findall(find_str_org.replace(" / ", " // ")):
                if c:
                    c = c.strip()
                    if c and not c.isdigit():
                        scraper["search"] = c
                        scraper["info"]["originaltitle"] = c
                        # scraper['info']['tvshowtitle'] = c
                        break
                        # break

        if profile and profile["descript"]:
            descript = (
                profile["descript"]
                .replace("[/COLOR]", "")
                .replace("[COLOR FF0DA09E]", "")
            )

            def delstartsstr(s, sdel):
                if s.startswith(sdel):
                    s = s[len(sdel) :]
                return s

            def _r1():
                r = re.compile(
                    r"(?:\wписание|О фильме|Рецензия.*?|Аннотация.*?|О спектакле):(.+?)(?:Доп. информация|Дополнительная информация|С\wмпл|Качество видео|Качество|Тип релиза|Video|Перевод|Релиз|Релиз группы|Информационные ссылки):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["plot"] = r.group(1).strip(
                        "\n"
                    )  # .replace(u'\n',u'')
                else:
                    r = re.compile(r"\wписание:(.+?)$", re.U | re.S).search(descript)
                    if r:
                        scraper["info"]["plot"] = r.group(1).strip("\n")
                    else:
                        r = re.compile(
                            r"(?:\wписание|ОПИСАНИЕ|Содержание:)(.+?)(?:Доп. информация|Качество видео|Качество|Тип релиза:)",
                            re.U | re.S,
                        ).search(descript)
                        if r:
                            scraper["info"]["plot"] = delstartsstr(
                                r.group(1), " фильма:"
                            ).strip("\n")

            def _r2():
                r = re.compile(
                    r"(?:Жанр|Жанры)[ ]?:(.+?)(?:Год выпуска.*?|Продолжительность|Перевод.*?|Страна|Тип|Продолжительность серии|Студия|Серии.*?|Язык|Год выхода|Рейтинг MPAA|Субтитры|Производство|Годы выпуска|Режисс\wр|Оригинальное название|Год|Production \wo|Средняя продолжительность серии):",
                    re.U | re.S,
                ).search(descript)
                if r is None:
                    r = re.compile(
                        r"Тематика:(.+?)(?:Тип раздаваемого материала|Тип материала):",
                        re.U | re.S,
                    ).search(descript)
                if r:
                    scraper["info"]["genre"] = r.group(1).replace("\n", "").strip()

            def _r3():
                r = re.compile(
                    r"(?:Год выпуска|Год выхода):([0-9 \n]+?)(?:Продолжительность|Перевод|Страна):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
                else:  # пробуем вытащить год из названия
                    r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(split[2])
                    if r:
                        if r.group(1) != "1080":
                            scraper["info"]["year"] = (
                                r.group(1).replace("\n", "").strip()
                            )
                r = re.compile(
                    r"(?:Режисс\wр|Режисс\wры|Режисс\wр-постановщик):(.+?)(?:В ролях|Сценарий|Сценарист|Студия|Описание|Роли озвучивали|Роли дублировали|Снято по манге|Автор оригинала|Телеканал|Источник|Композитор|Ведущий|Режисс\wр дубляжа|Субтитры|Перевод|Композиторы|Продолжительность|Роли озвучивают|Название|Тематика|Роли и исполнители|В главных ролях|Продюсер|Продюсеры):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["director"] = r.group(1).replace("\n", "").strip()

            def _r4():
                r = re.compile(
                    r"(?:Страна|Выпущено|Страны):(.+?)(?:Жанр|\wтудия|Слоган|Производство|Год выпуска|Продолжительность|Тип|Премьера|Жанры|Тематика|Язык|Режисс\wр|Сезон|Выпуск|Трансляция|Перевод|Киностудия)[ ]?:",
                    re.U | re.S,
                ).search(descript)
                c = re.compile(
                    r"(?:Студия|Производство):(.+?)(?:Жанр|Описание|Премьера|Субтитры|Режисс\wр|Режисс\wры|Перевод|Озвучка|Продолжительность|В ролях|Год выпуска|Роли озвучивали.*?|Язык|Перевод на русский|Ссылк\w|Многоголосая озвучка от):",
                    re.U | re.S,
                ).search(descript)
                if r and c:
                    separatorstr = ", "
                    if c.group(1).replace("\n", "").strip() == "":
                        separatorstr = ""
                    scraper["info"]["studio"] = (
                        r.group(1).replace("\n", "").strip()
                        + separatorstr
                        + c.group(1)
                        .replace("\n", "")
                        .strip()
                        .replace("Без озвучки", "")
                    )
                    scraper["info"]["writer"] = scraper["info"]["studio"]
                elif r:
                    scraper["info"]["studio"] = (
                        r.group(1)
                        .replace("\n", "")
                        .strip()
                        .replace("Выпущено:", ",")
                        .replace("Киностудии:", ",")
                        .replace("Кинокомпании:", ",")
                        .replace("Студии:", ",")
                        .replace("Киностудия:", ",")
                        .replace("Кинокомпания:", ",")
                        .replace("Студия:", ",")
                        .replace("Студия :", ",")
                        .replace("Издатель:", ", ")
                        .replace("Production Co:", ",")
                        .strip(", ")
                    )
                    scraper["info"]["writer"] = scraper["info"]["studio"]
                elif c:
                    scraper["info"]["studio"] = c.group(1).replace("\n", "").strip()
                    scraper["info"]["writer"] = scraper["info"]["studio"]

            r = re.compile(
                r"(?:В [главных ]*ролях|Роли и исполнители|Актеры):(.+?)(?:\wписание.*?|О фильме|IMDB|Рецензия.*?):",
                re.U | re.S,
            ).search(descript)
            if r:
                scraper["info"]["cast"] = [
                    i.strip()
                    for i in r.group(1).replace("\n", ",").strip().split(",")
                    if i
                ]
            if r is None:
                r = re.compile(
                    r"(?:Роли озвучивали|Роли озвучивают):(.+?)(?:\wписание|Роли дублировали|Содержание):",
                    re.U | re.S,
                ).search(descript)
                if r:
                    scraper["info"]["cast"] = [
                        i.strip()
                        for i in r.group(1).replace("\n", ",").strip().split(",")
                        if i
                    ]
            r = re.compile(
                r"Продолжительность:[ ~]*?(\d{1,2}:\d\d:\d\d)", re.U | re.S
            ).search(descript)
            if r:
                d = r.group(1)  # .split(':')
                scraper["info"]["tagline"] = (
                    "Продолжительность: " + d
                )  # (int(d[0])*60+int(d[1]))*60+int(d[2])
            t1 = thr.Thread(target=_r1)
            t2 = thr.Thread(target=_r2)
            t3 = thr.Thread(target=_r3)
            t4 = thr.Thread(target=_r4)
            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t1.join()
            t2.join()
            t3.join()
            t4.join()
        else:
            r = re.compile(r"([1-2]{1}\d{3})", re.U | re.S).search(split[2])
            if r:
                if r.group(1) != "1080":
                    scraper["info"]["year"] = r.group(1).replace("\n", "").strip()
        if profile and profile["cover"]:
            scraper["thumb"] = profile["cover"]
        if profile and profile["screenshot"]:
            scraper["fanart"] = profile["screenshot"][0]

        scraper["rutracker"] = True

        return scraper

    def scraper_tmdb_movie(self, item, profile, mode=0):
        scraper = self.scraper_default(item)

        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in (" /", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            split = item["name"].strip() + " ", "", "", ""

        else:
            first = item["name"][0:index].strip()
            second = item["name"][index:].strip()
            r = self.RE["second"].search(second)
            if r:
                g = []
                for i in range(1, 4):
                    if r.group(i):
                        if i == 2:
                            g.append("[" + r.group(i).strip() + "]")
                        else:
                            g.append(r.group(i).strip())
                    else:
                        g.append("")
                split = first, g[0], g[1], g[2]
            else:
                split = first, second, "", ""

        scraper["split"] = split

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        scraper["info"]["originaltitle"] = split[0]
        # если название русское, ищем английское
        r = re.compile(r"[а-яА-ЯёЁ]+", re.U | re.S).search(split[0])
        if r:
            index = 1000000
            find_str_org = split[1] + split[2] + split[3]
            # отключено из-за косяка с названиями вида  Русское (тут еще) / English  ( ) [ ]
            """
                for token in (u'(', u'['):
                            i = find_str_org.find(token)
                            if i != -1 and i < index:
                                index = i
                if index != 1000000:
                        find_str_org = find_str_org[0:index+1].strip()
                """
            #
            for c in re.compile(
                r"""/ ([ 0-9a-zA-Z`\u2026\u2013\u2014\u00c7\u00c9\u00d6\u00dc\u00df\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6\u00e7\u00e8\u00ea\u2019\u00e9\u00ec\u00ed\u00ee\u00ef\u00f1\u00f2\u00f3\u00f4\u00f6\u00f8\u00fa\u00fc\u00fd\u010d\u011b\u011f\u0130\u0131\u0159\u015e\u015f\u0160\u0161'"~/!:,&#\-\.\?\*]+?)(?: /|\[|\()""",
                re.U | re.S,
            ).findall(find_str_org.replace(" / ", " // ")):
                if c:
                    c = c.strip()
                    if c and not c.isdigit():
                        scraper["search"] = c
                        scraper["info"]["originaltitle"] = c
                        break

        # компилируем имя
        name = "[COLOR FFEEEEEE][B]" + split[0] + "[/B][/COLOR]"
        if split[1]:
            name += " " + split[1]
        if split[2]:
            name += " [COLOR FFFFFFCC]" + split[2] + "[/COLOR]"
        if split[3]:
            name += " " + split[3]

        # запрос для поиска
        search = split[0]

        # пробуем вытащить дату
        r = self.RE["year"].search(split[2])
        if r:
            year = int(r.group(1))
        else:
            year = None

        scraper["notfind"] = True

        tmdb = self.tmdb.scraper_movie(scraper["search"], year)
        if not tmdb:
            return scraper
        # if year:
        #        if year != tmdb['info']['year']:
        #                                return scraper

        if mode > 0:  # если осутствует описание, то берем его с трекера
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            if tmdb["info"]["plot"] == "":
                if profile and profile["descript"]:
                    descript = (
                        profile["descript"]
                        .replace("[/COLOR]", "")
                        .replace("[COLOR FF0DA09E]", "")
                    )

                    r = re.compile(
                        r"(?:\wписание|О фильме|Рецензия.*?|Аннотация.*?|О спектакле):(.+?)(?:Доп. информация|Дополнительная информация|С\wмпл|Качество видео|Качество|Тип релиза|Video|Перевод|Релиз|Релиз группы|Информационные ссылки):",
                        re.U | re.S,
                    ).search(descript)
                    if r:
                        tmdb["info"]["plot"] = r.group(1).strip("\n")
                    else:
                        r = re.compile(r"\wписание:(.+?)$", re.U | re.S).search(
                            descript
                        )
                        if r:
                            tmdb["info"]["plot"] = r.group(1).strip("\n")
                        else:
                            r = re.compile(
                                r"(?:\wписание|ОПИСАНИЕ|Содержание:)(.+?)(?:Доп. информация|Качество видео|Качество|Тип релиза:)",
                                re.U | re.S,
                            ).search(descript)
                            if r:
                                tmdb["info"]["plot"] = r.group(1).strip("\n")

        # ХАК
        # добавляем runtime (длительность фильма) в описание (в скинах не видно)
        if "runtime" in tmdb and tmdb["runtime"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n\n",
                    self.lang[40102],
                    ": [B]",
                    str(tmdb["runtime"]),
                    "[/B] ",
                    self.lang[40103],
                ]
            )
        if "budget" in tmdb and tmdb["budget"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n",
                    self.lang[40104],
                    ": [B]",
                    str(tmdb["budget"]),
                    "[/B] $",
                ]
            )
        if "revenue" in tmdb and tmdb["revenue"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n",
                    self.lang[40105],
                    "   : [B]",
                    str(tmdb["revenue"]),
                    "[/B] $",
                ]
            )
        # ХАК

        scraper["title"] = name
        scraper["fanart"] = tmdb["fanart"]
        scraper["thumb"] = tmdb["thumb"]
        scraper["cast"] = tmdb["cast"]
        scraper["info"].update(tmdb["info"])

        scraper["notfind"] = False

        # закладки
        try:  # проверка на 'китайское' название
            s = scraper["info"]["title"].encode("windows-1251")
        except:
            scraper["bookmark"] = ("rutrackermovies", str(item["id"]))
            scraper["rutracker"] = True
            scraper["rt_year"] = year
        else:
            scraper["bookmark"] = ("tmdb_movie", str(tmdb["id"]))

        return scraper

    def scraper_tmdb_series(self, item, profile, mode=0):
        only_tv = False
        r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
        if r:
            only_tv = True
        else:
            r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item["name"])
            if r:
                only_tv = True
        scraper = self.scraper_tmdb_multi(item, profile, mode, only_tv)
        # закладки
        if not scraper["notfind"]:
            if scraper.get("rutracker"):
                scraper["bookmark"] = ("rutrackerseries", str(item["id"]))
            else:
                scraper["bookmark"] = ("tmdb_series", str(scraper["id"]))
                if scraper.get("m_type"):
                    if scraper["m_type"] == "tv":
                        scraper["bookmark"] = ("tmdb_series_tv", str(scraper["id"]))
        return scraper

    def scraper_tmdb_cartoon(self, item, profile, mode=0):
        only_tv = False
        r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item["name"])
        if r:
            only_tv = True
        else:
            r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item["name"])
            if r:
                only_tv = True
        scraper = self.scraper_tmdb_multi(item, profile, mode, only_tv)
        # закладки
        if not scraper["notfind"]:
            if (scraper["info"]["genre"] != "") and (
                "мультфильм" not in scraper["info"]["genre"]
            ):
                scraper["notfind"] = True
                return scraper
            if scraper.get("rutracker"):
                scraper["bookmark"] = ("rutrackercartoon", str(item["id"]))
            else:
                scraper["bookmark"] = ("tmdb_cartoon", str(scraper["id"]))
                if scraper.get("m_type"):
                    if scraper["m_type"] == "tv":
                        scraper["bookmark"] = ("tmdb_cartoon_tv", str(scraper["id"]))
        return scraper

    def scraper_tmdb_multi(self, item, profile, mode=0, only_tv=False):
        scraper = self.scraper_default(item)

        # ищем количество серий и сезонов в раздаче
        r = re.compile(
            r"((?:/(?:\s{1,}Сезон[ы\:]{0,2}[\s]{1,}[0-9\-, \(\)]+[\sиз0-9]*\s{1,}/\s{1,}|\s{1,})Серии[\:]{0,1}\s{1,}[0-9\u2013\u2014\-]+[\sиз0-9\(\)\?\-]*|\[[0-9\-\+ ]+ из [0-9XХ\+\?]+\]))",
            re.U,
        ).search(item["name"])
        if r:
            scraper["info"]["plotoutline"] = (
                r.group(1)
                .replace("[", "Серии: ")
                .strip("]")
                .strip("/")
                .strip("(")
                .strip()
            )
        # пробуем отделить основную часть имени фильма
        index = 1000000
        for token in (" /", "(", "["):
            i = item["name"].find(token)
            if i != -1 and i < index:
                index = i
        if index == 1000000:
            split = item["name"].strip() + " ", "", "", ""

        else:
            first = item["name"][0:index].strip()
            second = item["name"][index:].strip()
            r = self.RE["second"].search(second)
            if r:
                g = []
                for i in range(1, 4):
                    if r.group(i):
                        if i == 2:
                            g.append("[" + r.group(i).strip() + "]")
                        else:
                            g.append(r.group(i).strip())
                    else:
                        g.append("")
                split = first, g[0], g[1], g[2]
            else:
                split = first, second, "", ""

        scraper["split"] = split

        # для поиска похожих раздач и поддиректорий
        scraper["search"] = scraper["subdir"] = split[0]

        scraper["info"]["originaltitle"] = split[0]
        # если название русское, ищем английское
        r = re.compile(r"[а-яА-ЯёЁ]+", re.U | re.S).search(split[0])
        if r:
            index = 1000000
            find_str_org = split[1] + split[2] + split[3]
            # отключено из-за косяка с названиями вида  Русское (тут еще) / English  ( ) [ ]
            """
                for token in (u'(', u'['):
                            i = find_str_org.find(token)
                            if i != -1 and i < index:
                                index = i
                if index != 1000000:
                        find_str_org = find_str_org[0:index+1].strip()
                """
            #
            for c in re.compile(
                r"""/ ([ 0-9a-zA-Z`\u2026\u2013\u2014\u00c7\u00c9\u00d6\u00dc\u00df\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6\u00e7\u00e8\u00ea\u2019\u00e9\u00ec\u00ed\u00ee\u00ef\u00f1\u00f2\u00f3\u00f4\u00f6\u00f8\u00fa\u00fc\u00fd\u010d\u011b\u011f\u0130\u0131\u0159\u015e\u015f\u0160\u0161'"~/!:,&#\-\.\?\*]+?)(?: /|\[|\()""",
                re.U | re.S,
            ).findall(find_str_org.replace(" / ", " // ")):
                if c:
                    c = c.strip()
                    if c and not c.isdigit():
                        scraper["search"] = c
                        scraper["info"]["originaltitle"] = c
                        break

        # компилируем имя
        name = "[COLOR FFEEEEEE][B]" + split[0] + "[/B][/COLOR]"
        if split[1]:
            name += " " + split[1]
        if split[2]:
            name += " [COLOR FFFFFFCC]" + split[2] + "[/COLOR]"
        if split[3]:
            name += " " + split[3]

        # запрос для поиска
        search = split[0]

        # пробуем вытащить дату
        r = self.RE["year"].search(split[2])
        if r:
            year = int(r.group(1))
        else:
            year = None

        scraper["notfind"] = True

        tmdb = self.tmdb.scraper_multi(scraper["search"], year, search, 1, only_tv)
        if not tmdb:
            return scraper
        # if year:
        #        if year != tmdb['info']['year']:
        #                                return scraper

        if mode > 0:  # если осутствует описание, то берем его с трекера
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            if tmdb["info"]["plot"] == "":
                if profile and profile["descript"]:
                    descript = (
                        profile["descript"]
                        .replace("[/COLOR]", "")
                        .replace("[COLOR FF0DA09E]", "")
                    )

                    r = re.compile(
                        r"(?:\wписание|О фильме|Рецензия.*?|Аннотация.*?|О спектакле):(.+?)(?:Доп. информация|Дополнительная информация|С\wмпл|Качество видео|Качество|Тип релиза|Video|Перевод|Релиз|Релиз группы|Информационные ссылки):",
                        re.U | re.S,
                    ).search(descript)
                    if r:
                        tmdb["info"]["plot"] = r.group(1).strip("\n")
                    else:
                        r = re.compile(r"\wписание:(.+?)$", re.U | re.S).search(
                            descript
                        )
                        if r:
                            tmdb["info"]["plot"] = r.group(1).strip("\n")
                        else:
                            r = re.compile(
                                r"(?:\wписание|ОПИСАНИЕ|Содержание:)(.+?)(?:Доп. информация|Качество видео|Качество|Тип релиза:)",
                                re.U | re.S,
                            ).search(descript)
                            if r:
                                tmdb["info"]["plot"] = r.group(1).strip("\n")

        # ХАК
        # добавляем runtime (длительность фильма) в описание (в скинах не видно)
        if "runtime" in tmdb and tmdb["runtime"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n\n",
                    self.lang[40102],
                    ": [B]",
                    str(tmdb["runtime"]),
                    "[/B] ",
                    self.lang[40103],
                ]
            )
        if "budget" in tmdb and tmdb["budget"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n",
                    self.lang[40104],
                    ": [B]",
                    str(tmdb["budget"]),
                    "[/B] $",
                ]
            )
        if "revenue" in tmdb and tmdb["revenue"]:
            if "plot" not in tmdb["info"]:
                tmdb["info"]["plot"] = ""
            tmdb["info"]["plot"] = "".join(
                [
                    tmdb["info"]["plot"],
                    "\n",
                    self.lang[40105],
                    "   : [B]",
                    str(tmdb["revenue"]),
                    "[/B] $",
                ]
            )
        # ХАК

        scraper["title"] = name
        scraper["fanart"] = tmdb["fanart"]
        scraper["thumb"] = tmdb["thumb"]
        if tmdb.get("cast"):
            scraper["cast"] = tmdb["cast"]
        scraper["info"].update(tmdb["info"])
        scraper["id"] = tmdb["id"]
        if tmdb.get("m_type"):
            scraper["m_type"] = tmdb["m_type"]

        scraper["notfind"] = False
        try:  # проверка на 'китайское' название
            s = scraper["info"]["title"].encode("windows-1251")
        except:
            scraper["rutracker"] = True
            scraper["rt_year"] = year

        return scraper

    def scraper_default(self, item):
        return {
            "title": item["name"],
            "search": None,
            "subdir": item["name"],
            "icon": None,
            "thumb": None,
            "fanart": None,
            "popup": [],
            "bookmark": None,
            "cast": None,
            "info": {"size": item["size"], "title": item["name"]},
        }


# ########################
#
#   MENU
#
# ########################


class Menu(Handler):
    def handle(self):
        thumb = self.addon.getAddonInfo("icon")
        bookmark_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "bookmark.png"
        )
        about_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "video.png"
        )
        self.item(Link("menu-rutracker"), title="RuTracker", thumb=thumb)
        # self.item(Link('menu-kinopoisk'), title=u'Кинопоиск') # Не работает. Если надо - чините сами.
        self.item(Link("bookmark"), title="Закладки", thumb=bookmark_thumb)
        self.item(Link("about-plugin"), title="О дополнении...", thumb=about_thumb)


class MenuRutracker(Handler):
    def handle(self):
        thumb = self.addon.getAddonInfo("icon")
        bookmark_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "bookmark.png"
        )
        findall_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "findall.png"
        )
        movie_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "movie.png"
        )
        video_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "video.png"
        )
        audiobook_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "audiobook.png"
        )
        audio_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "audio.png"
        )
        newstoday_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "newstoday.png"
        )
        news3day_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "news3day.png"
        )
        history_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "history.png"
        )
        favorites_thumb = os.path.join(
            self.addon.getAddonInfo("path"), "resources", "media", "favorites.png"
        )
        self.item(
            Link("bookmark"),
            title="[COLOR pink][Закладки][/COLOR]",
            thumb=bookmark_thumb,
        )
        self.item(
            Link("favorites", {"content": "global"}),
            title="[Избранное на трекере]",
            thumb=favorites_thumb,
        )
        self.item(
            Link("rutracker-search", {"content": "global"}),
            title="[COLOR yellow][Поиск по разделам: Фильмы, Сериалы и Мультипликация][/COLOR]",
            thumb=findall_thumb,
        )
        self.item(
            Link("history"),
            title="[COLOR green][История поиска][/COLOR]",
            thumb=history_thumb,
        )
        self.item(
            Link(
                "rutracker-search-page", {"content": "global", "search": "", "days": 1}
            ),
            title="[COLOR FF0DA09E]["
            + self.lang[30117]
            + ": Фильмы, Сериалы и Мультипликация][/COLOR]",
            thumb=newstoday_thumb,
        )
        self.item(
            Link(
                "rutracker-search-page", {"content": "global", "search": "", "days": 3}
            ),
            title="[COLOR FF0DA09E][Новинки за 3 дня: Фильмы, Сериалы и Мультипликация][/COLOR]",
            thumb=news3day_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "movie"}),
            title="Фильмы",
            thumb=movie_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "series"}),
            title="Сериалы",
            thumb=movie_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "cartoon"}),
            title="Мультипликация",
            thumb=movie_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "documentary"}),
            title="Документалистика и юмор",
            thumb=video_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "sport"}),
            title="Спорт",
            thumb=video_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "training"}),
            title="Обучающее видео",
            thumb=video_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "audiobook"}),
            title="Аудиокниги",
            thumb=audiobook_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "avtomoto"}),
            title="Всё по авто и мото",
            thumb=video_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "music"}),
            title="Музыка",
            thumb=audio_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "popmusic"}),
            title="Популярная музыка",
            thumb=audio_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "jazmusic"}),
            title="Джазовая и Блюзовая музыка",
            thumb=audio_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "rockmusic"}),
            title="Рок-музыка",
            thumb=audio_thumb,
        )
        self.item(
            Link("rutracker-folder", {"content": "electromusic"}),
            title="Электронная музыка",
            thumb=audio_thumb,
        )
        self.item(
            Link("extendedinfo", {"run": True}),
            title="[COLOR lightgreen][Когда не знаешь что смотреть (запуск ExtendedInfo)][/COLOR]",
        )
        self.item(
            Link("about-plugin"),
            title="[COLOR orange][О дополнении...][/COLOR]",
            thumb=thumb,
        )


class MenuKinopoisk(Handler):
    def handle(self):
        self.item(Link("kinopoisk-best-query", {}), title="Лучшие")
        self.item(Link("kinopoisk-search", {}), title="Поиск")
        self.item(Link("kinopoisk-person", {}), title="Персоны")


# ########################
#
#   TRACKER
#
# ########################


class RutrackerBase(Handler, Scrapers):
    def __init__(self, gsetting=None, link=None, argv=None):
        super().__init__(gsetting, link, argv)
        self._rutracker = None

    @property
    def rutracker(self) -> RuTracker:
        if not self._rutracker:
            self._rutracker = RuTracker()
        return self._rutracker

    def render_rutracker(
        self,
        is_search: bool,
        folder: Optional[str],
        data: Union[Dict[str, Any], int, None],
        is_favorite=False,
        is_united_search=False,
    ):
        RE_SPACE = re.compile(r"\s{1,}", re.U)

        err = None
        if data is None:
            err = 30001
        elif data == 0:
            err = 30002

        if err:
            lang = self.lang[err].split("|")
            xbmcgui.Dialog().ok("RuTracker", mkStr(lang[0], lang[1]))
        else:

            rating_view = bool(self.setting["rutracker_rating"] == "true")
            status_view = bool(self.setting["rutracker_status"] == "true")
            fanart_view = bool(self.setting["rutracker_fanart"] == "true")
            update_screenshot = bool(
                self.setting["rutracker_update_screenshot"] == "true"
            )
            screenshot_on = bool(self.setting["rutracker_screenshot_on"] == "true")
            turbo_mode = bool(self.setting["rutracker_turbo"] == "true")
            turbo_with_cache = bool(self.setting["rutracker_turbo_wcache"] == "true")
            seeder_view = bool(self.setting["rutracker_seeder"] == "true")
            self.enable_progress = (
                False
                if is_united_search
                or (
                    turbo_mode
                    and not (
                        "tmdb" in CONTENT[self.argv["content"]]["scraper"]
                        or "tvdb" in CONTENT[self.argv["content"]]["scraper"]
                    )
                )
                else bool(self.setting["rutracker_progress"] == "true")
            )

            search_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "search.png"
            )
            forward_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "forward.png"
            )
            forward10_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "forward10.png"
            )
            forward50_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "forward50.png"
            )
            backwards_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "backwards.png"
            )
            backwards10_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "backwards10.png"
            )
            backwards50_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "backwards50.png"
            )
            newstoday_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "newstoday.png"
            )
            news3day_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "news3day.png"
            )
            mostseed_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "mostseed.png"
            )
            popular_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "popular.png"
            )
            backfind_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "backfind.png"
            )
            nextfind_thumb = os.path.join(
                self.addon.getAddonInfo("path"), "resources", "media", "nextfind.png"
            )

            if not isinstance(data, dict):
                return

            if not folder and not is_search:
                items = [
                    x
                    for x in data["data"]
                    if x["id"] in CONTENT[self.argv["content"]]["index"]
                ]
            else:
                items = [
                    x
                    for x in data["data"]
                    if x["type"] == "torrent"
                    or x["id"] not in CONTENT[self.argv["content"]]["ignore"]
                ]

            # подбиваем общее кол-во строк
            total = len(items)
            if data["pages"][1] and not is_search:
                total += 1
                if (data["pages"][1] - 9) > 0:
                    total += 1
                if (data["pages"][1] - 49) > 0:
                    total += 1
            if data["pages"][3] and not is_search:
                total += 1
                if (data["pages"][3] + 9) <= data["pages"][0]:
                    total += 1
                if (data["pages"][3] + 49) <= data["pages"][0]:
                    total += 1
            if is_search:
                if data["pages"][1] and data["search_id"]:
                    total += 1
                if data["pages"][3] and data["search_id"]:
                    total += 1

            # меню для поиска (только на первой странице в категории)
            if not folder and not is_search:
                total += 3
                self.item(
                    Link("rutracker-search", {"content": self.argv["content"]}),
                    title="[COLOR FF0DA09E][B][" + self.lang[30114] + "][/B][/COLOR]",
                    thumb=search_thumb,
                    total=total,
                )
                self.item(
                    Link(
                        "rutracker-search-page",
                        {"content": self.argv["content"], "search": "", "days": 1},
                    ),
                    title="[COLOR FF0DA09E][B][" + self.lang[30117] + "][/B][/COLOR]",
                    thumb=newstoday_thumb,
                    total=total,
                )
                self.item(
                    Link(
                        "rutracker-search-page",
                        {"content": self.argv["content"], "search": "", "days": 3},
                    ),
                    title="[COLOR FF0DA09E][B][" + self.lang[30118] + "][/B][/COLOR]",
                    thumb=news3day_thumb,
                    total=total,
                )

            if folder and not is_search and (data["pages"][2] == 1):
                for item in items:
                    if item["type"] == "folder":
                        total_inc = 2
                    else:
                        total_inc = 4
                        break
                total += total_inc
                self.item(
                    Link(
                        "rutracker-search-page",
                        {
                            "content": self.argv["content"],
                            "index": self.argv["id"],
                            "search": "",
                            "days": 1,
                        },
                    ),
                    title="[COLOR FF0DA09E][B][" + self.lang[30117] + "][/B][/COLOR]",
                    thumb=newstoday_thumb,
                    total=total,
                )
                self.item(
                    Link(
                        "rutracker-search-page",
                        {
                            "content": self.argv["content"],
                            "index": self.argv["id"],
                            "search": "",
                            "days": 3,
                        },
                    ),
                    title="[COLOR FF0DA09E][B][" + self.lang[30118] + "][/B][/COLOR]",
                    thumb=news3day_thumb,
                    total=total,
                )
                if total_inc == 4:
                    self.item(
                        Link(
                            "rutracker-search-page",
                            {
                                "content": self.argv["content"],
                                "folder": self.argv["id"],
                                "search": "",
                                "seeders": True,
                            },
                        ),
                        title="[COLOR FF0DA09E][B]["
                        + self.lang[30119]
                        + "][/B][/COLOR]",
                        thumb=mostseed_thumb,
                        total=total,
                    )
                    self.item(
                        Link(
                            "rutracker-search-page",
                            {
                                "content": self.argv["content"],
                                "folder": self.argv["id"],
                                "search": "",
                                "downloads": True,
                            },
                        ),
                        title="[COLOR FF0DA09E][B]["
                        + self.lang[30120]
                        + "][/B][/COLOR]",
                        thumb=popular_thumb,
                        total=total,
                    )

            # popup_page =[(Link('setting'), self.lang[40015])]
            popup_page = [(self.p_settings, self.lang[40015])]
            # перейти на страницу
            if (data["pages"][1] or data["pages"][3]) and not is_search:
                popup_page.append(
                    (
                        Link(
                            "rutracker-gopage",
                            {
                                "content": self.argv["content"],
                                "id": self.argv["id"],
                                "page": data["pages"][2],
                                "maxpage": data["pages"][0],
                            },
                            True,
                        ),
                        self.lang[40018],
                    )
                )
                popup_page.reverse()
            if (data["pages"][1] or data["pages"][3]) and is_search:
                popup_page.append(
                    (
                        Link(
                            "rutracker-search-page",
                            {
                                "content": self.argv["content"],
                                "search_id": data["search_id"],
                                "search": data["search"],
                                "page": data["pages"][2],
                                "maxpage": data["pages"][0],
                            },
                            True,
                        ),
                        self.lang[40018],
                    )
                )
                popup_page.reverse()

            # верхний паджинатор
            if is_search and data["pages"][1] and data["search_id"]:
                self.item(
                    Link(
                        "rutracker-search-page",
                        {
                            "content": self.argv["content"],
                            "search_id": data["search_id"],
                            "search": data["search"],
                            "page": data["pages"][1],
                        },
                    ),
                    title="[COLOR FFE84C3D][B]["
                    + self.lang[30101]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][1])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=backfind_thumb,
                    total=total,
                )

            if data["pages"][1] and not is_search:
                self.item(
                    Link(
                        "rutracker-folder",
                        {
                            "content": self.argv["content"],
                            "id": self.argv["id"],
                            "page": data["pages"][1],
                        },
                    ),
                    title="[COLOR FF0DA09E][B]["
                    + self.lang[30101]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][1])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=backwards_thumb,
                    total=total,
                )
                if (data["pages"][2] - 10) > 0:
                    self.item(
                        Link(
                            "rutracker-folder",
                            {
                                "content": self.argv["content"],
                                "id": self.argv["id"],
                                "page": data["pages"][1] - 9,
                            },
                        ),
                        title=" [COLOR FF0DA09E][B]["
                        + self.lang[30101]
                        + " 10][/B][/COLOR] - ["
                        + str(data["pages"][1] - 9)
                        + "/"
                        + str(data["pages"][0])
                        + "]",
                        popup=popup_page,
                        popup_replace=True,
                        thumb=backwards10_thumb,
                        total=total,
                    )
                if (data["pages"][2] - 50) > 0:
                    self.item(
                        Link(
                            "rutracker-folder",
                            {
                                "content": self.argv["content"],
                                "id": self.argv["id"],
                                "page": data["pages"][1] - 49,
                            },
                        ),
                        title="  [COLOR FF0DA09E][B]["
                        + self.lang[30101]
                        + " 50][/B][/COLOR] - ["
                        + str(data["pages"][1] - 49)
                        + "/"
                        + str(data["pages"][0])
                        + "]",
                        popup=popup_page,
                        popup_replace=True,
                        thumb=backwards50_thumb,
                        total=total,
                    )

            self.show_progress("RuTracker", self.lang[40803])
            i = 0
            ilen = len(items)
            for item in items:
                i += 1
                if item["type"] == "folder":
                    self.item(
                        Link(
                            "rutracker-folder",
                            {"content": self.argv["content"], "id": item["id"]},
                        ),
                        title=item["name"],
                        popup=[
                            (
                                Link(
                                    "force-cache",
                                    {"content": self.argv["content"], "id": item["id"]},
                                ),
                                self.lang[40030],
                            )
                        ],
                        total=total,
                    )
                else:

                    #
                    self.update_progress(
                        i * 100 / ilen,
                        mkStr(
                            self.lang[40804] + ": " + str(i) + " / " + str(ilen),
                            item["name"],
                        ),
                    )
                    #
                    if self.iscanceled_progress():
                        break
                    # раздача

                    if turbo_mode:
                        if turbo_with_cache:
                            profile = self.rutracker.profile(item["id"], onlycache=True)
                        else:
                            profile = {
                                "descript": None,
                                "cover": None,
                                "screenshot": None,
                            }
                    else:
                        # получаем инфу по скриншотам, коверу и описанию
                        profile = self.rutracker.profile(
                            item["id"], screens=screenshot_on
                        )

                        if update_screenshot:
                            if profile["screenshot"] is None:
                                profile = self.rutracker.profile(item["id"], True, True)

                    # общий для всех popup (Info)
                    # popup = [(Link('info'), self.lang[40001])]
                    popup = [(self.p_info, self.lang[40001])]

                    if profile and profile["descript"]:
                        popup.append(
                            (Link("descript", profile["descript"]), self.lang[40002])
                        )
                    elif turbo_mode:
                        popup.append(
                            (Link("descript", {"id": item["id"]}), self.lang[40002])
                        )

                    # получаем данные из скрапера
                    scraper = self.scraper(
                        CONTENT[self.argv["content"]]["scraper"], item, profile
                    )

                    #
                    content = self.argv["content"]
                    if content == "global":
                        content = scraper["content"]
                    # расширенная информация из дополнения ExtendedInfo Script
                    year = None
                    if scraper["info"].get("year"):
                        year = scraper["info"]["year"]
                    if (
                        content == "movie"
                        or content == "cartoon"
                        or content == "series"
                    ):
                        popup.append(
                            (
                                Link(
                                    "extendedinfo",
                                    {
                                        "content": content,
                                        "name": scraper["search"],
                                        "year": year,
                                        "item_name": item["name"],
                                    },
                                ),
                                self.lang[40013],
                            )
                        )

                    # если фанарт выключен принудительно, то отключаем его
                    if not fanart_view:
                        scraper["fanart"] = None

                    name_ru = scraper["subdir"]  # для обновления в кэше

                    # чистим название файла для поддиректории
                    for char in '\\/:*?"<>|':
                        scraper["subdir"] = scraper["subdir"].replace(char, " ")
                    scraper["subdir"] = (
                        RE_SPACE.sub(" ", scraper["subdir"]).strip().replace(" ", ".")
                    )

                    # если в скрапере были доп. попапы, то добавляем их
                    popup.extend(scraper["popup"])

                    # если в скрапере нет обложки, то добавляем с трэкера
                    if not scraper["thumb"] and profile and profile["cover"]:
                        scraper["thumb"] = profile["cover"]

                    # если в скрапере нет обоев (фанарта), то добавляем с трэкера 1-й скриншот
                    if fanart_view:
                        if not scraper["fanart"] and profile and profile["screenshot"]:
                            scraper["fanart"] = profile["screenshot"][0]  # type: ignore

                    # добиваем стандартные для всех попапы

                    if turbo_mode and not (profile and profile["cover"]):
                        popup.append(
                            (Link("afisha", {"id": item["id"]}), self.lang[40040])
                        )

                    # скриншоты (для видео)
                    if profile and profile["screenshot"]:
                        popup.append(
                            (
                                Link("screenshot", profile["screenshot"]),
                                self.lang[40003] + " (" + str(len(profile["screenshot"])) + ")",  # type: ignore
                            )
                        )
                    elif turbo_mode or not screenshot_on:
                        popup.append(
                            (
                                Link(
                                    "screenshot",
                                    {
                                        "id": item["id"],
                                        "tm": turbo_mode,
                                        "twc": turbo_with_cache,
                                        "son": screenshot_on,
                                    },
                                ),
                                self.lang[40003],
                            )
                        )

                    # комментарии с раздачи
                    if item["comment"] == -1:
                        popup.append(
                            (Link("comment", {"id": item["id"]}), self.lang[40004])
                        )
                    elif item["comment"]:
                        popup.append(
                            (
                                Link("comment", {"id": item["id"]}),
                                self.lang[40004] + " (" + str(item["comment"]) + ")",
                            )
                        )

                    # статус раздачи
                    popup.append(
                        (
                            Link(
                                "status",
                                {
                                    "seeder": item["seeder"],
                                    "leecher": item["leecher"],
                                    "download": item["download"],
                                    "comment": item["comment"],
                                    "status": item["status"],
                                    "status_human": item["status_human"],
                                },
                            ),
                            self.lang[40005]
                            + " ("
                            + str(item["seeder"])
                            + "/"
                            + str(item["leecher"])
                            + ")",
                        )
                    )

                    fsm = False
                    if is_favorite and (content != "global"):
                        fsm = True
                    if not is_favorite or fsm:
                        # поиск по разделу по имени
                        popup.append(
                            (
                                Link(
                                    "rutracker-search",
                                    {
                                        "content": self.argv["content"],
                                        "textsearch": item["name"],
                                    },
                                    True,
                                ),
                                self.lang[30114],
                            )
                        )

                        # поиск похожих раздач
                        if scraper["search"]:
                            popup.append(
                                (
                                    Link(
                                        "rutracker-search",
                                        {
                                            "content": self.argv["content"],
                                            "search": scraper["search"],
                                        },
                                        True,
                                    ),
                                    self.lang[40006],
                                )
                            )

                        # закладки
                        if scraper["bookmark"]:
                            popup.append(
                                (
                                    Link(
                                        "bookmark-add",
                                        {
                                            "scrapper": scraper["bookmark"][0],
                                            "id": scraper["bookmark"][1],
                                            "datascraper": scraper,
                                        },
                                    ),
                                    self.lang[40009],
                                )
                            )

                    if not is_favorite:
                        forum_id = folder
                        if not folder:
                            forum_id = item["f_id"]
                        popup.append(
                            (
                                Link(
                                    "favorites-add",
                                    {"forum_id": forum_id, "topic_id": item["id"]},
                                ),
                                self.lang[40036],
                            )
                        )
                    else:
                        popup.append(
                            (
                                Link(
                                    "favorites-del",
                                    {
                                        "form_token": data["form_token"],
                                        "topic_id": item["id"],
                                    },
                                ),
                                self.lang[40037],
                            )
                        )

                    # обновить описание в кэше
                    popup.append(
                        (
                            Link(
                                "update-description",
                                {
                                    "id": item["id"],
                                    "scraper": CONTENT[self.argv["content"]]["scraper"],
                                    "name": scraper["search"],
                                    "year": year,
                                    "name_ru": name_ru,
                                    "item_name": item["name"],
                                    "tvdbname": scraper.get("tvdbsearch"),
                                },
                            ),
                            self.lang[40014],
                        )
                    )

                    # перейти на страницу
                    if (data["pages"][1] or data["pages"][3]) and not is_search:
                        popup.append(
                            (
                                Link(
                                    "rutracker-gopage",
                                    {
                                        "content": self.argv["content"],
                                        "id": self.argv["id"],
                                        "page": data["pages"][2],
                                        "maxpage": data["pages"][0],
                                    },
                                    True,
                                ),
                                self.lang[40018],
                            )
                        )
                    if (data["pages"][1] or data["pages"][3]) and is_search:
                        popup.append(
                            (
                                Link(
                                    "rutracker-search-page",
                                    {
                                        "content": self.argv["content"],
                                        "search_id": data["search_id"],
                                        "search": data["search"],
                                        "page": data["pages"][2],
                                        "maxpage": data["pages"][0],
                                    },
                                    True,
                                ),
                                self.lang[40018],
                            )
                        )

                    popup.append(
                        (
                            Link(
                                "addtorrserverbase",
                                {
                                    "id": item["id"],
                                    "profile": profile,
                                    "scraper": scraper,
                                    "name": item["name"],
                                },
                            ),
                            self.lang[40041],
                        )
                    )
                    # настройки плагина
                    # popup.append( (Link('setting'), self.lang[40015]) )
                    popup.append((self.p_settings, self.lang[40015]))

                    title = scraper["title"]
                    # количество раздающих в наименовании
                    if seeder_view and item["seeder"]:
                        len_temp = len(str(item["seeder"]))  # выравниваем строку
                        if len_temp == 3:
                            seeder = "| [COLOR pink]%5d[/COLOR] | " % item["seeder"]
                        elif len_temp == 2:
                            seeder = "| [COLOR pink]%6d[/COLOR] | " % item["seeder"]
                        elif len_temp == 1:
                            seeder = "| [COLOR pink]%7d[/COLOR] | " % item["seeder"]
                        else:
                            seeder = "| [COLOR pink]%4d[/COLOR] | " % item["seeder"]
                        title = seeder + title

                    # выставляем статус в наименование
                    if status_view:
                        try:
                            STATUS[item["status_human"]]
                        except KeyError:
                            title = "    " + title
                        else:
                            title = (
                                "[COLOR "
                                + STATUS[item["status_human"]][1]
                                + "]"
                                + item["status"]
                                + "[/COLOR]  "
                                + title
                            )

                    # выставляем рейтинг в наименование
                    if rating_view and CONTENT[self.argv["content"]]["rating"]:
                        rating = CONTENT[self.argv["content"]]["rating"] % scraper[
                            "info"
                        ].get("rating", 0.0)
                        if rating == "0.0":
                            rating = "[COLOR 22FFFFFF]0.0[/COLOR]"
                        elif rating == "10.0":
                            rating = "[B]10[/B]"
                        title = rating + "  " + title

                    # scraper['info']['title'] = title
                    scraper["info"]["mediatype"] = "movie"  # fix android info
                    # вывод
                    self.item(
                        Link(
                            "download",
                            {
                                "id": item["id"],
                                "content": content,
                                "subdir": scraper["subdir"],
                                "icon": scraper["icon"],
                                "title": item["name"],
                            },
                        ),
                        title=title,
                        icon=scraper["icon"],
                        thumb=scraper["thumb"],
                        fanart=scraper["fanart"],
                        media=CONTENT[self.argv["content"]]["media"],
                        info=scraper["info"],
                        cast=scraper["cast"],
                        popup=popup,
                        popup_replace=True,
                        folder=False,
                        total=total,
                    )

            self.hide_progress()
            # вперед на 50 страниц
            if (data["pages"][2] + 50) <= data["pages"][0] and not is_search:
                self.item(
                    Link(
                        "rutracker-folder",
                        {
                            "content": self.argv["content"],
                            "id": self.argv["id"],
                            "page": data["pages"][3] + 49,
                        },
                    ),
                    title="  [COLOR FF0DA09E][B]["
                    + self.lang[30102]
                    + " 50][/B][/COLOR] - ["
                    + str(data["pages"][3] + 49)
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=forward50_thumb,
                    total=total,
                )
            # вперед на 10 страниц
            if (data["pages"][2] + 10) <= data["pages"][0] and not is_search:
                self.item(
                    Link(
                        "rutracker-folder",
                        {
                            "content": self.argv["content"],
                            "id": self.argv["id"],
                            "page": data["pages"][3] + 9,
                        },
                    ),
                    title=" [COLOR FF0DA09E][B]["
                    + self.lang[30102]
                    + " 10][/B][/COLOR] - ["
                    + str(data["pages"][3] + 9)
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=forward10_thumb,
                    total=total,
                )
            # нижний паджинатор
            if data["pages"][3] and not is_search:
                self.item(
                    Link(
                        "rutracker-folder",
                        {
                            "content": self.argv["content"],
                            "id": self.argv["id"],
                            "page": data["pages"][3],
                        },
                    ),
                    title="[COLOR FF0DA09E][B]["
                    + self.lang[30102]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][3])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=forward_thumb,
                    total=total,
                )
            if is_search and data["pages"][3] and data["search_id"]:
                self.item(
                    Link(
                        "rutracker-search-page",
                        {
                            "content": self.argv["content"],
                            "search_id": data["search_id"],
                            "search": data["search"],
                            "page": data["pages"][3],
                        },
                    ),
                    title="[COLOR FFE84C3D][B]["
                    + self.lang[30102]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][3])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=popup_page,
                    popup_replace=True,
                    thumb=nextfind_thumb,
                    total=total,
                )

        # финал
        replace = False
        if "page" in self.argv:
            replace = True
        # xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED,'%R/%I')
        # xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_SIZE,'%R/%I')
        # xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_DATE)
        self.render(replace=replace)
        self.setviewmode(self.setting["rutracker_view"])


class RutrackerFolder(RutrackerBase):
    def handle(self):
        folder = self.argv.get("id")
        self.render_rutracker(
            False, folder, self.rutracker.get(folder, self.argv.get("page", 1))
        )


class RutrackerGoPage(RutrackerBase):
    def handle(self):
        folder = self.argv.get("id")

        kb = xbmc.Keyboard(
            "",
            self.lang[30115]
            + str(self.argv["maxpage"])
            + self.lang[30116]
            + str(self.argv["page"]),
        )
        kb.doModal()
        if kb.isConfirmed():
            textin = kb.getText()
            if textin.isdigit():
                page = int(textin)
                if (
                    page > 0
                    and page <= self.argv["maxpage"]
                    and page != self.argv["page"]
                ):
                    self.render_rutracker(
                        False, folder, self.rutracker.get(folder, page)
                    )
        return True


class RutrackerSearch(RutrackerBase):
    def handle(self):
        content = self.argv["content"]
        search = self.argv.get("search")
        # kbs = None

        if not search:
            textsearch = self.argv.get("textsearch")
            if not textsearch:
                textsearch = ""
            kb = xbmc.Keyboard(textsearch, self.lang[30114])
            kb.doModal()
            if kb.isConfirmed():
                search = kb.getText()
                # kbs = True
                HistoryAdd(content, search)
        if not search:
            return True

        data = self.rutracker.search(
            search, index=CONTENT[content]["index"], ignore=CONTENT[content]["ignore"]
        )

        # not found
        if data and not data["data"]:
            if not self.argv.get("united_search"):
                xbmcgui.Dialog().ok("RuTracker", self.lang[30008])
            return True

        # if kbs: HistoryAdd(content,search)
        self.render_rutracker(
            True, None, data, is_united_search=self.argv.get("united_search", False)
        )


class RutrackerSearchPage(RutrackerBase):
    def handle(self):
        content = self.argv["content"]
        search = self.argv.get("search", "")
        search_id = self.argv.get("search_id")
        page = self.argv.get("page")
        days = self.argv.get("days")
        seeders = self.argv.get("seeders")
        downloads = self.argv.get("downloads")
        folder = self.argv.get("folder")
        maxpage = self.argv.get("maxpage")
        index = self.argv.get("index")

        if maxpage:
            kb = xbmc.Keyboard(
                "",
                self.lang[30115]
                + str(self.argv["maxpage"])
                + self.lang[30116]
                + str(self.argv["page"]),
            )
            kb.doModal()
            if kb.isConfirmed():
                textin = kb.getText()
                if textin.isdigit():
                    page = int(textin)
                    if (page <= 0) or (page > maxpage) or (page == self.argv["page"]):
                        return True

        if index:
            data = self.rutracker.search(
                search,
                index=index,
                ignore=CONTENT[content]["ignore"],
                search_id=search_id,
                page=page,
                days=days,
                seeders=seeders,
            )
        elif folder:
            data = self.rutracker.search(
                search,
                folder=folder,
                search_id=search_id,
                page=page,
                days=days,
                seeders=seeders,
                downloads=downloads,
            )
        else:
            data = self.rutracker.search(
                search,
                index=CONTENT[content]["index"],
                ignore=CONTENT[content]["ignore"],
                search_id=search_id,
                page=page,
                days=days,
                seeders=seeders,
            )

        # not found
        if data and not data["data"]:
            xbmcgui.Dialog().ok("RuTracker", self.lang[30008])
            return True

        self.render_rutracker(True, None, data)


class Favorites(RutrackerBase):
    def handle(self):
        data = self.rutracker.favorites_get()
        # пустое Избранное
        if data and not data["data"]:
            xbmcgui.Dialog().ok("RuTracker", self.lang[30037])
            return True

        self.render_rutracker(True, None, data, True)


class FavoritesAdd(Handler):
    def handle(self):
        forum_id = self.argv.get("forum_id")
        topic_id = self.argv.get("topic_id")
        self.rutracker = RuTracker()
        data = self.rutracker.favorites_add(forum_id, topic_id)
        if data:
            xbmcgui.Dialog().ok("RuTracker", self.lang[30038])
        return True


class FavoritesDel(Handler):
    def handle(self):
        form_token = self.argv.get("form_token")
        topic_id = self.argv.get("topic_id")
        self.rutracker = RuTracker()
        data = self.rutracker.favorites_del(form_token, topic_id)
        if data:
            xbmcgui.Dialog().ok("RuTracker", self.lang[30039])
        return True


# ##############
#
#   KINOPOISK
#
# ##############


class KinopoiskBase(Handler, TrailerParser):
    kinopoisk: KinoPoisk

    def render_kinopoisk(self, data):
        if data is None:
            lang = self.lang[30001].split("|")
            xbmcgui.Dialog().ok("Kinopoisk", mkStr(lang[0], lang[1]))
        elif not data["data"]:
            xbmcgui.Dialog().ok("Kinopoisk", self.lang[30008])
        else:

            rating_view = bool(self.setting["rutracker_rating"] == "true")
            fanart_view = bool(self.setting["rutracker_fanart"] == "true")

            total = len(data["data"])
            if data["pages"][1]:
                total += 1
            if data["pages"][3]:
                total += 1

            # верхний паджинатор
            if data["pages"][1] and self.link:
                self.argv["page"] = data["pages"][1]
                self.item(
                    Link(self.link, self.argv),
                    title="[COLOR FF0DA09E][B]["
                    + self.lang[30101]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][1])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=[(Link("setting"), self.lang[40015])],
                    popup_replace=True,
                    total=total,
                )

            for id in data["data"]:
                movie = self.kinopoisk.movie(id, None)
                if movie:

                    # общий для всех popup (Info)
                    popup = [(Link("info"), self.lang[40001])]

                    # трэйлеры
                    if movie["trailers"]:
                        label, trailer_list = self.trailer_parser(movie["trailers"])
                        popup.append((Link("trailer", trailer_list), label))

                    # рецензии
                    popup.append((Link("review", {"id": id}), self.lang[40007]))

                    # добавить в закладки
                    popup.append(
                        (
                            Link("bookmark-add", {"scrapper": "kinopoisk", "id": id}),
                            self.lang[40009],
                        )
                    )

                    # настройки плагина
                    popup.append((Link("setting"), self.lang[40015]))

                    # имя для поиска на RuTracker
                    search = movie["info"]["title"]
                    if movie["info"].get("originaltitle"):
                        search = movie["info"]["originaltitle"]

                    # если фанарт выключен принудительно, то отключаем его
                    if not fanart_view:
                        movie["fanart"] = None

                    # выставляем рейтинг в наименование
                    if rating_view:
                        rating = "%1.1f" % movie["info"].get("rating", 0.0)
                        if rating == "0.0":
                            rating = "[COLOR 22FFFFFF]0.0[/COLOR]"
                        elif rating == "10.0":
                            rating = "[B]10[/B]"
                        movie["info"]["title"] = rating + "  " + movie["info"]["title"]

                    # вывод
                    self.item(
                        Link(
                            "rutracker-search", {"content": "movie", "search": search}
                        ),
                        title=movie["info"]["title"],
                        thumb=movie["thumb"],
                        media="video",
                        info=movie["info"],
                        fanart=movie["fanart"],
                        popup=popup,
                        popup_replace=True,
                        total=total,
                    )

            # нижний паджинатор
            if data["pages"][3] and self.link:
                self.argv["page"] = data["pages"][3]
                self.item(
                    Link(self.link, self.argv),
                    title="[COLOR FF0DA09E][B]["
                    + self.lang[30102]
                    + "][/B][/COLOR] - ["
                    + str(data["pages"][3])
                    + "/"
                    + str(data["pages"][0])
                    + "]",
                    popup=[(Link("setting"), self.lang[40015])],
                    popup_replace=True,
                    total=total,
                )

            # финал
            replace = False
            if data["pages"][2] > 1:
                replace = True

            self.render(replace=replace)


class KinopoiskBestQuery(Handler):
    def handle(self):
        self.kinopoisk = KinoPoisk()

        genre_lang = {"all": self.lang[70301]}
        for tag, code in GENRE:
            genre_lang[tag] = self.lang[code]

        if self.argv.get("change"):

            # ввод жанра
            if self.argv["change"] == "genre":
                genre_list = ["[B]" + self.lang[80101] + "[/B]"]
                genre_list.extend([genre_lang[x[0]] for x in GENRE])
                sel = xbmcgui.Dialog()
                gnr = sel.select(self.lang[70202], genre_list)
                if gnr > -1:
                    if gnr == 0:
                        genre = "all"
                    else:
                        genre = GENRE[gnr - 1][0]
                    self.setting["kinopoisk_genre"] = genre

            # ввод даты
            if self.argv["change"] == "decade":
                decade_list = ["[B]" + self.lang[70301] + "[/B]"]
                for y in range(201, 188, -1):
                    decade_list.append(str(10 * y) + "-e")

                sel = xbmcgui.Dialog()
                d = sel.select(self.lang[70203], decade_list)
                if d > -1:
                    if d == 0:
                        self.setting["kinopoisk_decade"] = "0"
                    else:
                        self.setting["kinopoisk_decade"] = decade_list[d][0:4]

            # ввод рейтинга
            if self.argv["change"] == "rate":
                rate_list = ["[B]" + self.lang[70301] + "[/B]"]
                for r in range(10, 0, -1):
                    rate_list.append(str(r))

                sel = xbmcgui.Dialog()
                r = sel.select(self.lang[70204], rate_list)
                if r > -1:
                    if r == 0:
                        self.setting["kinopoisk_rate"] = "0"
                    else:
                        self.setting["kinopoisk_rate"] = rate_list[r]

            # ввод кол-ва оценок
            if self.argv["change"] == "votes":
                vot = xbmcgui.Dialog()
                v = vot.numeric(0, self.lang[70205])
                if v:
                    v = int(v)
                    if v < 100:
                        v = 100
                    self.setting["kinopoisk_votes"] = str(v)

            # ввод страны производства
            if self.argv["change"] == "country":
                countries = self.kinopoisk.countries()
                countries_list = ["[B]" + countries[0][1] + "[/B]"]
                countries_list.extend([x[1] for x in countries[1:]])
                sel = xbmcgui.Dialog()
                country = sel.select(self.lang[70208], countries_list)  # type: ignore
                if country > -1:
                    self.setting["kinopoisk_country"] = str(countries[country][0])

            # ввод mpaa
            if self.argv["change"] == "mpaa":
                mpaa_list = ["[B]" + self.lang[70301] + "[/B]"]
                mpaa_list.extend(MPAA)

                sel = xbmcgui.Dialog()
                m = sel.select(self.lang[70206], mpaa_list)
                if m > -1:
                    if m == 0:
                        self.setting["kinopoisk_mpaa"] = "all"
                    else:
                        self.setting["kinopoisk_mpaa"] = mpaa_list[m]

            # ввод DVD
            if self.argv["change"] == "dvd":
                sel = xbmcgui.Dialog()
                d = sel.select(self.lang[70207], [self.lang[70304], self.lang[70303]])
                if d > -1:
                    if d == 0:
                        self.setting["kinopoisk_dvd"] = "true"
                    else:
                        self.setting["kinopoisk_dvd"] = "false"

        # получение текущих параметров поиска
        genre = self.setting["kinopoisk_genre"]
        decade = int(self.setting["kinopoisk_decade"])
        rate = int(self.setting["kinopoisk_rate"])
        votes = int(self.setting["kinopoisk_votes"])
        country = int(self.setting["kinopoisk_country"])
        mpaa = self.setting["kinopoisk_mpaa"]
        dvd = bool(self.setting["kinopoisk_dvd"] == "true")

        # начинаем вывод

        # вывод жанра
        self.item(
            Link("kinopoisk-best-query", {"change": "genre"}),
            title=self.lang[70102] + ": [B]" + genre_lang[genre] + "[/B]",
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод даты
        decade_title = "[B]" + self.lang[70301] + "[/B]"
        if decade:
            decade_title = "[B]" + str(decade) + "[/B]-e"
        self.item(
            Link("kinopoisk-best-query", {"change": "decade"}),
            title=self.lang[70103] + ": " + decade_title,
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод рейтинга
        rate_title = "[B]" + self.lang[70301] + "[/B]"
        if rate:
            rate_title = self.lang[70302] + " [B]" + str(rate) + "[/B]"
        self.item(
            Link("kinopoisk-best-query", {"change": "rate"}),
            title=self.lang[70104] + ": " + rate_title,
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод кол-во оценок
        self.item(
            Link("kinopoisk-best-query", {"change": "votes"}),
            title=self.lang[70105]
            + ": "
            + self.lang[70302]
            + " [B]"
            + str(votes)
            + "[/B]",
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод страны производства
        self.item(
            Link("kinopoisk-best-query", {"change": "country"}),
            title=self.lang[70106]
            + ":  [B]"
            + self.kinopoisk.country(country, " ")
            + "[/B]",
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод MPAA
        self.item(
            Link("kinopoisk-best-query", {"change": "mpaa"}),
            title="MPAA: [B]" + (self.lang[70301] if mpaa == "all" else mpaa) + "[/B]",
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # вывод DVD
        self.item(
            Link("kinopoisk-best-query", {"change": "dvd"}),
            title="DVD: [B]" + (self.lang[70304] if dvd else self.lang[70303]) + "[/B]",
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # кнопка ПОИСК
        self.item(
            Link(
                "kinopoisk-best",
                {
                    "genre": genre,
                    "decade": decade,
                    "rate": rate,
                    "votes": votes,
                    "country": country,
                    "mpaa": mpaa,
                    "dvd": dvd,
                },
            ),
            title="".join(["[COLOR FF0DA09E][B][", self.lang[70110], "][/B][/COLOR]"]),
            popup=[(Link("setting"), self.lang[40015])],
            popup_replace=True,
        )

        # финал
        replace = False
        if self.argv.get("change"):
            replace = True

        self.render(replace=replace)


class KinopoiskBest(KinopoiskBase):
    def handle(self):
        self.argv["limit"] = int(self.setting["kinopoisk_limit"])
        if not self.argv["limit"]:
            self.argv["limit"] = 50

        if self.argv["genre"] == "all":
            self.argv["genre"] = None
        if self.argv["mpaa"] == "all":
            self.argv["mpaa"] = None

        self.kinopoisk = KinoPoisk()
        self.render_kinopoisk(self.kinopoisk.best(**self.argv))


class KinopoiskSearch(KinopoiskBase):
    def handle(self):
        kb = xbmc.Keyboard("", self.lang[70201])
        kb.doModal()
        if kb.isConfirmed():
            name = kb.getText()
            if name:
                self.kinopoisk = KinoPoisk()
                self.render_kinopoisk(self.kinopoisk.search(name))


class KinopoiskPerson(Handler):
    def handle(self):
        kb = xbmc.Keyboard("", self.lang[70401])
        kb.doModal()
        if kb.isConfirmed():
            name = kb.getText()
            if name:
                self.kinopoisk = KinoPoisk()

                data = self.kinopoisk.person(name)

                if data is None:
                    lang = self.lang[30001].split("|")
                    xbmcgui.Dialog().ok("Kinopoisk", mkStr(lang[0], lang[1]))
                elif not data["data"]:
                    xbmcgui.Dialog().ok("Kinopoisk", self.lang[30008])
                else:

                    for d in data["data"]:
                        title = "[B]" + d["name"] + "[/B]"
                        if d["originalname"] and d["year"]:
                            title += (
                                " / " + d["originalname"] + " (" + str(d["year"]) + ")"
                            )
                        elif d["originalname"]:
                            title += " / " + d["originalname"]
                        elif d["year"]:
                            title += " /  (" + str(d["year"]) + ")"

                        self.item(
                            Link("kinopoisk-work", {"id": d["id"]}),
                            title=title,
                            thumb=d["poster"],
                            popup=[(Link("setting"), self.lang[40015])],
                            popup_replace=True,
                        )


class KinopoiskWork(KinopoiskBase):
    def handle(self):
        self.kinopoisk = KinoPoisk()

        data = self.kinopoisk.work(self.argv["id"])

        if not data:
            xbmcgui.Dialog().ok("Kinopoisk", self.lang[30008])
        else:

            works = [x for x in WORK if x[0] in data]

            sel = xbmcgui.Dialog()
            work = sel.select(
                self.lang[70402],
                [x[1] + " (" + str(len(data[x[0]])) + ")" for x in works],
            )
            if work == -1:
                work = 0

            self.render_kinopoisk({"pages": (1, 0, 1, 0), "data": data[works[work][0]]})


################
#
#   ЗАКЛАДКИ
#
################
class BookmarkDB:
    def __init__(self, filename):
        self.filename = filename

        if not xbmcvfs.exists(self.filename):
            self._connect()
            self.cur.execute("pragma auto_vacuum=1")
            self.cur.execute(
                "create table bookmark(addtime integer, scrapper varchar(32), id varchar(32))"
            )
            self.cur.execute("create index time on bookmark(addtime desc)")
            self.db.commit()
            self._close()

    def get(self):
        self._connect()
        self.cur.execute("select scrapper,id from bookmark order by addtime desc")
        res = [{"scrapper": x[0], "id": x[1]} for x in self.cur.fetchall()]
        self._close()
        return res

    def add(self, scrapper, id):
        self.delete(scrapper, id)
        self._connect()
        self.cur.execute(
            "insert into bookmark(addtime,scrapper,id) values(?,?,?)",
            (int(time.time()), scrapper, str(id)),
        )
        self.db.commit()
        self._close()

    def delete(self, scrapper, id):
        self._connect()
        self.cur.execute(
            "delete from bookmark where scrapper=? and id=?", (scrapper, id)
        )
        self.db.commit()
        self._close()
        if "rutracker" in scrapper:
            rutrackerbookmark = Cache("rutracker_bookmark.db")
            rutrackerbookmark.delete("bookmarkid:" + str(id))

    def _connect(self):
        self.db = sqlite.connect(self.filename)
        self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()


class Bookmark(Handler, TrailerParser):
    def handle(self):
        bookmark = BookmarkDB(self.path("bookmark.db"))

        if "scrapper" in self.argv:
            bookmark.delete(self.argv["scrapper"], self.argv["id"])
            xbmcgui.Dialog().ok("RuTracker", self.lang[30021])

        tvdb = TvDb()
        tmdb = TmDb()
        kinopoisk = KinoPoisk()

        movie: Any = {}

        def zakview(type="movie", year=True, razd=True):
            # открыть раздачу сразу
            if razd:
                popup.append(
                    (
                        Link(
                            "download",
                            {
                                "id": int(d["id"]),
                                "content": type,
                                "subdir": movie["subdir"],
                                "icon": movie["icon"],
                                "title": movie["title"],
                            },
                        ),
                        self.lang[40011],
                    )
                )
            # удалить из закладок
            popup.append(
                (
                    Link("bookmark", {"scrapper": d["scrapper"], "id": d["id"]}),
                    self.lang[40010],
                    True,
                    True,
                )
            )

            # поиск
            popup.append(
                (
                    Link(
                        "rutracker-search",
                        {"content": type, "textsearch": movie["info"].get("title")},
                        True,
                    ),
                    self.lang[30114],
                )
            )
            # настройки плагина
            # popup.append( (Link('setting'), self.lang[40015]) )
            popup.append((self.p_settings, self.lang[40015]))

            # имя для поиска на RuTracker
            search = movie.get("search", "")
            if search == "":
                search = movie["info"]["title"]
                if movie["info"].get("originaltitle"):
                    try:  # проверяем на китайские названия
                        s = movie["info"]["originaltitle"].encode("windows-1251")
                    except:
                        pass
                    else:
                        search = movie["info"]["originaltitle"]
            if movie["info"].get("year") and year:
                if movie.get("rt_year"):
                    search = search + " " + str(movie["rt_year"])
                else:
                    search = search + " " + str(movie["info"]["year"])

            # если фанарт выключен принудительно, то отключаем его
            if not fanart_view:
                movie["fanart"] = None

            # выставляем рейтинг в наименование
            if rating_view:
                rating = "%1.1f" % movie["info"].get("rating", 0.0)
                if rating == "0.0":
                    rating = "[COLOR 22FFFFFF]0.0[/COLOR]"
                elif rating == "10.0":
                    rating = "[B]10[/B]"
                movie["info"]["title"] = rating + "  " + movie["info"]["title"]
            #
            cast = movie.get("cast", None)
            movie["info"]["mediatype"] = "movie"  # fix android info
            # вывод
            self.item(
                Link("rutracker-search", {"content": type, "search": search}),
                title=movie["info"]["title"],
                thumb=movie["thumb"],
                media="video",
                info=movie["info"],
                fanart=movie["fanart"],
                cast=cast,
                popup=popup,
                popup_replace=True,
                total=total,
            )
            return

        data = bookmark.get()
        if not data:
            xbmcgui.Dialog().ok("RuTracker", self.lang[30008])
            return True
        else:

            rating_view = bool(self.setting["rutracker_rating"] == "true")
            fanart_view = bool(self.setting["rutracker_fanart"] == "true")

            total = len(data)

            for d in data:

                # общий для всех popup (Info)
                # popup = [(Link('info'), self.lang[40001])]
                popup: List[Tuple] = [(self.p_info, self.lang[40001])]

                if d["scrapper"] == "tvdb":

                    movie = tvdb.movie(d["id"])
                    zakview("series", False, False)

                elif d["scrapper"] == "rutrackermovies":

                    movie = self.rutrackerinfo(d["id"])
                    zakview()

                elif d["scrapper"] == "rutrackerseries":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("series")

                elif d["scrapper"] == "rutrackercartoon":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("cartoon")

                elif d["scrapper"] == "rutrackerdocumentary":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("documentary")

                elif d["scrapper"] == "rutrackersport":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("sport")

                elif d["scrapper"] == "rutrackertraining":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("training")

                elif d["scrapper"] == "rutrackeraudiobook":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("audiobook")

                elif d["scrapper"] == "rutrackeravtomoto":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("avtomoto")

                elif d["scrapper"] == "rutrackermusic":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("music")

                elif d["scrapper"] == "rutrackerpopmusic":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("popmusic")

                elif d["scrapper"] == "rutrackerjazmusic":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("jazmusic")

                elif d["scrapper"] == "rutrackerrockmusic":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("rockmusic")

                elif d["scrapper"] == "rutrackerelectromusic":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("electromusic")

                elif d["scrapper"] == "rutrackerglobal":

                    movie = self.rutrackerinfo(d["id"])
                    zakview("global")

                elif d["scrapper"] == "tmdb_movie":

                    movie = tmdb.movie(int(d["id"]))
                    zakview(razd=False)

                elif (
                    d["scrapper"] == "tmdb_series" or d["scrapper"] == "tmdb_series_tv"
                ):

                    if d["scrapper"] == "tmdb_series":
                        movie = tmdb.movie(int(d["id"]))
                    if d["scrapper"] == "tmdb_series_tv":
                        movie = tmdb.tv(int(d["id"]))

                    zakview("series", False, False)

                elif (
                    d["scrapper"] == "tmdb_cartoon"
                    or d["scrapper"] == "tmdb_cartoon_tv"
                ):

                    if d["scrapper"] == "tmdb_cartoon":
                        movie = tmdb.movie(int(d["id"]))
                    if d["scrapper"] == "tmdb_cartoon_tv":
                        movie = tmdb.tv(int(d["id"]))

                    zakview("cartoon", False, False)

                elif (
                    d["scrapper"] == "tmdb_global_movie"
                    or d["scrapper"] == "tmdb_global_tv"
                ):

                    if d["scrapper"] == "tmdb_global_movie":
                        movie = tmdb.movie(int(d["id"]))
                    if d["scrapper"] == "tmdb_global_tv":
                        movie = tmdb.tv(int(d["id"]))

                    zakview("global", False, False)

                elif d["scrapper"] == "kinopoisk":

                    movie = kinopoisk.movie(d["id"])

                    # трэйлеры
                    if movie and movie["trailers"]:
                        label, trailer_list = self.trailer_parser(movie["trailers"])
                        popup.append((Link("trailer", trailer_list), label))

                    # рецензии
                    popup.append((Link("review", {"id": d["id"]}), self.lang[40007]))
                    zakview(razd=False)

                else:
                    # TODO - для других скраперов
                    pass

    def rutrackerinfo(self, id):
        rutrackerbookmark = Cache("rutracker_bookmark.db")
        return rutrackerbookmark.get(
            "bookmarkid:" + str(id), False, self.addinfo, "notwork"
        )

    def addinfo(self, data):
        return False, data


class BookmarkAdd(Handler):
    def handle(self):
        BookmarkDB(self.path("bookmark.db")).add(self.argv["scrapper"], self.argv["id"])
        if self.argv["datascraper"].get("rutracker"):
            rutrackerbookmark = Cache("rutracker_bookmark.db")
            r = rutrackerbookmark.get(
                "bookmarkid:" + str(self.argv["id"]),
                False,
                self.addinfo,
                self.argv["datascraper"],
            )
        xbmcgui.Dialog().ok("RuTracker", self.lang[30020])
        return True

    def addinfo(self, data):
        return True, data


# ########################
#
#   ACTION
#
# ########################


class TorrentBase(Handler):
    def download(self):
        self.rutracker = RuTracker()
        torrent = self.rutracker.download(self.argv["id"])
        if torrent:
            return torrent
        xbmcgui.Dialog().ok("RuTracker", *self.lang[30001].split("|"))

    def get_magnet(self):
        self.rutracker = RuTracker()
        magnet = self.rutracker.magnet(self.argv["id"])
        if magnet:
            return magnet
        xbmcgui.Dialog().ok("RuTracker", *self.lang[30001].split("|"))

    def get_dirname(self, prefix) -> Tuple[bool, Optional[str]]:
        dirname = self.setting[prefix + "_dir"]
        if dirname and self.setting[prefix + "_save"] == "0":
            dirname = None

        if not dirname:
            dirname = xbmcgui.Dialog().browse(
                3,
                "RuTracker",
                CONTENT[self.argv["content"]]["media"],
                "",
                False,
                False,
                "",
            )
            dirname = str(dirname)

        return bool(self.setting[prefix + "_subdir"] == "true"), (
            dirname if dirname else None
        )

    def _mkdir(self, root, path):
        if not isinstance(path, list):
            path = [path]
        for subdir in path:
            root = os.path.join(root, subdir)
            try:
                os.mkdir(root)
                os.chmod(root, 0x777)
            except:
                pass
        return root

    def _clear(self, dirname):
        for filename in os.listdir(dirname):
            filename = os.path.join(dirname, filename)
            if os.path.isfile(filename):
                os.unlink(filename)
            else:
                self._clear(filename)
                os.rmdir(filename)

    def metainfo(self, torrent_data: bytes) -> Dict[bytes, Any]:
        from xbmcup.bencodepy import bdecode

        return bdecode(torrent_data)

    def infohash(self, torrent_data: bytes) -> str:
        from xbmcup.bencodepy import bencode
        import hashlib

        metainfo = self.metainfo(torrent_data)
        return hashlib.sha1(bencode(metainfo[b"info"])).hexdigest()


class Download(TorrentBase):
    def addon_chk(self, script_name):
        return xbmc.getCondVisibility("System.HasAddon(%s)" % script_name) == 1

    def _opentam(self):
        _log("start - opentam")
        if self.setting["tam_magnet"] == "true":
            magnet_link = self.get_magnet()
            if not magnet_link:
                return True
            magnet_link = magnet_link + "&tr=http://bt.t-ru.org/ann?magnet"
        else:
            torrent_data = self.download()
            if not torrent_data:
                return True
            torrent_path = self.path("tam")
            if not os.path.isdir(torrent_path):
                os.mkdir(torrent_path)
                os.chmod(torrent_path, 0x777)

            infohash = self.infohash(torrent_data)
            magnet_link = os.path.join(torrent_path, str(infohash) + ".torrent")
            if not os.path.isfile(magnet_link):
                file(magnet_link, "wb").write(torrent_data)

        fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
        if "http://" in fanart:
            pass
        elif "https://" in fanart:
            pass
        else:
            fanart = None
        info = {
            "cover": xbmc.getInfoLabel("ListItem.Art(thumb)"),
            "fanart": fanart,
            "icon": None,
            "title": xbmc.getInfoLabel("ListItem.Title"),
            "originaltitle": xbmc.getInfoLabel("ListItem.OriginalTitle"),
            "year": xbmc.getInfoLabel("ListItem.Year"),
            "premiered": xbmc.getInfoLabel("ListItem.Premiered").replace(".", "-"),
            "genre": xbmc.getInfoLabel("ListItem.Genre"),
            "director": xbmc.getInfoLabel("ListItem.Director"),
            "rating": xbmc.getInfoLabel("ListItem.Rating"),
            "votes": xbmc.getInfoLabel("ListItem.Votes").replace(",", ""),
            "mpaa": xbmc.getInfoLabel("ListItem.Mpaa"),
            "cast": xbmc.getInfoLabel("ListItem.Cast").split("\n"),
            "castandrole": [
                (i.split(" в роли "))
                for i in xbmc.getInfoLabel("ListItem.CastAndRole").split("\n")
                if i
            ],
            "studio": xbmc.getInfoLabel("ListItem.Studio"),
            "trailer": xbmc.getInfoLabel("ListItem.Trailer"),
            "writer": xbmc.getInfoLabel("ListItem.Writer"),
            "tagline": xbmc.getInfoLabel("ListItem.Tagline"),
            "plot": xbmc.getInfoLabel("ListItem.Plot"),
            "code": xbmc.getInfoLabel("ListItem.IMDBNumber"),
            "plotoutline": xbmc.getInfoLabel("ListItem.PlotOutline"),
            "mediatype": "movie",  # fix android info
        }
        infoout = {}
        for i in info:
            if info[i] and info[i] != [""]:
                if not (i == "votes" and info[i] == "0"):
                    if isinstance(info[i], str):
                        infoout[i] = info[i].replace("|", "#")  # fix bug in TAM
                    else:
                        infoout[i] = info[i]
        # handle = str(sys.argv[1])
        # purl =handle+",?mode=open&url="+ quote_plus(magnet_link) +"&info="+ quote_plus(repr(info))
        # xbmc.executebuiltin('RunScript(plugin.video.tam,%s)' % purl) # работает, не запускает TAM и остаемся в трекере
        purl = (
            "?mode=open&url="
            + quote_plus(magnet_link)
            + "&info="
            + quote_plus(repr(infoout))
        )
        # xbmc.executebuiltin('RunAddon(plugin.video.tam,%s)' % purl) # работает и запускает TAM, но выходит из трекера
        # if xbmc.getInfoLabel('System.BuildVersion')[:2] > '17':
        #        _log(' try - for Kodi 18 Leia')
        #        purl = "plugin://plugin.video.tam/" + purl
        #        self.item(UrlLink(purl), title=self.lang[40029], media=CONTENT[self.argv['content']]['media'],  folder=True, total=1)
        #        self.render()
        #        self.setviewmode(self.setting['rutracker_view'])
        # else:
        _log(
            'try - xbmc.executebuiltin("Container.Update(plugin://plugin.video.tam/%s"))'
            % purl
        )
        xbmc.executebuiltin("Container.Update(plugin://plugin.video.tam/%s)" % purl)
        _log("end - opentam")
        return True

    def handle(self):
        config = self.get_torrent_client()

        stream = None
        if CONTENT[self.argv["content"]]["stream"]:

            msg = []
            #
            if self.addon_chk("script.module.torrserver"):
                msg.append(("torrserver", self.lang[40028]))
            if self.addon_chk("plugin.video.elementum"):
                msg.append(("elementum", self.lang[40025]))
            if self.addon_chk("script.module.torrent2http"):
                msg.append(("torrent2http", self.lang[40034]))
            # Теперь работает через путь до торрент файла (по умолчанию) или magnet, зависит от настройки.
            if self.addon_chk("plugin.video.tam"):
                msg.append(("tam", self.lang[40026]))


            # Передать магнет в дополнение TAM (с возвратом)
            if self.addon_chk("plugin.video.tam"):
                msg.append(("opentam", self.lang[40029]))

            if config["client"] == "utorrent":
                msg.append(("utorrent", self.lang[40020]))
            elif config["client"] == "transmission":
                msg.append(("transmission", self.lang[40021]))
            elif config["client"] == "deluge":
                msg.append(("deluge", self.lang[40031]))
            elif config["client"] == "qbittorrent":
                msg.append(("qbittorrent", self.lang[40032]))
            elif config["client"] == "rtorrent":
                msg.append(("rtorrent", self.lang[40033]))

            p2p_option = (
                None,               # 50302
                "torrserver",       # 50150
                "elementum",        # 50151
                "tam",              # 50152
                #"torrenter",        # 50153
                #"libtorrent",       # 50154
                #"torrentstream",    # 50155
                #"delugestream",     # 50156
                "opentam",          # 50157
                "torrent2http",     # 50158
            )

            p2p_engine = p2p_option[int(self.setting["rutracker_p2p"])]
            if p2p_engine:
                avaible_p2p = [x[0] for x in msg]
                if p2p_engine in avaible_p2p:
                    stream = p2p_engine
                else:
                    xbmcgui.Dialog().ok(
                        "RuTracker",
                        "Выбранный в настройках торрент движок не установлен.",
                    )
                    return True
            else:
                dialog = xbmcgui.Dialog()
                index = dialog.select("RuTracker", [x[1] for x in msg])
                if index < 0:
                    return True
                else:
                    stream = msg[index][0]

        if stream in (
            "libtorrent",
            "torrentstream",
            "delugestream",
            "elementum",
            "torrenter",
            "torrserver",
            "tam",
            "torrent2http",
        ):
            self.argv["engine"] = stream
            self.run(Link("stream", self.argv))

        elif stream == "opentam":
            self._opentam()

        else:
            torrent = self.download()
            if torrent:

                subdir, rootdir = self.get_dirname("torrent")
                if not rootdir:
                    return True
                dirname = (
                    self._mkdir(rootdir, self.argv["subdir"]) if subdir else rootdir
                )

                from xbmcup.ctor import Torrent

                client = Torrent(
                    client=config["client"],
                    host=config["host"],
                    port=config["port"],
                    login=config["login"],
                    password=config["password"],
                    url=config["url"],
                )
                if client.add(torrent, dirname) is None:
                    if subdir:
                        dirname = os.path.join(rootdir, self.argv["subdir"][0])
                        self._clear(dirname)
                        os.rmdir(dirname)
                    xbmcgui.Dialog().ok("RuTracker", *self.lang[30014].split("|"))
                else:
                    cmd = None
                    if config["client"] == "utorrent":
                        msg = 30015
                        cmd = "plugin.program.utorrent"
                    elif config["client"] == "transmission":
                        msg = 30016
                        cmd = "script.transmission"
                    elif config["client"] == "deluge":
                        msg = 30035
                        cmd = "plugin.program.deluge"
                    elif config["client"] == "rtorrent":
                        msg = 30036
                        cmd = "plugin.program.rtorrent"

                    # if self.argv['bookmark']:
                    #    BookmarkDB(self.path('bookmark.db')).delete(self.argv['bookmark'][0], self.argv['bookmark'][1])
                    if cmd:
                        if xbmcgui.Dialog().yesno(
                            "RuTracker", *self.lang[msg].split("|")
                        ):
                            xbmc.executebuiltin("XBMC.RunAddon(" + cmd + ")")
                    else:
                        xbmcgui.Dialog().ok("RuTracker", *self.lang[30034].split("|"))

        return True

    def get_torrent_client(self):
        torrent = self.setting["torrent"]
        if torrent == "0":
            config = {
                "client": "utorrent",
                "host": self.setting["torrent_utorrent_host"],
                "port": self.setting["torrent_utorrent_port"],
                "url": "",
                "login": self.setting["torrent_utorrent_login"],
                "password": self.setting["torrent_utorrent_password"],
            }
        elif torrent == "1":
            config = {
                "client": "transmission",
                "host": self.setting["torrent_transmission_host"],
                "port": self.setting["torrent_transmission_port"],
                "url": self.setting["torrent_transmission_url"],
                "login": self.setting["torrent_transmission_login"],
                "password": self.setting["torrent_transmission_password"],
            }
        elif torrent == "2":
            config = {
                "client": "deluge",
                "host": self.setting["torrent_deluge_host"],
                "port": self.setting["torrent_deluge_port"],
                "url": self.setting["torrent_deluge_path"],
                "login": "",
                "password": self.setting["torrent_deluge_password"],
            }
        elif torrent == "3":
            config = {
                "client": "qbittorrent",
                "host": self.setting["torrent_qbittorrent_host"],
                "port": self.setting["torrent_qbittorrent_port"],
                "url": "",
                "login": self.setting["torrent_qbittorrent_login"],
                "password": self.setting["torrent_qbittorrent_password"],
            }
        elif torrent == "4":
            config = {
                "client": "rtorrent",
                "host": self.setting["torrent_rtorrent_host"],
                "port": self.setting["torrent_rtorrent_port"],
                "url": "",
                "login": "",
                "password": "",
            }
        return config


class Stream(TorrentBase):
    def handle(self):
        if self.argv["engine"] == "elementum":
            self._elementum()
        elif self.argv["engine"] == "torrenter":
            self._torrenter()
        elif self.argv["engine"] == "torrserver":
            self._torrserver()
        elif self.argv["engine"] == "tam":
            self._tam()
        elif self.argv["engine"] == "torrent2http":
            self._torrent2http()
        else:
            self._torrserver()

    def _torrenttomagnet(self, data):
        metainfo = self.metainfo(data)
        infohash = self.infohash(data)
        tr = [metainfo[b"announce"]]
        for t in metainfo[b"announce-list"]:
            tr.append(t.pop())

        params = {
            "dn": metainfo[b"info"][b"name"],
            "tr": tr,
        }
        magneturi = "magnet:?xt=urn:btih:{0}&{1}".format(
            str(infohash).upper(), urlencode(params, True)
        )
        return magneturi

    def _files(
        self,
        torrent,
        reverse=False,
        sortfile=False,
        pathfile=False,
        sortpath=False,
        onlyvideo=False,
        onlyaudio=False,
    ):
        from xbmcup.bencodepy import bdecode

        try:
            info: Dict[bytes, Any] = bdecode(torrent)[b"info"]

        except bdecode.BTFailure as e:
            _log(e)

        else:
            def _decode(s) -> str:
                try:
                    return s.decode("utf8")
                except:
                    try:
                        return s.decode("cp1251")
                    except:
                        return s

            if b"files" in info:
                def get_path(parts: List[bytes]) -> List[str]:
                    strs = [ _decode(part) for part in parts ]
                    return strs

                def full_name(parts: List[bytes]) -> str:
                    strs = [ _decode(part) for part in parts ]
                    return os.sep.join(strs)

                if pathfile:
                    def file_item(i: int, x: Dict[bytes, Any]):
                        return dict(
                            id=i,
                            fullname=full_name(x[b"path"]),
                            path=get_path(x[b"path"]),
                            name=_decode(os.sep.join(x[b"path"])),
                            size=x[b"length"],
                        )

                    files = [ file_item(i, x) for i, x in enumerate(info[b"files"]) ]

                else:
                    def file_item2(i: int, x: Dict[bytes, Any]):
                        return dict(
                            id=i,
                            fullname=full_name(x[b"path"]),
                            path=get_path(x[b"path"]),
                            name=_decode(x[b"path"][-1]),
                            size=x[b"length"],
                        )
                    files = [ file_item2(i, x) for i, x in enumerate(info[b"files"]) ]

            else:
                files = [ dict(
                        id=0,
                        fullname=_decode(info[b"name"]),
                        path=[_decode(info[b"name"])],
                        name=_decode(info[b"name"]),
                        size=info[b"length"],
                ) ]

            if sortfile:
                from functools import cmp_to_key

                if sortpath:
                    files.sort(
                        key=cmp_to_key(
                            lambda f1, f2: cmp(f1["fullname"], f2["fullname"])
                        )
                    )
                else:
                    files.sort(
                        key=cmp_to_key(lambda f1, f2: cmp(f1["name"], f2["name"]))
                    )
            if reverse:
                files.reverse()

            file_ext = []
            if onlyvideo:
                video_file_ext = [
                    "3gp",
                    "avi",
                    "mkv",
                    "mp4",
                    "mov",
                    "wmv",
                    "m2ts",
                    "ts",
                    "divx",
                    "ogm",
                    "m4v",
                    "flv",
                    "m2v",
                    "mpeg",
                    "mpg",
                    "mts",
                    "vob",
                    "bdmv",
                ]
                file_ext.extend(video_file_ext)
            if onlyaudio:
                audio_file_ext = [
                    "mp3",
                    "flac",
                    "ape",
                    "ogg",
                    "ac3",
                    "dts",
                    "wma",
                    "wav",
                    "aac",
                    "mp2",
                    "mka",
                    "midi",
                    "aiff",
                    "it",
                    "s3m",
                    "mod",
                    "m4a",
                ]
                file_ext.extend(audio_file_ext)
            if onlyvideo or onlyaudio:
                files_temp = list()
                for i in files:
                    if i["name"].split(".")[-1].lower() in file_ext:  # type: ignore
                        files_temp.append(i)
                files = files_temp
            return files

    def _torrent2http(self):
        from xbmcup.etor import Torrent2http

        # проигрываем файл
        if "file_id" in self.argv:
            url_torrent = xbmcvfs.translatePath(
                "special://temp/plugin_rutracker_cache.torrent"
            )
            play = Torrent2http().play(
                torrent_file=url_torrent,
                file_id=int(self.argv["file_id"]),
                DDir=self.setting["torrent2http_dir_cache"],
            )
            return True

        # получаем список файлов из торрента
        else:
            torrent = self.download()
            if not torrent:
                return True

            # кэшируем торрент
            file(
                xbmcvfs.translatePath("special://temp/plugin_rutracker_cache.torrent"),
                "wb",
            ).write(torrent)

            filelist = self._files(
                torrent,
                bool(self.setting["torrent2http_reverse"] == "true"),
                bool(self.setting["torrent2http_sortabc"] == "true"),
                bool(self.setting["torrent2http_pathtor"] == "true"),
                bool(self.setting["torrent2http_sortpath"] == "true"),
                bool(self.setting["torrent2http_onlyvideo"] == "true"),
                bool(self.setting["torrent2http_onlyaudio"] == "true"),
            )

            if not filelist:
                return True

            total = len(filelist)

            fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
            thumb = xbmc.getInfoLabel("ListItem.Art(thumb)")
            icon = self.argv["icon"]
            title = self.argv["title"]
            subdir = self.argv["subdir"]
            del self.argv["icon"]
            del self.argv["title"]
            del self.argv["subdir"]

            for f in filelist:
                self.argv["file_id"] = f["id"]
                self.item(
                    Link("stream", self.argv),
                    title=f["name"],
                    media=CONTENT[self.argv["content"]]["media"],
                    info={"size": f["size"], "title": f["name"]},
                    popup=[(self.p_settings, self.lang[40015])],
                    icon=icon,
                    thumb=thumb,
                    fanart=fanart,
                    property=[("IsPlayable", "true")],
                    popup_replace=True,
                    folder=False,
                    total=total,
                )

            self.render()
            self.setviewmode(self.setting["rutracker_files_view"])
            # self.render(mode='full')

    def _torrserver(self):
        # проигрываем файл
        if "file_id" in self.argv:
            url_torrent = xbmcvfs.translatePath(
                "special://temp/plugin_rutracker_cache.torrent"
            )
            global torrserve_stream
            import torrserve_stream

            player = torrserve_stream.Player(
                path=url_torrent, index=int(self.argv["file_id"])
            )
            return True

        # получаем список файлов из торрента
        else:
            torrent = self.download()
            if not torrent:
                return True

            # кэшируем торрент
            file(
                xbmcvfs.translatePath("special://temp/plugin_rutracker_cache.torrent"),
                "wb",
            ).write(torrent)

            filelist = self._files(
                torrent,
                bool(self.setting["torrserver_reverse"] == "true"),
                bool(self.setting["torrserver_sortabc"] == "true"),
                bool(self.setting["torrserver_pathtor"] == "true"),
                bool(self.setting["torrserver_sortpath"] == "true"),
                bool(self.setting["torrserver_onlyvideo"] == "true"),
                bool(self.setting["torrserver_onlyaudio"] == "true"),
            )

            if not filelist:
                return True

            total = len(filelist)

            fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
            thumb = xbmc.getInfoLabel("ListItem.Art(thumb)")
            icon = self.argv["icon"]
            title = self.argv["title"]
            subdir = self.argv["subdir"]
            del self.argv["icon"]
            del self.argv["title"]
            del self.argv["subdir"]

            for f in filelist:
                self.argv["file_id"] = f["id"]
                self.argv["file_name"] = f["fullname"].replace(os.sep, "/")  # type: ignore
                self.item(
                    Link("stream", self.argv),
                    title=f["name"],
                    media=CONTENT[self.argv["content"]]["media"],
                    info={"size": f["size"], "title": f["name"]},
                    popup=[(self.p_settings, self.lang[40015])],
                    icon=icon,
                    thumb=thumb,
                    fanart=fanart,
                    property=[("IsPlayable", "true")],
                    popup_replace=True,
                    folder=False,
                    total=total,
                )

            self.render()
            self.setviewmode(self.setting["rutracker_files_view"])
            # self.render(mode='full')

    def _torrenter(self):
        # проигрываем файл
        if "file_id" in self.argv:
            url_torrent = xbmcvfs.translatePath(
                "special://temp/plugin_rutracker_cache.torrent"
            )
            # это тут не работает...
            purl = (
                "plugin://plugin.video.torrenter/?action=playSTRM&url="
                + quote_plus(url_torrent)
                + "&index="
                + str(int(self.argv["file_id"]))
            )
            item = xbmcgui.ListItem(path=purl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            # а вот так срабатывает
            # xbmc.Player().play(purl)
            return True

        # получаем список файлов из торрента
        else:
            torrent = self.download()
            if not torrent:
                return True

            # кэшируем торрент
            file(
                xbmcvfs.translatePath("special://temp/plugin_rutracker_cache.torrent"),
                "wb",
            ).write(torrent)

            filelist = self._files(
                torrent,
                bool(self.setting["torrenter_reverse"] == "true"),
                bool(self.setting["torrenter_sortabc"] == "true"),
                bool(self.setting["torrenter_pathtor"] == "true"),
                bool(self.setting["torrenter_sortpath"] == "true"),
                bool(self.setting["torrenter_onlyvideo"] == "true"),
                bool(self.setting["torrenter_onlyaudio"] == "true"),
            )

            if not filelist:
                return True

            total = len(filelist)

            fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
            thumb = xbmc.getInfoLabel("ListItem.Art(thumb)")
            icon = self.argv["icon"]
            title = self.argv["title"]
            subdir = self.argv["subdir"]
            del self.argv["icon"]
            del self.argv["title"]
            del self.argv["subdir"]

            for f in filelist:
                self.argv["file_id"] = f["id"]
                self.item(
                    Link("stream", self.argv),
                    title=f["name"],
                    media=CONTENT[self.argv["content"]]["media"],
                    info={"size": f["size"], "title": f["name"]},
                    popup=[(self.p_settings, self.lang[40015])],
                    icon=icon,
                    thumb=thumb,
                    fanart=fanart,
                    property=[("IsPlayable", "true")],
                    popup_replace=True,
                    folder=False,
                    total=total,
                )

            self.render()
            self.setviewmode(self.setting["rutracker_files_view"])
            # self.render(mode='full')

    def _tam(self):
        # проигрываем файл
        if "file_id" in self.argv:
            # magnet_link = self.get_magnet()
            # magnet_link = magnet_link+'&tr=http://bt.t-ru.org/ann?magnet'
            url_torrent = xbmcvfs.translatePath(
                "special://temp/plugin_rutracker_tam_cache.torrent"
            )
            if self.setting["tam_magnet"] == "true":
                magnet_link = self._torrenttomagnet(file(url_torrent, "rb").read())
            else:
                magnet_link = url_torrent.encode("utf8")
            # это тут не работает...
            purl = (
                "plugin://plugin.video.tam/?mode=play&url="
                + quote_plus(magnet_link)
                + "&ind="
                + str(self.argv["file_id"])
            )
            item = xbmcgui.ListItem(path=purl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            # а вот так срабатывает
            # xbmc.Player().play(purl)
            return True
        # получаем список файлов из торрента
        else:
            torrent = self.download()
            if not torrent:
                return True

            # кэшируем торрент
            file(
                xbmcvfs.translatePath(
                    "special://temp/plugin_rutracker_tam_cache.torrent"
                ),
                "wb",
            ).write(torrent)

            filelist = self._files(
                torrent,
                bool(self.setting["tam_reverse"] == "true"),
                bool(self.setting["tam_sortabc"] == "true"),
                bool(self.setting["tam_pathtor"] == "true"),
                bool(self.setting["tam_sortpath"] == "true"),
                bool(self.setting["tam_onlyvideo"] == "true"),
                bool(self.setting["tam_onlyaudio"] == "true"),
            )

            if not filelist:
                return True

            total = len(filelist)

            fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
            thumb = xbmc.getInfoLabel("ListItem.Art(thumb)")
            icon = self.argv["icon"]
            title = self.argv["title"]
            subdir = self.argv["subdir"]
            del self.argv["icon"]
            del self.argv["title"]
            del self.argv["subdir"]

            for f in filelist:
                self.argv["file_id"] = f["id"]
                self.item(
                    Link("stream", self.argv),
                    title=f["name"],
                    media=CONTENT[self.argv["content"]]["media"],
                    info={"size": f["size"], "title": f["name"]},
                    popup=[(self.p_settings, self.lang[40015])],
                    icon=icon,
                    thumb=thumb,
                    fanart=fanart,
                    property=[("IsPlayable", "true")],
                    popup_replace=True,
                    folder=False,
                    total=total,
                )

            self.render()
            self.setviewmode(self.setting["rutracker_files_view"])
            # self.render(mode='full')

    def _elementum(self):
        # проигрываем файл
        if "file_id" in self.argv:
            url_torrent = xbmcvfs.translatePath(
                "special://temp/plugin_rutracker_cache.torrent"
            )
            # это тут не работает...
            # возможно из-за предупреждения в этом плагине: Attempt to use invalid handle -1
            ver_els = xbmc.getInfoLabel("System.AddonVersion(plugin.video.elementum)")
            sindex = "&index="
            try:
                ver_el = eval(ver_els.replace(".", ","))
                if ver_el >= (0, 1, 52):
                    sindex = "&oindex="
            except BaseException as e:
                _log(e, "elementum ver check error")
            purl = (
                "plugin://plugin.video.elementum/play?uri="
                + quote_plus(url_torrent)
                + sindex
                + str(int(self.argv["file_id"]))
            )
            item = xbmcgui.ListItem(path=purl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            # а вот так срабатывает
            # xbmc.Player().play(purl)
            return True

        # получаем список файлов из торрента
        else:
            torrent = self.download()
            if not torrent:
                return True

            # кэшируем торрент
            file(
                xbmcvfs.translatePath("special://temp/plugin_rutracker_cache.torrent"),
                "wb",
            ).write(torrent)

            filelist = self._files(
                torrent,
                bool(self.setting["elementum_reverse"] == "true"),
                bool(self.setting["elementum_sortabc"] == "true"),
                bool(self.setting["elementum_pathtor"] == "true"),
                bool(self.setting["elementum_sortpath"] == "true"),
                bool(self.setting["elementum_onlyvideo"] == "true"),
                bool(self.setting["elementum_onlyaudio"] == "true"),
            )

            if not filelist:
                return True

            total = len(filelist)

            fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
            thumb = xbmc.getInfoLabel("ListItem.Art(thumb)")
            icon = self.argv["icon"]
            title = self.argv["title"]
            subdir = self.argv["subdir"]
            del self.argv["icon"]
            del self.argv["title"]
            del self.argv["subdir"]

            for f in filelist:
                self.argv["file_id"] = f["id"]
                self.item(
                    Link("stream", self.argv),
                    title=f["name"],
                    media=CONTENT[self.argv["content"]]["media"],
                    info={"size": f["size"], "title": f["name"]},
                    popup=[(self.p_settings, self.lang[40015])],
                    icon=icon,
                    thumb=thumb,
                    fanart=fanart,
                    property=[("IsPlayable", "true")],
                    popup_replace=True,
                    folder=False,
                    total=total,
                )

            self.render()
            self.setviewmode(self.setting["rutracker_files_view"])
            # self.render(mode='full')

    def _copy(self, filename, dirname):
        progress = xbmcgui.DialogProgress()
        progress.create("RuTracker")
        full = os.path.getsize(filename)
        message, fname, fullsize = (
            self.lang[30012],
            filename.split(os.sep)[-1].encode("utf8"),
            self._human(full).strip(),
        )
        lines = mkStr(
            message, "File: " + fname, "Size: " + self._human(0) + " / " + fullsize
        )
        progress.update(0, lines)

        load = 0
        ff = open(filename, "rb")
        ft = open(os.path.join(dirname, filename.split(os.sep)[-1]), "wb")

        loop = 0.0

        while True:
            buf = ff.read(8192)
            if not buf:
                break
            load += len(buf)
            ft.write(buf)

            if loop + 0.5 < time.time():
                lines = mkStr(
                    message,
                    "File: " + fname,
                    "Size: " + self._human(load) + " / " + fullsize,
                )
                progress.update(int(load / (full / 100)), lines)
                loop = time.time()

        progress.close()

        ff.close()
        ft.close()

    def _human(self, size):
        human = None
        for h, f in (
            ("KB", 1024),
            ("MB", 1024 * 1024),
            ("GB", 1024 * 1024 * 1024),
            ("TB", 1024 * 1024 * 1024 * 1024),
        ):
            if size / f > 0:
                human = h
                factor = f
            else:
                break
        if human is None:
            return ("%10.1f %s" % (size, "byte")).replace(".0", "")
        else:
            return "%10.2f %s" % (float(size) / float(factor), human)


class ForceCache(Handler, Scrapers):
    def handle(self):
        if xbmcgui.Dialog().yesno("RuTracker", *self.lang[30030].split("|")):

            rutracker = RuTracker()

            items = {}
            page = 1
            total = 1

            progress = xbmcgui.DialogProgress()
            progress.create("RuTracker")
            lines = mkStr(
                self.lang[40801],
                self.lang[40802] + ":   " + str(page) + " / " + str(total),
            )
            progress.update(0, lines)

            while True:

                data = rutracker.get(self.argv["id"], page)
                if not data:
                    break

                for item in [x for x in data["data"] if x["type"] == "torrent"]:
                    items[item["id"]] = item

                if not data["pages"][3]:
                    break
                page = data["pages"][3]
                total = data["pages"][0]

                lines = mkStr(
                    self.lang[40801],
                    self.lang[40802] + ":   " + str(page) + " / " + str(total),
                )
                progress.update(int(float(page) / (float(total) / 100.0)), lines)

                if progress.iscanceled():
                    progress.close()
                    return True

            progress.close()
            if progress.iscanceled():
                return True

            if items:
                total = len(items)
                i = 0

                progress = xbmcgui.DialogProgress()
                progress.create("RuTracker")

                for id, item in items.items():
                    i += 1
                    lines = mkStr(
                        self.lang[40803],
                        self.lang[40804] + ":   " + str(i) + " / " + str(total),
                    )
                    progress.update(int(float(i) / (float(total) / 100.0)), lines)

                    # кэшируем описание
                    profile_data = rutracker.profile(item["id"])
                    if not profile_data:
                        progress.close()
                        return True

                    # кэшируем скрапер
                    self.scraper(CONTENT[self.argv["content"]]["scraper"], item)

                    if progress.iscanceled():
                        progress.close()
                        return True

            progress.close()

            xbmcgui.Dialog().ok("RuTracker", *self.lang[30031].split("|"))

        return True


class Setting(Handler):
    def handle(self):
        self.setting.dialog()
        return True


class Info(Handler):
    def handle(self):
        xbmc.executebuiltin("Action(Info)")
        return True


class ExtendedInfo(Handler):
    tmdb = TmDb()

    def handle(self):
        # self.enable_hide_all = False
        tmdb = None
        params = None
        if not self.addon_chk("script.extendedinfo"):
            xbmcgui.Dialog().ok("RuTracker", *self.lang[30033].split("|"))
            return True
        self.show_busy()
        if self.argv.get("content") == "movie":
            tmdb = self.tmdb.search_movie(self.argv["name"], self.argv["year"])
        elif self.argv.get("content") == "series":
            item_name = self.argv["item_name"]
            onlytv = False
            r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item_name)
            if r:
                onlytv = True
            else:
                r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item_name)
                if r:
                    onlytv = True
            tmdb = self.tmdb.search_multi(
                self.argv["name"], self.argv["year"], year_delta=1, only_tv=onlytv
            )
        elif self.argv.get("content") == "cartoon":
            item_name = self.argv["item_name"]
            onlytv = False
            r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(item_name)
            if r:
                onlytv = True
            else:
                r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item_name)
                if r:
                    onlytv = True
            tmdb = self.tmdb.search_multi(
                self.argv["name"], self.argv["year"], year_delta=1, only_tv=onlytv
            )
        elif self.argv.get("run"):
            params = ""
        if tmdb:
            params = "info=extendedinfo,name=%s" % tmdb["info"]["title"]
            if tmdb.get("m_type"):
                if tmdb["m_type"] == "tv":
                    params = "info=extendedtvinfo,name=%s" % tmdb["info"]["title"]
            if self.argv["year"]:
                params += ",year=%s" % str(self.argv["year"])
            params += ",id=%s" % str(tmdb["id"])
        if params or params == "":
            self.hide_busy()
            xbmc.executebuiltin(
                "RunScript(script.extendedinfo,%s)" % self.encode_(params)
            )
        else:
            self.hide_busy()
            xbmcgui.Dialog().ok("RuTracker", self.lang[30008])

        return True

    def encode_(self, param):
        try:
            return str(param).encode("utf-8")
        except:
            return param

    def addon_chk(self, script_name):
        return xbmc.getCondVisibility("System.HasAddon(%s)" % script_name) == 1


class Trailer(Handler):
    def handle(self):
        dialog = xbmcgui.Dialog()
        index = dialog.select(self.lang[40101], [x[0] for x in self.argv])
        if index < 0:
            return True
        xbmc.Player().play(self.argv[index][1])
        return True


class UpdateDescription(Handler):
    def handle(self):
        self.enable_hide_all = False
        index = 0
        if "tmdb" in self.argv["scraper"]:
            dialog = xbmcgui.Dialog()
            index = dialog.select("RuTracker", [self.lang[40014], self.lang[40019]])
            if index < 0:
                return True
            if index == 1:
                self.show_busy()
                if "movie" in self.argv["scraper"]:
                    self.tmdb = TmDb()
                    tmdb = self.tmdb.scraper_movie(
                        self.argv["name"], self.argv["year"], True
                    )
                    # return True
                if "series" in self.argv["scraper"]:
                    item_name = self.argv["item_name"]
                    onlytv = False
                    r = re.compile(r"Сезон[\:]{0,1}[\s]{1,}([0-9]+)", re.U).search(
                        item_name
                    )
                    if r:
                        onlytv = True
                    else:
                        r = re.compile(r"(Серии[\:]{0,1})", re.U).search(item_name)
                        if r:
                            onlytv = True
                    self.tmdb = TmDb()
                    tmdb = self.tmdb.scraper_multi(
                        self.argv["name"],
                        self.argv["year"],
                        self.argv["name_ru"],
                        1,
                        onlytv,
                        update=True,
                    )

                if "cartoon" in self.argv["scraper"]:
                    self.tmdb = TmDb()
                    tmdb = self.tmdb.scraper_multi(
                        self.argv["name"],
                        self.argv["year"],
                        self.argv["name_ru"],
                        1,
                        update=True,
                    )
        elif "tvdb" in self.argv["scraper"]:
            dialog = xbmcgui.Dialog()
            index = dialog.select("RuTracker", [self.lang[40014], self.lang[40017]])
            if index < 0:
                return True
            if index == 1:
                self.show_busy()
                self.tvdb = TvDb()
                tvdb = self.tvdb.scraper(self.argv["tvdbname"], self.argv["year"], True)
        if index == 0:
            self.show_busy()
            self.rutracker = RuTracker()
            profile = self.rutracker.profile(self.argv["id"], True)

        xbmc.executebuiltin("Container.Refresh")
        return True


class Screenshot(Handler):
    def handle(self):
        # xbmc.executehttpapi('ClearSlideshow') Это уже не работает...
        # for url in self.argv:
        # xbmc.executehttpapi('AddToSlideshow(%s)' % url)
        # xbmc.executehttpapi('AddToSlideshow(%s)' % 'http://st-im.kinopoisk.ru/im/wallpaper/1/3/7/kinopoisk.ru-Stone-1372763--w--1280.jpg')
        if isinstance(self.argv, dict):
            id = self.argv.get("id")
            son = self.argv.get("son")
            tm = self.argv.get("tm")
            self.rutracker = RuTracker()
            update = False
            if not tm and not son:
                update = True
            profile = self.rutracker.profile(id, update)
            if not profile or not profile["screenshot"]:
                if profile is None:
                    code_msg = 30001
                elif not profile:
                    code_msg = 30002
                else:
                    code_msg = 30004
                xbmcgui.Dialog().ok("RuTracker", *self.lang[code_msg].split("|"))
                return True
            argv = profile["screenshot"]
            if tm and profile["cover"]:
                argv.append(profile["cover"])  # добавим афишу в конец
        else:
            argv = self.argv
        screenshot_view = int(self.setting["rutracker_screenshot_view"])
        if screenshot_view == 0:
            dialog = xbmcgui.Dialog()
            #
            #
            type_screen = self.lang[40003]
            if ("radikal.ru" in argv[0]) or ("fastpic.ru" in argv[0]):
                type_screen = "Preview"
            index = dialog.select(
                "RuTracker " + type_screen + ":", [str(i + 1) for i in range(len(argv))]
            )
            if index < 0:
                return True
            else:
                xbmc.executebuiltin("ShowPicture(%s)" % argv[index])
        elif screenshot_view == 1:
            if xbmc.getInfoLabel("System.BuildVersion")[:2] > "16":
                # xbmcgui.Dialog().ok('RuTracker', u'Режим слайд-шоу в Kodi 18 Leia пока не работает.\nПереключаю на режим по одному.' )
                # self.setting['rutracker_screenshot_view'] = '0'
                try:
                    from xbmcup import slideshow

                    slideshow.open(argv, 0)
                    return True
                except BaseException as e:
                    _log(e, "new slideshow error")
            # -- parameters
            url = [{"url": argv[i], "title": str(i + 1)} for i in range(len(argv))]
            from xbmcup.diafilms import Diafilm

            # -- initialize GUI
            # import xbmcaddon
            path = self.addon.getAddonInfo("path")

            ui = Diafilm("Diafilms.xml", path, "default", "720p")
            ui.Set_URL(url)

            # -- show images
            ui.doModal()
            del ui

            #
            #

        # xbmc.executebuiltin('SlideShow(,recursive,notrandom)')
        return True


class Afisha(Handler):
    def handle(self):
        id = self.argv.get("id")
        self.rutracker = RuTracker()
        profile = self.rutracker.profile(id)
        if not profile or not profile["cover"]:
            if profile is None:
                code_msg = 30001
            elif not profile:
                code_msg = 30002
            else:
                code_msg = 30040
            xbmcgui.Dialog().ok("RuTracker", *self.lang[code_msg].split("|"))
            return True
        argv = [profile["cover"]]
        Screenshot(argv=argv).handle()


class Status(Handler):
    def handle(self):
        download = self.argv["download"]
        if download == -1:
            download = "нет данных"
        else:
            download = str(download)
        line = (
            self.lang[40491]
            + ":  [B]"
            + str(self.argv["seeder"])
            + "[/B]    "
            + self.lang[40492]
            + ":  [B]"
            + str(self.argv["leecher"])
            + "[/B]    "
            + self.lang[40493]
            + ":  [B]"
            + download
            + "[/B]"
        )

        try:
            lang, color = STATUS[self.argv["status_human"]]
        except KeyError:
            xbmcgui.Dialog().ok(self.lang[40005], line)
        else:
            lines = mkStr(
                "[COLOR "
                + color
                + "]"
                + self.argv["status"]
                + "[/COLOR] "
                + self.lang[lang],
                "   " + line,
            )
            xbmcgui.Dialog().ok(self.lang[40005], lines)

        return True


class FlushCache(Handler):
    def handle(self):
        if self.argv["cache"] == 1:
            cache_name = "RuTracker"
        elif self.argv["cache"] == 2:
            cache_name = "TheMovieDB"
        elif self.argv["cache"] == 3:
            cache_name = "TVDB"
        else:
            cache_name = "KinoPoisk"
        if not xbmcgui.Dialog().yesno(cache_name, *self.lang[30041].split("|")):
            return True
        if self.argv["cache"] == 1:
            cache_name = "RuTracker"
            Cache("rutracker_catalog.db").flush()
            Cache("rutracker_profile.db").flush()
        elif self.argv["cache"] == 2:
            cache_name = "TheMovieDB"
            Cache("tmdb.db").flush()
        elif self.argv["cache"] == 3:
            cache_name = "TVDB"
            Cache("tvdb.db").flush()
        else:
            cache_name = "KinoPoisk"
            Cache("kinopoisk.db").flush()
        xbmcgui.Dialog().ok(cache_name, self.lang[30010])
        return True


#
class ClearCookies(Handler):
    def handle(self):
        dirname = xbmcvfs.translatePath("special://temp")
        for subdir in ("xbmcup", sys.argv[0].replace("plugin://", "").replace("/", "")):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)
        if self.argv["mode"] == 1:
            filename = os.path.join(dirname, "rutracker.moz")
            if not xbmcvfs.exists(filename):
                return True
            if not os.path.isfile(filename):
                return True
            os.unlink(filename)
            xbmcgui.Dialog().ok("RuTracker", self.lang[30032])
        if self.argv["mode"] == 2:
            t_dir = self.setting["torrent_dir"]
            kb = xbmc.Keyboard(t_dir, self.lang[50304])
            kb.doModal()
            if kb.isConfirmed():
                self.setting["torrent_dir"] = kb.getText()
        return True


class Descript(Handler):
    def handle(self):
        if isinstance(self.argv, dict):
            id = self.argv.get("id")
            self.rutracker = RuTracker()
            profile = self.rutracker.profile(id)
            if not profile or not profile["descript"]:
                if profile is None:
                    code_msg = 30001
                elif not profile:
                    code_msg = 30002
                else:
                    code_msg = 30003
                xbmcgui.Dialog().ok("RuTracker", *self.lang[code_msg].split("|"))
                return True
            argv = profile["descript"]
        else:
            argv = self.argv
        gui = GuiDescript("DialogTextViewer.xml", sys.argv[0], descript=argv)
        gui.doModal()
        del gui
        return True


class GuiDescript(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.descript = kwargs["descript"]
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        lang = Lang()
        self.getControl(1).setLabel(lang[40002])  # type: ignore
        self.getControl(5).setText(self.descript)  # type: ignore

    def onFocus(self, control):
        pass


class Comment(Handler):
    def handle(self):
        gui = GuiComment("DialogTextViewer.xml", sys.argv[0], id=self.argv["id"])
        gui.doModal()
        del gui
        return True


class GuiComment(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.id = kwargs["id"]
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self._lang = Lang()
        self.lang = {
            "comment": self._lang[40004],
            "page": self._lang[30103],
            "load": self._lang[30104],
            "usertime": self._lang[30111],
            "count": self._lang[30112],
            "location": self._lang[30113],
        }

        self.label = self.getControl(1)
        self.text = self.getControl(5)

        self.rutracker = RuTracker()
        self.comment = []
        self.page = 1
        self.page_total = None
        if self.load():
            self.cursor = 0
            self.render()

    def onFocus(self, control):
        pass

    def onAction(self, action):
        id = action.getId()
        if id == 1:
            self.left()
        elif id == 2:
            self.right()
        elif id in (9, 10, 92):
            self.close()

    def left(self):
        if not self.lock:
            if self.cursor > 0:
                self.cursor -= 1
                self.render()

    def right(self):
        if not self.lock:
            if self.cursor + 1 < len(self.comment):
                self.cursor += 1
                self.render()
            elif self.page_total is not None:

                if self.page < self.page_total:
                    self.page += 1
                    if self.load():
                        self.cursor += 1
                        self.render()
                    else:
                        self.page -= 1

    def load(self):
        self.lock = True
        self.label.setLabel(self.lang["comment"])  # type: ignore
        self.text.setText(self.lang["load"])  # type: ignore

        data = self.rutracker.comment(self.id, self.page)

        if not data or not data["comments"]:
            if data is None:
                code_msg = 30001
            elif not data:
                code_msg = 30002
            else:
                code_msg = 30005
            xbmcgui.Dialog().ok("RuTracker", *self._lang[code_msg].split("|"))

            if self.page_total is None:
                self.close()
                return False

            self.lock = False
            return False

        else:
            self.comment.extend(data["comments"])
            if self.page_total is None:
                self.page_total = data["pages"][0]

            self.lock = False
            return True

    def render(self):
        self.label.setLabel(self.lang["comment"] + ":  " + str(self.cursor + 1) + "/" + str(len(self.comment)) + "     " + self.lang["page"] + ":  " + str(self.page) + "/" + str(self.page_total))  # type: ignore

        msg = self.comment[self.cursor]
        text = ""

        if msg["time"]:
            text += msg["time"] + "\n"

        text += "[COLOR FF0DA09E][B]" + msg["nick"] + "[/B][/COLOR]"

        profile = []
        for tag, lang in (
            ("usertime", self.lang["usertime"]),
            ("count", self.lang["count"]),
            ("location", self.lang["location"]),
        ):
            if msg[tag]:
                profile.append(lang + ":  " + msg[tag])
        if profile:
            text += "   [ " + ",  ".join(profile) + " ]"

        text += "\n\n\n" + msg["message"].replace("[BR]", "\n").strip()

        self.text.setText(text)  # type: ignore


class Review(Handler):
    def handle(self):
        self.kinopoisk = KinoPoisk()
        stat = self.kinopoisk.review(self.argv["id"], "stat")

        if stat is None:
            xbmcgui.Dialog().ok("Kinopoisk", *self.lang[30001].split("|"))
        elif stat["all"] == 0:
            xbmcgui.Dialog().ok("Kinopoisk", self.lang[30009])
        else:

            self.langs = {
                "all": self.lang[90014],
                "good": self.lang[90011],
                "bad": self.lang[90012],
                "neutral": self.lang[90013],
            }

            menu = []
            for tag in ("good", "bad", "neutral", "all"):
                menu.append((tag, self.langs[tag] + " (" + str(stat[tag]) + ")"))

            sel = xbmcgui.Dialog()
            r = sel.select(self.lang[90001], [x[1] for x in menu])
            if r > -1:

                gui = GuiReview(
                    "DialogTextViewer.xml",
                    sys.argv[0],
                    id=self.argv["id"],
                    query=menu[r][0],
                )
                gui.doModal()
                del gui

        return True


class GuiReview(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.id = kwargs["id"]
        self.query = kwargs["query"]
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self._lang = Lang()
        self.lang = {
            "review": self._lang[40007],
            "load": self._lang[30105],
            "count": self._lang[30112],
        }

        self.label = self.getControl(1)
        self.text = self.getControl(5)

        self.kinopoisk = KinoPoisk()
        self.review = []
        if self.load():
            self.cursor = 0
            self.render()

    def onFocus(self, control):
        pass

    def onAction(self, action):
        id = action.getId()
        if id == 1:
            self.left()
        elif id == 2:
            self.right()
        elif id in (9, 10, 92):
            self.close()

    def left(self):
        if not self.lock:
            if self.cursor > 0:
                self.cursor -= 1
                self.render()

    def right(self):
        if not self.lock:
            if self.cursor + 1 < len(self.review):
                self.cursor += 1
                self.render()

    def load(self):
        self.lock = True
        self.label.setLabel(self.lang["review"])  # type: ignore
        self.text.setText(self.lang["load"])  # type: ignore

        data = self.kinopoisk.review(self.id, self.query)

        if not data:
            if data is None:
                err = 30001
            else:
                err = 30009
            xbmcgui.Dialog().ok("Kinopoisk", *self._lang[err].split("|"))
            return False

        self.review = data[:]
        self.lock = False
        return True

    def render(self):
        self.label.setLabel(self.lang["review"] + ":  " + str(self.cursor + 1) + "/" + str(len(self.review)))  # type: ignore

        msg = self.review[self.cursor]
        text = ""

        if msg["time"]:
            text += msg["time"] + "\n"

        text += "[COLOR FF0DA09E][B]" + msg["nick"] + "[/B][/COLOR]"

        if msg["count"]:
            text += "   [ " + self.lang["count"] + ":  " + str(msg["count"]) + " ]"

        text += "\n\n\n"

        if msg["title"]:
            text += "[COLOR FF0DA09E][B]" + msg["title"] + "[/B][/COLOR]\n\n"

        text += msg["review"].replace("\n", "\n\n").strip()

        self.text.setText(text)  # type: ignore


#
class AboutPlugin(Handler):
    def handle(self):
        path = self.addon.getAddonInfo("path")
        addon_xml_path = os.path.join(path, "addon.xml")
        readme_path = os.path.join(path, "readme.txt")
        addon_xml_text = open(addon_xml_path, "r").read()
        readme_text = open(readme_path, "r").read()
        text = readme_text
        r = re.compile("<news>(.*?)</news>", re.U | re.S).search(addon_xml_text)
        if r:
            v = re.compile(
                '"[ \n]*?version="(.*?)"[ \n]*?provider-name="', re.U | re.S
            ).search(addon_xml_text)
            if v:
                text = "".join(
                    [
                        "[COLOR gold][B]Что нового в версии ",
                        v.group(1),
                        " :[/B][/COLOR]\n",
                        r.group(1),
                        "\n[COLOR gray]__________________________________________________________________________________________________________________[/COLOR]\n",
                        text,
                    ]
                )
        gui = GuiAboutPlugin(
            "DialogTextViewer.xml", sys.argv[0], descript=text, title="О дополнении..."
        )
        gui.doModal()
        del gui
        return True


class GuiAboutPlugin(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.descript = kwargs["descript"]
        self.title = kwargs["title"]
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        lang = Lang()
        self.getControl(1).setLabel(self.title)  # type: ignore
        self.getControl(5).setText(self.descript)  # type: ignore

    def onFocus(self, control):
        pass


#


def main():
    # plugin = Plugin(Menu)
    plugin = Plugin(MenuRutracker)
    plugin.route("menu-rutracker", MenuRutracker)
    plugin.route("menu-kinopoisk", MenuKinopoisk)

    plugin.route("rutracker-folder", RutrackerFolder)
    plugin.route("rutracker-search", RutrackerSearch)
    plugin.route("rutracker-gopage", RutrackerGoPage)
    plugin.route("rutracker-search-page", RutrackerSearchPage)

    plugin.route("kinopoisk-best-query", KinopoiskBestQuery)
    plugin.route("kinopoisk-best", KinopoiskBest)
    plugin.route("kinopoisk-search", KinopoiskSearch)
    plugin.route("kinopoisk-person", KinopoiskPerson)
    plugin.route("kinopoisk-work", KinopoiskWork)

    plugin.route("bookmark", Bookmark)
    plugin.route("bookmark-add", BookmarkAdd)

    plugin.route("download", Download)
    plugin.route("stream", Stream)

    plugin.route("force-cache", ForceCache)
    plugin.route("setting", Setting)
    plugin.route("info", Info)
    plugin.route("trailer", Trailer)
    plugin.route("screenshot", Screenshot)
    plugin.route("status", Status)
    plugin.route("flush-cache", FlushCache)
    plugin.route("descript", Descript)
    plugin.route("comment", Comment)
    plugin.route("review", Review)
    plugin.route("update-description", UpdateDescription)
    plugin.route("clear-cookies", ClearCookies)
    plugin.route("extendedinfo", ExtendedInfo)
    plugin.route("about-plugin", AboutPlugin)

    plugin.route("history", History)
    plugin.route("history-searchin", HistorySearchIn)
    plugin.route("favorites", Favorites)
    plugin.route("favorites-add", FavoritesAdd)
    plugin.route("favorites-del", FavoritesDel)
    plugin.route("afisha", Afisha)
    plugin.route("addtorrserverbase", AddTorrserverBase)

    if _setting_["rutracker_wallpaper"] == "true":
        plugin.run(fanart=True)
    else:
        plugin.run()


if __name__ == "__main__":
    try:
        search_vars = sys.argv[2].split("?")
        search_vars = search_vars[-1].split("&")
        if "usearch=True" in search_vars:
            params = parse_qs(sys.argv[2].replace("?", ""))
            _log(params, "params=")
            united_search = {
                "route": "rutracker-search",
                "argv": {
                    "content": "global",
                    "search": params["keyword"][0],
                    "united_search": True,
                },
            }
            import json

            sys.argv[2] = "?" + quote_plus(json.dumps(united_search))
    except BaseException as e:
        _log(e)

    _log(f"RuTracker call: {sys.argv[0]}{sys.argv[2]}")

    main()

# pr.disable()
# pr.dump_stats('/home/osmc/rutracker_stats')

# collected = gc.collect()
# print('collected:',collected)
#  это не нужно, проверено в Kodi 17.6
# try: sys.modules.clear()
