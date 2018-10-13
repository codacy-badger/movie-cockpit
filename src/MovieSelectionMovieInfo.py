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

from Components.config import config
from ServiceReference import ServiceReference
from TMDB import TMDB
from TMDBInfo import TMDBInfo


class MovieInfo(TMDBInfo, TMDB, object):

	def openInfoLong(self):
		if config.MVC.InfoLong.value == "IMDbSearch":
			self.IMDbSearch()
		elif config.MVC.InfoLong.value == "MVC-TMDBInfo":
			self.MVCTMDBInfo()
		elif config.MVC.InfoLong.value == "TMDBInfo":
			self.TMDBInfo()
		elif config.MVC.InfoLong.value == "TMBDInfo":
			self.TMBDInfo()
		elif config.MVC.InfoLong.value == "CSFDInfo":
			self.CSFDInfo()
		else:
			pass

	def IMDbSearch(self):
		name = ''
		if (self["list"].getCurrentSelName()):
			name = (self["list"].getCurrentSelName())
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			name = self.getMovieNameWithoutPhrases(self.getMovieNameWithoutExt(name))
			self.checkHideMiniTV_beforeFullscreen()
			self.session.open(IMDB, name, False)
		except ImportError:
			pass

	def MVCTMDBInfo(self):
		service = self["list"].getCurrent()
		if service:
			path = service.getPath()
			if path and path != config.MVC.movie_trashcan_path.value:
				if not path.endswith("/.."):
					name = service.getName()
					#					spath = self.getInfoFilePath(path)
					self.checkHideMiniTV_beforeFullscreen()
					self.session.open(TMDBInfo, name, path)

	def TMDBInfo(self):
		name = ''
		if (self["list"].getCurrentSelName()):
			name = (self["list"].getCurrentSelName())
		try:
			from Plugins.Extensions.TMDb.plugin import TMDbMain
			name = self.getMovieNameWithoutPhrases(self.getMovieNameWithoutExt(name))
			self.checkHideMiniTV_beforeFullscreen()
			self.session.open(TMDbMain, name)
		except ImportError:
			pass

	def TMBDInfo(self):
		name = ''
		if (self["list"].getCurrentSelName()):
			name = (self["list"].getCurrentSelName())
		try:
			from Plugins.Extensions.TMBD.plugin import TMBD
		except ImportError:
			TMBD = None
		if TMBD:
			name = self.getMovieNameWithoutPhrases(self.getMovieNameWithoutExt(name))
			self.checkHideMiniTV_beforeFullscreen()
			self.session.open(TMBD, name)

	def CSFDInfo(self):
		name = ''
		if self["list"].getCurrentSelName():
			name = self["list"].getCurrentSelName()
		try:
			from Plugins.Extensions.CSFD.plugin import CSFD
			name = self.getMovieNameWithoutPhrases(self.getMovieNameWithoutExt(name))
			self.checkHideMiniTV_beforeFullscreen()
			self.session.open(CSFD, name, False)
		except ImportError:
			pass

	def showEventInformation(self):
		# Get our customized event
		from IMDbEventViewSimple import IMDbEventViewSimple
		print("MVC: MovieSelectionMovieInfo: showEventInformation: getCurrentSelDir():" + self["list"].getCurrentSelDir())
		if not self["list"].getCurrentSelDir().endswith("/.."):
			evt = self["list"].getCurrentEvent()
			if evt:
				self.checkHideMiniTV_beforeFullscreen()
				self.session.open(IMDbEventViewSimple, evt, ServiceReference(self.getCurrent()))
