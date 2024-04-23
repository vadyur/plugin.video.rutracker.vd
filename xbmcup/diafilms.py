import re, os, time, sys

import xbmcgui
import xbmc

class Diafilm(xbmcgui.WindowXML):
    # Controls
    CONTROL_MAIN_IMAGE = 100
    # Actions
    ACTION_CONTEXT_MENU = [117]
    ACTION_MENU = [122]
    ACTION_PREVIOUS_MENU = [9]
    ACTION_SHOW_INFO = [11]
    ACTION_EXIT_SCRIPT = [10, 13, 92]   # 10-ESC, 13-X,92-Backspace
    ACTION_DOWN = [4]
    ACTION_UP = [3]
    ACTION_0 = [58]

    def __init__(self, xmlFilename, scriptPath, defaultSkin, defaultRes):
        pass

    def Set_URL(self, url):
        self.Diafilm_URL= url

    def onInit(self):
        self.Clean_List()

        # -- fill up the image list
        # get diafilm list
        for df in self.Diafilm_URL:
            self.Add_to_List(df['url'], df['title'])

        self.setFocus(self.getControl(self.CONTROL_MAIN_IMAGE))

    def onAction(self, action):
        if action in self.ACTION_EXIT_SCRIPT:
            self.close()

    def onClick(self, controlId):
        pass

    def Clean_List(self):
        self.getControl(self.CONTROL_MAIN_IMAGE).reset()

    def Add_to_List(self, url, title):
        li = xbmcgui.ListItem(label=title,
                              iconImage=url,
                              path = url)
        li.setProperty('show_info', 'true')
        li.setProperty('show_info', 'photo')
        li.setProperty('title', title)
        li.setProperty('aspectratio', 'keep')
        self.getControl(self.CONTROL_MAIN_IMAGE).addItem(li)
