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

from __init__ import _
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Button import Button
from Screens.EventView import EventViewSimple
from TMDB import TMDB


class IMDbEventViewSimple(EventViewSimple, TMDB, object):

	def __init__(self, session, Event, Ref, callback=None, similarEPGCB=None):
		EventViewSimple.__init__(self, session, Event, Ref, callback, similarEPGCB)
		self.skinName = ["EventViewSimple", "EventView"]
		if config.MVC.InfoLong.value == "IMDbSearch":
			text_blue = _("IMDb")
		elif config.MVC.InfoLong.value == "TMDBInfo":
			text_blue = _("TMDb")
		elif config.MVC.InfoLong.value == "CSFDInfo":
			text_blue = _("CSFD")
		else:
			text_blue = ""
		self["key_blue"] = Button(text_blue)
		self["epgactions"] = ActionMap(["EventViewEPGActions"], {"openMultiServiceEPG": self.InfoDetail})

	def InfoDetail(self):
		nameM = self.getMovieNameWithoutPhrases(self.getMovieNameWithoutExt(self.event.getEventName()))
		if nameM != "":
			if config.MVC.InfoLong.value == "IMDbSearch":
				self.IMDbSearchName(nameM)
			elif config.MVC.InfoLong.value == "TMDBInfo":
				self.TMDBInfoName(nameM)
			elif config.MVC.InfoLong.value == "CSFDInfo":
				self.CSFDInfoName(nameM)
			else:
				pass

	def setService(self, service):
		EventViewSimple.setService(self, service)
		if self.isRecording:
			self["channel"].setText("")

	def setEvent(self, event):
		EventViewSimple.setEvent(self, event)
		if (self.isRecording) and (event.getDuration() == 0):
			self["duration"].setText("")
		else:
			self["duration"].setText(_("%d min") % (event.getDuration() / 60))

	def IMDbSearchName(self, name):
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, name, False)
		except ImportError:
			pass

	def TMDBInfoName(self, name):
		try:
			from Plugins.Extensions.TMDb.plugin import TMDbMain
			self.session.open(TMDbMain, name)
		except ImportError:
			pass

	def CSFDInfoName(self, name):
		try:
			from Plugins.Extensions.CSFD.plugin import CSFD
			self.session.open(CSFD, name, False)
		except ImportError:
			pass
