#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 dream-alpha
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

import shutil
from __init__ import _
from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.Button import Button
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.Pixmap import Pixmap
from enigma import eTimer
from Tools.Directories import fileExists
from Components.Harddisk import Util
from SkinUtils import getSkinPath
from TMDB import TMDB
from Cover import Cover

PAGE_DETAILS = 0   # details
PAGE_SELECTION = 1 # selection list
IDX_COVER_URL = 6
TEMP_COVER = "/tmp/PreviewCover.jpg"
SELECTION_ID = 1   # tmdb movie id
SELECTION_TYPE = 2 # movie or tvshow

class TMDBInfo(Screen, TMDB, Cover, object):
	skin = Util.readFile(getSkinPath("TMDBInfo.xml"))

	def __init__(self, session, moviename, spath=None):
		print("MVC: TMDBInfo: __init__: moviename: %s, spath: %s" % (moviename, spath))
		Screen.__init__(self, session)
		self.cover_size = config.MVC.cover_size.value
		self.show_format = config.MVC.movie_show_format.value
		self.moviename = self.getMovieNameWithoutExt(moviename)
		self.search_moviename = self.getMovieNameWithoutPhrases(self.moviename)
		self.movielist = None
		self.spath = spath
		self.page = PAGE_DETAILS
		self.info = None
		self.selection = None

		self.coverTimer = eTimer()
		self.coverTimer_conn = self.coverTimer.timeout.connect(self.showCover)

		self["previewcover"] = Pixmap()
		self["nocover"] = Pixmap()
		self["previewlist"] = MenuList([])
		self["movie_name"] = Label("")
		self["contenttxt"] = ScrollLabel()
		self["runtime"] = Label(_("Runtime") + ":")
		self["runtimetxt"] = Label("")
		self["genre"] = Label(_("Genre") + ":")
		self["genretxt"] = Label("")
		self["country"] = Label(_("Production Countries") + ":")
		self["countrytxt"] = Label("")
		self["release"] = Label(_("Release Date") + ":")
		self["releasetxt"] = Label("")
		self["rating"] = Label(_("Vote") + ":")
		self["ratingtxt"] = Label("")
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1
		self.deleteCover(TEMP_COVER)
		self.movielist = self.getMovieList(self.search_moviename, config.MVC.cover_auto_selection.value)
		if self.movielist:
			self["previewlist"] = MenuList(self.movielist[0])
			if self.movielist[1] > 1:
				self.page = PAGE_SELECTION
			else:
				self.page = PAGE_DETAILS

			self.selection = self["previewlist"].l.getCurrentSelection()
			print("MVC: TMDBInfo: __init__: selection: " + str(self.selection))
			if self.selection:
				self.info = self.getTMDBInfo(self.selection[SELECTION_ID], self.selection[SELECTION_TYPE], config.MVC.cover_language.value)
				self.downloadCover(self.info[IDX_COVER_URL], TEMP_COVER)
		else:
			self.page = PAGE_DETAILS
			self.selection = None
			self.info = None

		self.mpath = None

		self.onLayoutFinish.append(self.layoutFinished)
		self["actions"] = HelpableActionMap(
			self,
			"TMDBInfo",
			{
				"MVCEXIT": self.exit,
				"MVCUp": self.pageUp,
				"MVCDown": self.pageDown,
				"MVCOK": self.ok,
				"MVCGreen": self.ok,
				"MVCYellow": self.save,
				"MVCRed": self.exit,
			},
			-1
		)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button("")
		self["key_yellow"] = Button(_("Save"))

		self["previewlist"].onSelectionChanged.append(self.selectionChanged)

	def layoutFinished(self):
		self.setTitle(_("Movie Information TMDb"))
		self.switchPage()

	def selectionChanged(self):
		print("MVC: TMDBInfo: selectionChanged")
		if self.page == PAGE_SELECTION:
			self.deleteCover(TEMP_COVER)
			self.selection = self["previewlist"].l.getCurrentSelection()
			print("MVC: TMDBInfo: selectionChanged: selection: " + str(self.selection))
			if self.selection:
				self.info = self.getTMDBInfo(self.selection[SELECTION_ID], self.selection[SELECTION_TYPE], config.MVC.cover_language.value)
				self.downloadCover(self.info[IDX_COVER_URL], TEMP_COVER)
				self.switchPage()

	def switchPage(self):
		print("MVC: TMDBInfo: switchPage: " + str(self.page))
		if self.page == PAGE_SELECTION:
			self["movie_name"].setText(_("Search results for") + ": " + self.search_moviename)
			self["previewlist"].show()
			self["contenttxt"].hide()
			self["key_yellow"].hide()
			self["key_green"].show()
		else:
			self["previewlist"].hide()
			self["contenttxt"].show()
			self["key_yellow"].show()
			self["key_green"].hide()

		if self.info:
			self["movie_name"].setText(self.moviename)
			content, runtime, genres, countries, release, vote, _cover_url = self.info
			self["contenttxt"].setText(content)
			if runtime != "":
				self["runtimetxt"].setText(runtime + " " + _("Minutes"))
			else:
				self["runtimetxt"].setText(runtime)
			self["genretxt"].setText(genres)
			self["countrytxt"].setText(countries)
			self["releasetxt"].setText(release)
			if vote:
				self["ratingtxt"].setText(vote.replace('\n', '') + " / 10")
				self.ratingstars = int(10 * round(float(vote.replace(',', '.')), 1))
				if self.ratingstars > 0:
					self["starsbg"].show()
					self["stars"].show()
					self["stars"].setValue(self.ratingstars)
				else:
					self["starsbg"].show()
					self["stars"].hide()
			else:
				self["ratingtxt"].setText("0 / 10")
				self["starsbg"].show()
				self["stars"].hide()
		else:
			self["movie_name"].setText(_("Search results for") + ": " + self.search_moviename)
			self["contenttxt"].setText(_("Nothing was found"))
			self["contenttxt"].show()
		self.coverTimer.start(int(config.MVC.cover_delay.value), True)

	def save(self):
		print("MVC: TMDBInfo: save: self.spath: " + self.spath)
		if self.page == PAGE_DETAILS and self.spath:
			self.mpath = self.getCoverPath(self.spath)
			if fileExists(self.mpath):
				self.session.openWithCallback(
					self.saveCallback,
					MessageBox,
					_("Cover exists")
					+ "\n"
					+ _("Do you want to replace the existing cover?"),
					MessageBox.TYPE_YESNO
				)
			else:
				self.saveTempCover(self.mpath)

	def saveCallback(self, result):
		if result:
			self.saveTempCover(self.mpath)

	def saveTempCover(self, cover_path):
		print("MVC: TMDBInfo: saveTempCover: cover_path: " + cover_path)
		if fileExists(TEMP_COVER):
			try:
				shutil.copy2(TEMP_COVER, cover_path)
				self.showMsg(failed=False)
			except Exception as e:
				print('MVC: TMDBInfo: saveTempCover: exception failure:\n', str(e))
				self.showMsg(failed=True)
		else:
			self.showMsg(failed=True)

	def showMsg(self, askno=False, failed=False):
		if not askno:
			if not failed:
				msg = _("Cover saved successfully")
			else:
				msg = _("Saving cover failed")
			self.session.open(
				MessageBox,
				msg,
				MessageBox.TYPE_INFO,
				5
			)

	def ok(self):
		if self.page == PAGE_SELECTION:
			self.page = PAGE_DETAILS
			self.switchPage()

	def pageUp(self):
		if self.page == PAGE_DETAILS:
			self["contenttxt"].pageUp()
		if self.page == PAGE_SELECTION:
			self["previewlist"].up()

	def pageDown(self):
		if self.page == PAGE_DETAILS:
			self["contenttxt"].pageDown()
		if self.page == PAGE_SELECTION:
			self["previewlist"].down()

	def showCover(self):
		print("MVC: TMDBInfo: ShowCover")
		self.displayCover(TEMP_COVER, self["previewcover"], getSkinPath("img/tmdb.svg"))

	def exit(self):
		print("MVC: TMDBInfo: exit")
		if self.movielist:
			if self.page == PAGE_DETAILS and self.movielist[1] > 1:
				self["movie_name"].setText(_("Search results for") + ": " + self.moviename)
				self.page = PAGE_SELECTION
				self.switchPage()
				return

		self["previewlist"].onSelectionChanged = []
		self.close()
