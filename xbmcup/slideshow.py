# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os

import xbmcgui
from errors import log as _log

class SlideShow(xbmcgui.WindowXMLDialog):
    ACTION_PREVIOUS_MENU = [9, 92, 10, 13]
    ID_LIST_PICTURES = 5000

    def __init__(self, *args, **kwargs):
        self.images = kwargs.get('listitems')
        self.index = kwargs.get('index')
        self.image = kwargs.get('image')
        self.action = None

    def onInit(self):
        super(SlideShow, self).onInit()
        if not self.images:
            return None
        self.getControl(self.ID_LIST_PICTURES).addItems(self.create_listitems(self.images))
        self.getControl(self.ID_LIST_PICTURES).selectItem(self.index)
        self.setFocusId(self.ID_LIST_PICTURES)

    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.position = self.getControl(self.ID_LIST_PICTURES).getSelectedPosition()
            self.close()

    def create_listitems(self, img):
        items = []
        _log(img)
        j = 1
        for i in img:
                li = xbmcgui.ListItem(label=str(j),
                              iconImage=i,
                              thumbnailImage=i,
                              path = i)
                li.setArt({'poster': i, 'fanart': i})
                li.setProperty('show_info', 'true')
                li.setProperty('show_info', 'photo')
                li.setProperty('title', i)
                li.setProperty('aspectratio', 'keep')
                items.append(li)
                j += 1
        _log(items)
        return items


def open(listitems, index):
    slideshow = SlideShow(u'script-script.module.kodi65-pictureviewer.xml',
                          os.path.join(os.path.dirname(__file__), ".."),
                          'default', '1080i',
                          listitems=listitems,
                          index=index)
    slideshow.doModal()
    return slideshow.position
