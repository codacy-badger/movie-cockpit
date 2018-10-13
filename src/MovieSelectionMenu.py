#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#               2018 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#

import os
from __init__ import _
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Components.Sources.StaticText import StaticText
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.Harddisk import Util
from Bookmarks import Bookmarks
from SkinUtils import getSkinPath
from plugin import settingsOpen as mvcsetup

FUNC_IDX_MOVIE_HOME = 0
FUNC_IDX_DIR_UP = 1
FUNC_IDX_RELOAD_WITHOUT_CACHE = 2
FUNC_IDX_DELETE = 3
FUNC_IDX_DELETE_PERMANENTLY = 4
FUNC_IDX_EMPTY_TRASHCAN = 5
FUNC_IDX_OPEN_TRASHCAN = 6
FUNC_IDX_SELECT_ALL = 7
FUNC_IDX_COPY = 8
FUNC_IDX_MOVE = 9
FUNC_IDX_OPEN_SETUP = 10
FUNC_IDX_RELOAD = 11
FUNC_IDX_REMOVE_MARKER = 12
FUNC_IDX_DELETE_CUTLIST = 13


class MovieMenu(Screen, Bookmarks, object):
	skin = Util.readFile(getSkinPath("MovieSelectionMenu.xml"))

	def __init__(self, session, menumode, service, selections, current_path):
		Screen.__init__(self, session)
		self["title"] = StaticText()
		self.service = service
		self.selections = selections
		self.reload_after_close = False
#
		self["actions"] = ActionMap(
			["OkCancelActions", "ColorActions"],
			{"ok": self.okButton, "cancel": self.close, "red": self.close}
		)

		self.menu = []
		if menumode == "functions":
			self.setTitle(_("Select function"))

			if not self.isBookmark(os.path.realpath(current_path)):
				self.menu.append((_("Movie home"), boundFunction(self.close, FUNC_IDX_MOVIE_HOME)))

			if current_path == config.MVC.movie_pathlimit.value:
				self.menu.append((_("Directory up"), boundFunction(self.close, FUNC_IDX_DIR_UP)))

			self.menu.append((_("Select all"), boundFunction(self.close, FUNC_IDX_SELECT_ALL)))

			self.menu.append((_("Delete"), boundFunction(self.close, FUNC_IDX_DELETE)))
			self.menu.append((_("Move"), boundFunction(self.close, FUNC_IDX_MOVE)))
			self.menu.append((_("Copy"), boundFunction(self.close, FUNC_IDX_COPY)))

			if config.MVC.movie_trashcan_enable.value and os.path.exists(config.MVC.movie_trashcan_path.value):
				self.menu.append((_("Delete permanently"), boundFunction(self.close, FUNC_IDX_DELETE_PERMANENTLY)))
				self.menu.append((_("Empty trashcan"), boundFunction(self.close, FUNC_IDX_EMPTY_TRASHCAN)))
				self.menu.append((_("Go to trashcan"), boundFunction(self.close, FUNC_IDX_OPEN_TRASHCAN)))

			self.menu.append((_("Remove cutlist marker"), boundFunction(self.close, FUNC_IDX_REMOVE_MARKER)))
			self.menu.append((_("Delete cutlist file"), boundFunction(self.close, FUNC_IDX_DELETE_CUTLIST)))

			self.menu.append((_("Reload cache"), boundFunction(self.close, FUNC_IDX_RELOAD_WITHOUT_CACHE)))
			self.menu.append((_("Setup"), boundFunction(self.execPlugin, mvcsetup)))

		elif menumode == "plugins":
			self.setTitle(_("Select plugin"))
			if service:
				for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST):
					self.menu.append((p.description, boundFunction(self.execPlugin, p)))

		self["menu"] = List(self.menu)
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		return

	def okButton(self):
		self["menu"].getCurrent()[1]()

	# Overwrite Screen close function
	def close(self, function=None):
		if function is None:
			if self.reload_after_close:
				function = FUNC_IDX_RELOAD
		# Call base class function
		Screen.close(self, function)

	def execPlugin(self, plugin):
		# Very bad but inspect.getargspec won't work
		# Plugins should always be designed to accept additional parameters!
		try:
			plugin(self.session, self.service, self.selections)
		except Exception:
			plugin(session=self.session, service=self.service)
