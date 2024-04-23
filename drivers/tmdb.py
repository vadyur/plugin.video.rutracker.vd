# -*- coding: utf-8 -*-
from typing import Any
import urllib
import time
from . import tmdbsimple as TmDbS

from xbmcup.cache import Cache
from xbmcup import errors

#tmdbs.API_KEY = 'f090bb54758cabf231fb605d3e3e0468'
from urllib.parse import quote_plus

class TmDb:
    def __init__(self):
        self.cache = Cache('tmdb.db')
        self.tmdbs = TmDbS
        self.tmdbs.API_KEY = 'f090bb54758cabf231fb605d3e3e0468'


    def scraper_movie(self, name, year=None, update=False):
        scraper = self.search_movie(name, year, update)
        if not scraper:
                return None
        return self.movie(scraper['id'], update)


    def search_movie(self, name, year=None, update=False):
        try:
            tag = 'scrmovie:' + quote_plus(name.encode('utf8'))
        except:
            return None
        else:
            if year:
                tag += ':' + str(year)
            return self.cache.get(tag, update, self._search_movie, name, year)

    def movie(self, id, update=False):
        idstr = str(id)
        return self.cache.get('movie:'+idstr, update, self._movie, id)

    def scraper_multi(self, name, year=None, name_ru=None, year_delta=0, only_tv=False, update=False):
        scraper = self.search_multi(name, year, name_ru, year_delta, only_tv, update)
        if not scraper:
                return None
        if scraper['m_type'] == u'movie':
                return self.movie(scraper['id'], update)
        if scraper['m_type'] == u'tv':
                return self.tv(scraper['id'], update)
        return scraper

    def tv(self, id, update=False):
        idstr = str(id)
        return self.cache.get('tv:'+idstr, update, self._tv, id)

    def search_multi(self, name, year=None, name_ru=None, year_delta=0, only_tv=False, update=False):
        try:
            tag = 'scrmulti:' + quote_plus(name.encode('utf8'))
        except:
            return None
        else:
            if year:
                tag += ':' + str(year)
            if only_tv:
                tag += ':tv'
            return self.cache.get(tag, update, self._search_multi, name, year, name_ru, year_delta, only_tv)

    # Private

    def _tv(self, id):
        res = {
        'fanart': None,
        'thumb': None,
        'cast': None,
        'info' : {}
        }
        timeout = True #
        ident = self.tmdbs.TV(id)
        try:
                response_all = ident.info(language='ru', append_to_response='credits,videos,content_ratings')
        except BaseException as e:
                #errors.log(e)
                errors.log(e, u'ошибка tmdb (tv id:'+str(id)+') !!!')
                #timeout2 = 6*60*60
                return False, None #timeout2, None
        #print(response_all)
        #print(response_all['name'])
        response = response_all
        tempstr = ''
        for k in response['genres']:
                tempstr += k['name']+', '
        res['info']['genre'] = tempstr[0:-2]
        res['info']['studio'] = u''
        if response.get('networks'):
                tempstr = ''
                for k in response['networks']:
                        tempstr += k['name']+', '
                res['info']['tagline'] = tempstr[0:-2]
        tempstr = ''
        for k in response['production_companies']:
                tempstr += k['name']+', '
        separatorstr =u', '
        if res['info']['studio'] == u'': separatorstr = u''
        if tempstr != '': res['info']['studio'] = res['info']['studio']+separatorstr+tempstr[0:-2]
        #res['info']['tagline'] = response['tagline']
        res['info']['status'] = response['status']
        res['info']['title'] = response['name']
        res['info']['originaltitle'] = response['original_name']
        res['info']['plot'] = response['overview']
        res['info']['rating'] = response['vote_average']
        res['info']['votes'] = str(response['vote_count'])
        #if response['vote_count'] < 20: timeout = 60*24*60*60 #
        #if response['overview'] == u'': timeout = 60*24*60*60 #
        res['info']['premiered'] = response['first_air_date']
        year = None
        if res['info'].get('premiered'):
                year = int(response['first_air_date'].split('-')[0])
                res['info']['year'] = year
        #res['info']['code'] = response['imdb_id']
        if response.get('poster_path'):
                res['thumb'] = 'https://image.tmdb.org/t/p/w500'+response['poster_path']
        if response.get('backdrop_path'):
                res['fanart'] = 'https://image.tmdb.org/t/p/w780'+response['backdrop_path'] # original
        #res['info']['aired'] = response['last_air_date']
        res['last_air_date'] = response['last_air_date']
        res['runtime'] = response['episode_run_time']
        res['seasons'] = response['number_of_seasons']
        res['episodes'] = response['number_of_episodes']
        res['popularity'] = response['popularity']
        res['m_type'] = u'tv' # признак ТВ не удалять!!!
        res['id'] = response['id']
        #response = ident.credits()
        response = response_all['credits']
        #print(response)
        #res['info']['cast'] = [ i['name'] for i in response['cast'] if i]
        #res['info']['castandrole'] =[ (i['name'], i['character']) for i in response['cast'] if i]
        #res['cast'] = [ {'name': i['name'], 'role': i['character'], 'order': i['order'], 'thumbnail': 'https://image.tmdb.org/t/p/w185'+i['profile_path'] if i['profile_path'] else None} for i in response['cast'] if i]
        castfull = [] # оптимизация в один цикл
        cast = []
        castandrole = []
        for i in response['cast']:
                cast.append(i['name'])
                castandrole.append( (i['name'], i['character']) )
                castfull.append( {'name': i['name'], 'role': i['character'], 'order': i['order'], 'thumbnail': 'https://image.tmdb.org/t/p/w185'+i['profile_path'] if i['profile_path'] else None} )
        res['info']['cast'] = cast
        res['info']['castandrole'] = castandrole
        res['cast'] = castfull
        # w45, w185
        director = writer = ''
        for i in response['crew']:
                if i['job'] == u'Director': director += i['name']+u', '
                if i['job'] == u'Screenplay': writer += i['name']+u', '
                elif i['job'] == u'Writer': writer += i['name']+u', '
        res['info']['director'] = director[0:-2]
        res['info']['writer'] = writer[0:-2]
        #response = ident.videos(language='ru')
        response = response_all['videos']
        for i in response['results']:
                if i['type'] == u'Trailer':
                        if i['site'] == u'YouTube': res['info']['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % i['key']
        if not res['info'].get('trailer'):
                response = ident.videos()
                for i in response['results']:
                        if i['type'] == u'Trailer':
                                if i['site'] == u'YouTube': res['info']['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % i['key']
        #response = ident.releases()
        response = response_all['content_ratings']
        mpaa = u''
        for i in response['results']:
                if i['iso_3166_1'] == u'US' and mpaa == u'': mpaa = i['rating']
                if i['iso_3166_1'] == u'RU': mpaa = i['rating']
        if mpaa != u'': res['info']['mpaa'] = mpaa
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year >= time.gmtime(time.time()).tm_year:
            timeout = 14*24*60*60 # 2 weeks

        return timeout, res


    def _search_multi(self, name, year=None, name_ru=None, year_delta=0, only_tv=False):
        res = {
        'fanart': None,
        'thumb': None,
        'info' : {}
        }
        timeout = True #
        if name == u'':
            timeout= 14*24*60*60 #
            return timeout, None
        search: Any = self.tmdbs.Search()
        response = search.multi(query=name, language='ru', include_adult=True)
        if year: year = int(year)
        if search.results:
                if response['total_results'] == 1:
                        index = 0
                        i = search.results[index]
                        if i.get('name'):
                                name_f = i['name']
                                if i.get('first_air_date'): year_f = int(i['first_air_date'].split('-')[0])
                                else: year_f = 0
                        if i.get('title'):
                                name_f = i['title']
                                if i.get('release_date'): year_f = int(i['release_date'].split('-')[0])
                                else: year_f = 0
                        name_f_org = u''
                        if i.get('original_name'): name_f_org = i['original_name']
                        if i.get('original_title'): name_f_org = i['original_title']
                        if only_tv:
                                if i['media_type'] != u'tv':
                                                timeout = 14*24*60*60 #
                                                return timeout, None
                        if name_ru:
                                if name_ru == name:
                                        if name_f.lower() != name.lower():
                                                timeout = 14*24*60*60 #
                                                return timeout, None
                                        elif year:
                                                if i['media_type'] == u'tv':
                                                        ident = self.tmdbs.TV(i['id'])
                                                        response_all = ident.info()
                                                        if response_all.get('last_air_date'):
                                                                year_l = int(response_all['last_air_date'].split('-')[0])
                                                                if year < year_f or year > year_l:
                                                                        timeout = 14*24*60*60 #
                                                                        return timeout, None
                                                        elif abs(year-year_f) > year_delta:
                                                                timeout = 14*24*60*60 #
                                                                return timeout, None
                                                elif abs(year-year_f) > year_delta:
                                                        timeout = 14*24*60*60 #
                                                        return timeout, None
                        if year:
                                if i['media_type'] == u'movie':
                                        if abs(year-year_f) > year_delta:
                                                        timeout = 14*24*60*60 #
                                                        return timeout, None
                if response['total_results'] > 1:
                   index_all = 0
                   find = False
                   for k in range(2,response['total_pages']+2):
                        index = 0
                        for i in search.results:
                                if only_tv:
                                        if i['media_type'] != u'tv':
                                                                index += 1
                                                                index_all += 1
                                                                continue
                                if i.get('name'):
                                        name_f = i['name']
                                        if i.get('first_air_date'): year_f = int(i['first_air_date'].split('-')[0])
                                        else: year_f = 0
                                if i.get('title'):
                                        name_f = i['title']
                                        if i.get('release_date'): year_f = int(i['release_date'].split('-')[0])
                                        else: year_f = 0
                                name_f_org = u''
                                if i.get('original_name'): name_f_org = i['original_name']
                                if i.get('original_title'): name_f_org = i['original_title']
                                if name_f.lower() == name.lower():
                                                        if year:
                                                                if i['media_type'] == u'tv':
                                                                        ident = self.tmdbs.TV(i['id'])
                                                                        response_all = ident.info()
                                                                        if response_all.get('last_air_date'):
                                                                                year_l = int(response_all['last_air_date'].split('-')[0])
                                                                                if year >= year_f and year <= year_l:
                                                                                        find = True
                                                                                        break
                                                                        elif abs(year-year_f) <= year_delta:
                                                                                find = True
                                                                                break
                                                                elif abs(year-year_f) <= year_delta:
                                                                        find = True
                                                                        break
                                                        else:
                                                                find = True
                                                                break
                                if name_f_org.lower() == name.lower():
                                                        if year:
                                                                if i['media_type'] == u'tv':
                                                                        ident = self.tmdbs.TV(i['id'])
                                                                        response_all = ident.info()
                                                                        if response_all.get('last_air_date'):
                                                                                year_l = int(response_all['last_air_date'].split('-')[0])
                                                                                if year >= year_f and year <= year_l:
                                                                                        find = True
                                                                                        break
                                                                        elif abs(year-year_f) <= year_delta:
                                                                                find = True
                                                                                break
                                                                elif abs(year-year_f) <= year_delta:
                                                                        find = True
                                                                        break
                                                        else:
                                                                find = True
                                                                break
                                if name_ru:
                                        if name_f.lower() == name_ru.lower():
                                                        if year:
                                                                if i['media_type'] == u'tv':
                                                                        ident = self.tmdbs.TV(i['id'])
                                                                        response_all = ident.info()
                                                                        if response_all.get('last_air_date'):
                                                                                year_l = int(response_all['last_air_date'].split('-')[0])
                                                                                if year >= year_f and year <= year_l:
                                                                                        find = True
                                                                                        break
                                                                        elif abs(year-year_f) <= year_delta:
                                                                                find = True
                                                                                break
                                                                elif abs(year-year_f) <= year_delta:
                                                                        find = True
                                                                        break
                                                        else:
                                                                find = True
                                                                break
                                index += 1
                                index_all += 1
                        if index_all >= response['total_results'] or index_all >= 1000:
                                timeout = 14*24*60*60 #
                                return timeout, None
                        else:
                           if not find:
                                        response = search.multi(query=name, page=k, language='ru', include_adult=True)
                           else: break
                res['m_type'] = search.results[index]['media_type']
                res['info']['title'] = name_f
                if name_f_org != u'': res['info']['originaltitle'] = name_f_org
                res['info']['plot'] = search.results[index]['overview']
                res['info']['rating'] = search.results[index]['vote_average']
                res['info']['votes'] = str(search.results[index]['vote_count'])
                if res['m_type'] == u'tv':
                        if search.results[index].get('first_air_date'):
                                res['info']['premiered'] = search.results[index]['first_air_date']
                if res['m_type'] == u'movie':
                        if search.results[index].get('release_date'):
                                res['info']['premiered'] = search.results[index]['release_date']
                if search.results[index].get('poster_path'):
                        res['thumb'] = 'https://image.tmdb.org/t/p/w500'+search.results[index]['poster_path']
                if search.results[index].get('backdrop_path'):
                        res['fanart'] = 'https://image.tmdb.org/t/p/w780'+search.results[index]['backdrop_path']

                res['genre_ids'] = search.results[index]['genre_ids']
                res['id'] = search.results[index]['id']
                #if search.results[index]['vote_count'] < 19: timeout = 60*24*60*60 #
                year = None
                if year_f !=0:
                        res['info']['year'] = year_f
                        year = year_f
                # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
                if year and year >= time.gmtime(time.time()).tm_year:
                            timeout = 14*24*60*60 # 2 weeks

                return timeout, res

        timeout = 14*24*60*60 #
        return timeout, None


    def _movie(self, id):
        res = { 'info': {},
        'thumb': None,
        'fanart': None,
        'cast': None,
        'id': None,
        }
        timeout = True #
        ident = self.tmdbs.Movies(id)
        try:
                response_all = ident.info(language='ru', append_to_response='credits,videos,releases')
        except BaseException as e:
                #errors.log(e)
                errors.log(e, u'ошибка tmdb (movie id:'+str(id)+') !!!')
                #timeout2 = 6*60*60
                return False, None #timeout2, None
        response = response_all
        tempstr = ''
        for k in response['genres']:
                tempstr += k['name']+', '
        res['info']['genre'] = tempstr[0:-2]
        tempstr = ''
        for k in response['production_countries']:
                tempstr += k['name']+', '
        res['info']['studio'] = tempstr[0:-2]
        tempstr = ''
        for k in response['production_companies']:
                tempstr += k['name']+', '
        separatorstr =u', '
        if res['info']['studio'] == u'': separatorstr = u''
        if tempstr != '': res['info']['studio'] = res['info']['studio'] +separatorstr+ tempstr[0:-2]
        res['info']['tagline'] = response['tagline']
        res['info']['status'] = response['status']
        res['info']['title'] = response['title']
        res['info']['originaltitle'] = response['original_title']
        res['info']['plot'] = response['overview']
        res['info']['rating'] = response['vote_average']
        res['info']['votes'] = str(response['vote_count'])
        #if response['vote_count'] < 19: timeout = 60*24*60*60 #
        #if response['overview'] == u'': timeout = 60*24*60*60 #
        res['info']['premiered'] = response['release_date']
        year = None
        if res['info'].get('premiered'):
                year = int(response['release_date'].split('-')[0])
                res['info']['year'] = year
        res['info']['code'] = response['imdb_id']
        if response.get('poster_path'):
                res['thumb'] = 'https://image.tmdb.org/t/p/w500'+response['poster_path']
        if response.get('backdrop_path'):
                res['fanart'] = 'https://image.tmdb.org/t/p/w780'+response['backdrop_path'] # original
        res['runtime'] = response['runtime']
        res['budget'] = response['budget']
        res['revenue'] = response['revenue']
        res['popularity'] = response['popularity']
        res['id'] = response['id']
        #response = ident.credits()
        response = response_all['credits']
        #res['info']['cast'] = [ i['name'] for i in response['cast'] if i]
        #res['info']['castandrole'] =[ (i['name'], i['character']) for i in response['cast'] if i]
        #res['cast'] = [ {'name': i['name'], 'role': i['character'], 'order': i['order'], 'thumbnail': 'https://image.tmdb.org/t/p/w185'+i['profile_path'] if i['profile_path'] else None} for i in response['cast'] if i]
        castfull = [] # оптимизация в один цикл
        cast = []
        castandrole = []
        for i in response['cast']:
                cast.append(i['name'])
                castandrole.append( (i['name'], i['character']) )
                castfull.append( {'name': i['name'], 'role': i['character'], 'order': i['order'], 'thumbnail': 'https://image.tmdb.org/t/p/w185'+i['profile_path'] if i['profile_path'] else None} )
        res['info']['cast'] = cast
        res['info']['castandrole'] = castandrole
        res['cast'] = castfull
        # w45, w185
        director = writer = ''
        for i in response['crew']:
                if i['job'] == u'Director': director += i['name']+u', '
                if i['job'] == u'Screenplay': writer += i['name']+u', '
                elif i['job'] == u'Writer': writer += i['name']+u', '
        res['info']['director'] = director[0:-2]
        res['info']['writer'] = writer[0:-2]
        #response = ident.videos(language='ru')
        response = response_all['videos']
        for i in response['results']:
                if i['type'] == u'Trailer':
                        if i['site'] == u'YouTube': res['info']['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % i['key']
        if not res['info'].get('trailer'):
                response = ident.videos()
                for i in response['results']:
                        if i['type'] == u'Trailer':
                                if i['site'] == u'YouTube': res['info']['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % i['key']
        #response = ident.releases()
        response = response_all['releases']
        year_new = 9999
        mpaa = u''
        for i in response['countries']:
                yeartemp = int(i['release_date'].split('-')[0])
                if yeartemp < year_new: year_new = yeartemp # ищем год выхода фильма
                if i['iso_3166_1'] == u'US' and mpaa == u'': mpaa = i['certification']
                if i['iso_3166_1'] == u'RU': mpaa = i['certification']
        if year_new != 9999:
                        res['info']['year'] = year_new
                        year = year_new
        if mpaa != u'': res['info']['mpaa'] = mpaa
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year >= time.gmtime(time.time()).tm_year:
            timeout = 14*24*60*60 # 2 weeks

        return timeout, res


    def _search_movie(self, name, year=None):
        res = {
        'info': {},
        'thumb': None,
        'fanart': None,
        'id': None,
        }
        timeout = True #
        if name == u'':
                        timeout= 14*24*60*60 #
                        return timeout, None
        search: Any = self.tmdbs.Search()
        if year:
                response = search.movie(query=name, year=year, language='ru', include_adult=True)
        else:
                response = search.movie(query=name, language='ru', include_adult=True)
        if search.results:
                if response['total_results'] == 1: index = 0
                if response['total_results'] > 1:
                   index_all = 0
                   find = False
                   for k in range(2,response['total_pages']+2):
                        index = 0
                        for i in search.results:
                                if i['title'].lower() == name.lower():
                                        #if year:
                                        #        if int(year) == int(i['release_date'].split('-')[0]):
                                        #                find = True
                                        #                break
                                        #else:
                                                        find = True
                                                        break
                                if i['original_title'].lower() == name.lower():
                                        #if year:
                                        #        if int(year) == int(i['release_date'].split('-')[0]):
                                        #                find = True
                                        #                break
                                        #else:
                                                        find = True
                                                        break
                                index += 1
                                index_all += 1
                        if index_all >= response['total_results'] or index_all >= 1000:
                                timeout = 14*24*60*60 #
                                return timeout, None
                        else:
                           if not find:
                                if year:
                                        response = search.movie(query=name, year=year, page=k, language='ru', include_adult=True)
                                else:
                                        response = search.movie(query=name, page=k, language='ru', include_adult=True)
                           else: break

                res['info']['title'] = search.results[index]['title']
                res['info']['originaltitle'] = search.results[index]['original_title']
                res['info']['plot'] = search.results[index]['overview']
                res['info']['rating'] = search.results[index]['vote_average']
                res['info']['votes'] = str(search.results[index]['vote_count'])
                res['info']['premiered'] = search.results[index]['release_date']
                if search.results[index].get('poster_path'):
                        res['thumb'] = 'https://image.tmdb.org/t/p/w500'+search.results[index]['poster_path']
                if search.results[index].get('backdrop_path'):
                        res['fanart'] = 'https://image.tmdb.org/t/p/w780'+search.results[index]['backdrop_path'] # original
                id = search.results[index]['id']
                res['id'] = id
                #if search.results[index]['vote_count'] < 19: timeout = 60*24*60*60 #
                year = None
                if res['info'].get('premiered'):
                        year = int(res['info']['premiered'].split('-')[0])

                # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
                if year and year >= time.gmtime(time.time()).tm_year:
                            timeout = 14*24*60*60 # 2 weeks
                return timeout, res

        timeout = 14*24*60*60 #
        return timeout, None
