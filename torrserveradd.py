# -*- coding: utf-8 -*-
import xbmcgui
from xbmcup.app import Handler
from drivers.rutracker import RuTracker

class AddTorrserverBase(Handler):
	def handle(self):
		self.show_busy()
		from xbmcup import torrserver
		self.rutracker = RuTracker()
		data = self.rutracker.download(self.argv['id'])
		if not data:
			return True
		scraper = self.argv['scraper']
		s_info = scraper['info']
		s_info['mediatype'] = 'movie'
		info = { 'kodi': { 'info' : s_info, 'cast': scraper['cast'] } }
		if self.argv['profile']['descript']: info['descript'] = self.argv['profile']['descript']
		if self.argv['scraper']['thumb']: info['poster_path'] = self.argv['scraper']['thumb']
		res = torrserver.add(title=self.argv['name'], info=info, data=data)
		if res: xbmcgui.Dialog().ok(self.nameaddon, self.lang[30042])
		return True
