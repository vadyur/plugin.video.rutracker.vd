# -*- coding: utf-8 -*-

import sys, os, time

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

addon = xbmcaddon.Addon()


def fs_dec(path):
    sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
    return path.decode(sys_enc).encode('utf-8')

def fs_enc(path):
	path=xbmc.translatePath(path)
	sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
	try:path2=path.decode('utf-8')
	except: pass
	try:path2=path2.encode(sys_enc)
	except: 
		try: path2=path2.encode(sys_enc)
		except: path2=path
	return path2


class xPlayer(xbmc.Player):
	def __init__(self, hash=None, index=0, engine=None):
		self.tsserv = None
                self.hash = hash
                self.engine = engine
                self.index = index
		self.active = True
		self.started = False
		self.ended = False
		self.paused = False
		self.buffering = False
		xbmc.Player.__init__(self)
		width, height = xPlayer.get_skin_resolution()
		w = width
		h = int(0.14 * height)
		x = 0
		y = (height - h) / 2
		self._ov_window = xbmcgui.Window(12005)
		self._ov_label = xbmcgui.ControlLabel(x, y, w, h, '', alignment=6)
		self._ov_background = xbmcgui.ControlImage(x, y, w, h, fs_dec(xPlayer.get_ov_image()))
		self._ov_background.setColorDiffuse('0xD0000000')
		self.ov_visible = False
		self.onPlayBackStarted()


	def onPlayBackPaused(self):
		self.ov_show()


	def onPlayBackStarted(self):
		self.ov_hide()
		if not xbmc.Player().isPlaying(): xbmc.sleep(2000)
		status = ''
		while xbmc.Player().isPlaying():
			if self.ov_visible == True:
			      try:
                                engine_t2h = self.engine
				try:
					status   = engine_t2h.status()
					speed    = status.download_rate / 1024 * 8
					seeds    = status.num_seeds
				except:
					speed    = '?????'
					seeds    = '?'

				try:    tdownload = status.total_download / 1024 / 1024
				except: tdownload = '???'

				try:
					file_status = engine_t2h.file_status(self.index)
					download = file_status.download / 1024 / 1024
				except:
					download = tdownload

				status = "Загружено "+str(download)+" Мб \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)[:4]+' Мбит/сек'

			      except:
                                        status = 'error'
			      self.ov_update(status)
			xbmc.sleep(800)


	def onPlayBackResumed(self):
		self.ov_hide()
		
	def onPlayBackStopped(self):
		self.ov_hide()
	
	def __del__(self):
		self.ov_hide()

	@staticmethod
	def get_ov_image():
		ov_image = fs_enc(os.path.join(addon.getAddonInfo('path'), 'bg.png'))
		if not os.path.isfile(ov_image):
			import base64
			fl = open(ov_image, 'wb')
			fl.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='))
			fl.close()
		return ov_image

	@staticmethod
	def get_skin_resolution():
		import xml.etree.ElementTree as Et
		skin_path = fs_enc(xbmc.translatePath('special://skin/'))
		tree = Et.parse(os.path.join(skin_path, 'addon.xml'))
		res = tree.findall('./extension/res')[0]
		return int(res.attrib['width']), int(res.attrib['height'])

	def ov_show(self):
		if not self.ov_visible:
			self._ov_window.addControls([self._ov_background, self._ov_label])
			self.ov_visible = True

	def ov_hide(self):
		if self.ov_visible:
			self._ov_window.removeControls([self._ov_background, self._ov_label])
			self.ov_visible = False

	def ov_update(self, txt=" "):
		if self.ov_visible:
			self._ov_label.setLabel(txt)
