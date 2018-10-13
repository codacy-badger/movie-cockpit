#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#               2018 by dream_alpha
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
from time import time
from CutList import CutList
from ServiceCenter import ServiceCenter
from MovieCache import MovieCache, TYPE_ISLINK, TYPE_ISDIR, str2date
from MediaTypes import extTS, extVideo, plyAll, cmtUp, cmtTrash, cmtBM, cmtDir
from MountPoints import MountPoints
from Bookmarks import Bookmarks
from SkinUtils import getSkinPath
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor, parseFont, parseSize
from enigma import eListboxPythonMultiContent, eListbox, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG
from RecordingsControl import RecordingsControl


class MovieCenterGUI(GUIComponent, MountPoints, Bookmarks, object):
	GUI_WIDGET = eListbox

	def __init__(self):
		#print("MVC: MovieCenterGUI: __init__")
		GUIComponent.__init__(self)
		self.initSkin()

	def initSkin(self):
		self.MVCFont = parseFont("Regular;30", ((1, 1), (1, 1)))
		self.MVCSelectFont = parseFont("Regular;30", ((1, 1), (1, 1)))
		self.MVCDateFont = parseFont("Regular;28", ((1, 1), (1, 1)))

		self.MVCStartHPos = 10
		self.MVCSpacer = 10

		self.MVCMovieHPos = None
		self.MVCMovieVPos = None
		self.MVCMovieWidth = None

		self.MVCDateHPos = None
		self.MVCDateVPos = None
		self.MVCDateWidth = 230

		self.MVCProgressHPos = None
		self.MVCProgressVPos = None

		self.MVCBarHPos = None
		self.MVCBarVPos = None
		self.MVCBarSize = parseSize("90, 14", ((1, 1), (1, 1)))

		self.MVCIconVPos = None
		self.MVCIconHPos = None
		self.MVCIconSize = parseSize("45, 35", ((1, 1), (1, 1)))

		self.MVCRecIconVPos = None
		self.MVCRecIconHPos = None
		self.MVCRecIconSize = parseSize("230, 40", ((1, 1), (1, 1)))

		# MVCSelNumTxtHPos is equal to MVCIconHPos
		# MVCSelNumTxtWidth is equal to MVCIconSize.width()
		self.MVCSelNumTxtVPos = None

		self.MVCPiconHPos = None
		self.MVCPiconVPos = None
		self.MVCPiconSize = parseSize("55, 35", ((1, 1), (1, 1)))

		self.DefaultColor = parseColor("#bababa").argb()
		self.TitleColor = parseColor("#bababa").argb()
		self.DateColor = parseColor("#bababa").argb()
		self.BackColor = None
		self.BackColorSel = None
		self.FrontColorSel = parseColor(config.MVC.color_highlight.value).argb()
		self.RecordingColor = parseColor(config.MVC.color_recording.value).argb()

		skin_path = getSkinPath("img/")
		self.pic_back = LoadPixmap(cached=True, path=skin_path + "back.svg")
		self.pic_directory = LoadPixmap(cached=True, path=skin_path + "dir.svg")
		self.pic_movie_default = LoadPixmap(cached=True, path=skin_path + "movie_default.svg")
		self.pic_movie_watching = LoadPixmap(cached=True, path=skin_path + "movie_watching.svg")
		self.pic_movie_finished = LoadPixmap(cached=True, path=skin_path + "movie_finished.svg")
		self.pic_movie_rec = LoadPixmap(cached=True, path=skin_path + "movie_rec.svg")
		self.pic_movie_cut = LoadPixmap(cached=True, path=skin_path + "movie_cut.svg")
		self.pic_e2bookmark = LoadPixmap(cached=True, path=skin_path + "e2bookmark.svg")
		self.pic_trashcan = LoadPixmap(cached=True, path=skin_path + "trashcan.svg")
		self.pic_trashcan_full = LoadPixmap(cached=True, path=skin_path + "trashcan_full.svg")
		self.pic_link = LoadPixmap(cached=True, path=skin_path + "link.svg")
		self.pic_col_dir = LoadPixmap(cached=True, path=skin_path + "coldir.svg")
		self.pic_progress_bar = LoadPixmap(cached=True, path=skin_path + "progcl.svg")
		self.pic_rec_progress_bar = LoadPixmap(cached=True, path=skin_path + "rec_progcl.svg")
		self.pic_recording = LoadPixmap(cached=True, path=skin_path + "recording.svg")

	def applySkin(self, desktop, parent):
		attribs = []
		value_attributes = [
			"MVCStartHPos", "MVCSpacer", "MVCMovieHPos", "MVCMovieVPos", "MVCMovieWidth" "MVCIconVPos", "MVCIconHPos", "MVCRecIconVPos", "MVCRecIconHPos",
			"MVCBarHPos", "MVCBarVPos", "MVCDateHPos", "MVCDateVPos", "MVCDateWidth", "MVCSelNumTxtVPos", "MVCProgressHPos", "MVCProgressVPos",
			"MVCPiconHPos", "MVCPiconVPos"
		]
		size_attributes = [
			"MVCBarSize", "MVCIconSize", "MVCRecIconSize", "MVCPiconSize"
		]
		font_attributes = [
			"MVCFont", "MVCSelectFont", "MVCDateFont"
		]
		color_attributes = [
			"TitleColor", "DateColor", "DefaultColor", "BackColor", "BackColorSel", "FrontColorSel", "RecordingColor"
		]

		if self.skinAttributes:
			for (attrib, value) in self.skinAttributes:
				if attrib in value_attributes:
					setattr(self, attrib, int(value))
				elif attrib in size_attributes:
					setattr(self, attrib, parseSize(value, ((1, 1), (1, 1))))
				elif attrib in font_attributes:
					setattr(self, attrib, parseFont(value, ((1, 1), (1, 1))))
				elif attrib in color_attributes:
					setattr(self, attrib, parseColor(value).argb())
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs

		self.l.setFont(1, self.MVCFont)
		self.l.setFont(3, self.MVCSelectFont)
		self.l.setFont(4, self.MVCDateFont)

		#print("MVC: MovieCenterGUI: applySkin: attribs: " + str(attribs))
		return GUIComponent.applySkin(self, desktop, parent)

	def buildMovieCenterEntry(self, service, date, title, path, selnum, length, ext, filetype, cut_list, service_reference):

		def xPos(x, startHPos):
			if x is None:
				x = startHPos
			return x

		def yPos(ySize, yHeight, y):
			if y is None:
				y = (ySize - yHeight) / 2
			return y

		def getPiconPath(service_reference):
			piconpath = ""
			if config.MVC.movie_picons.value:
				metaref = service_reference
				pos = metaref.rfind(':')
				if pos != -1:
					metaref = metaref[:pos].rstrip(':').replace(':', '_')
				piconpath = config.MVC.movie_picons_path.value + "/" + metaref + '.png'
				#print("MVC: MovieCenterGUI: buildMovieCenterEntry: piconpath: " + piconpath)
			return piconpath

		def createProgressBar(progress, color, recording):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createProgressBar: progress: %s, startHPos: %s, remainingWidth: %s" % (progress, self.startHPos, self.remainingWidth))
			x = xPos(self.MVCBarHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCBarSize.height(), self.MVCBarVPos)

			bar_pic = self.pic_progress_bar
			if recording:
				bar_pic = self.pic_rec_progress_bar
				color = self.DefaultColor

			if config.MVC.movie_progress.value == "PB":
				self.res.append((eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, x, y, self.MVCBarSize.width(), self.MVCBarSize.height(), progress, bar_pic, 1, color, self.FrontColorSel, self.BackColor, None))
				self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer
				self.remainingWidth = self.width - self.startHPos
				#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createProgressBar: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def createProgressValue(progress, color):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createProgressValue: progress: %s, startHPos: %s, remainingWidth: %s" % (progress, self.startHPos, self.remainingWidth))
			x = xPos(self.MVCProgressHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize, self.MVCProgressVPos)

			if config.MVC.movie_progress.value == "P":
				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCBarSize.width(), self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_CENTER, text="%d%%" % (progress), color=color, color_sel=self.FrontColorSel))
				self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer
				self.remainingWidth = self.width - self.startHPos
				#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createProgressValue: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def createTitle(title, ext, color):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createTitle: %s, startHPos: %s, remainingWidth: %s" % (title, self.startHPos, self.remainingWidth))
			x = xPos(self.MVCMovieHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize, self.MVCMovieVPos)
			w = self.MVCMovieWidth
			if w is None:
				w = self.remainingWidth - self.MVCDateWidth - self.MVCSpacer

			if ext in plyAll and (config.MVC.movie_progress.value == "PB" or config.MVC.movie_progress.value == "P"):
				w -= (self.MVCBarSize.width() + self.MVCSpacer)

			self.res.append(MultiContentEntryText((x, y), (w, self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_LEFT, text=title, color=color, color_sel=self.FrontColorSel))
			self.startHPos = x + w + self.MVCSpacer
			self.remainingWidth = self.width - self.startHPos
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createTitle: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def createIcon(pixmap, filetype):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createIcon: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))
			x = xPos(self.MVCIconHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCIconSize.height(), self.MVCIconVPos)

			if config.MVC.link_icons.value and filetype == TYPE_ISLINK:
				pixmap = self.pic_link

			self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCIconSize.width(), self.MVCIconSize.height()), png=pixmap, **{}))
			self.startHPos = x + self.MVCIconSize.width() + self.MVCSpacer
			self.remainingWidth = self.width - self.startHPos
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createIcon: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def createSelNum(service):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createSelNum: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

			if service in self.highlightsMov:
				selnumtxt = "-->"
			elif service in self.highlightsDel:
				selnumtxt = "X"
			elif service in self.highlightsCpy:
				selnumtxt = "+"
			elif selnum > 0:
				selnumtxt = "%02d" % selnum
			else:
				selnumtxt = None

			if selnumtxt:
				x = xPos(self.MVCIconHPos, self.startHPos)
				y = yPos(self.l.getItemSize().height(), self.MVCSelectFont.pointSize, self.MVCSelNumTxtVPos)

				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCIconSize.width(), self.l.getItemSize().height()), font=self.usedSelectFont, flags=RT_HALIGN_CENTER, text=selnumtxt))
				self.startHPos = x + self.MVCIconSize.width() + self.MVCSpacer
				self.remainingWidth = self.width - self.startHPos
				#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createSelNum: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))
			return selnumtxt

		def createPicon(service_reference):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createPicon: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))
			x = xPos(self.MVCPiconHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCPiconSize.height(), self.MVCPiconVPos)

			piconpath = getPiconPath(service_reference)

			self.res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, self.MVCPiconSize.width(), self.MVCPiconSize.height(), loadPNG(piconpath), None, None))
			self.startHPos = x + self.MVCPiconSize.width() + self.MVCSpacer
			self.remainingWidth = self.width - self.startHPos
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createPicon: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def createDateText(datetext, ext, color, recording):
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createDateText: %s, startHPos: %s, remainingWidth: %s" % (datetext, self.startHPos, self.remainingWidth))
			x = xPos(self.MVCDateHPos, self.startHPos)
			y = yPos(self.l.getItemSize().height(), self.MVCDateFont.pointSize, self.MVCDateVPos)

			halign = RT_HALIGN_LEFT

			if ext not in plyAll:
				alignment = config.MVC.count_size_position.value

				if alignment == '1':
					halign = RT_HALIGN_RIGHT
				elif alignment == '2':
					halign = RT_HALIGN_LEFT
				else:
					halign = RT_HALIGN_CENTER

			if recording:
				if self.MVCRecIconHPos is None:
					x = x + (self.MVCDateWidth - self.MVCRecIconSize.width()) / 2
				else:
					x = x + self.MVCRecIconHPos

				y = yPos(self.l.getItemSize().height(), self.MVCRecIconSize.height(), self.MVCRecIconVPos)

				self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCRecIconSize.width(), self.MVCRecIconSize.height()), png=self.pic_recording, **{}))
			else:
				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCDateWidth, self.l.getItemSize().height()), font=self.usedDateFont, text=datetext, color=color, color_sel=self.FrontColorSel, flags=halign))
			self.startHPos = x + self.MVCDateWidth + self.MVCSpacer
			self.remainingWidth = self.width - self.startHPos
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: createDateText: startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		def getDateText(path, info_value, filetype, ext):
			datetext = ""
			count, size = MovieCache.getInstance().getCountSize(path)
			counttext = "%d" % count

			size /= (1024 * 1024 * 1024)  # GB
			sizetext = "%.0f GB" % size
			if size >= 1024:
				sizetext = "%.1f TB" % size / 1024

			#print("MVC: MovieCenterGUI: getValues: count: %s, size: %s" % (count, size))
			if info_value == "C":
				datetext = "(%s)" % counttext

			if info_value == "S":
				datetext = "(%s)" % sizetext

			if info_value == "CS":
					datetext = "(%s/%s)" % (counttext, sizetext)

			if info_value == "D":
				if ext == cmtTrash:
					datetext = _("trashcan")
				elif config.MVC.directories_ontop.value:
					datetext = _("Collection")
				elif filetype == TYPE_ISLINK:
					datetext = _("Link")
				else:
					datetext = _("Directory")

			#print("MVC: MovieCenterGUI: getValues: datetext: %s" % (datetext))
			return count, datetext

		def getDirValues(path, filetype, ext):
			datetext = ""
			pixmap = self.pic_directory

			if ext == cmtUp:
				pixmap = self.pic_back
				if config.MVC.directories_info.value == "D":
					datetext = _("up")

			if ext == cmtBM:
				pixmap = self.pic_e2bookmark
				if config.MVC.directories_info.value == "D":
					datetext = _("Bookmark")

			if ext == cmtTrash:
				if config.MVC.movie_trashcan_enable.value:
					count, datetext = getDateText(path, config.MVC.movie_trashcan_info.value, filetype, ext)
					if count > 0:
						pixmap = self.pic_trashcan_full
					else:
						pixmap = self.pic_trashcan

			if ext == cmtDir:
				pixmap = self.pic_directory

				if config.MVC.directories_ontop.value:
					pixmap = self.pic_col_dir

				_count, datetext = getDateText(path, config.MVC.directories_info.value, filetype, ext)

			return datetext, pixmap

		def getFileValues(service, date, length, cut_list):

			def getFileIcon(ext):
				pixmap = self.pic_movie_default

				movieWatching = False
				movieFinished = False
				if config.MVC.movie_progress.value:
					movieWatching = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_watching_percent.value) and progress < int(config.MVC.movie_finished_percent.value)
					movieFinished = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_finished_percent.value)

				# video
				if ext in extVideo:
					if movieWatching:
						pixmap = self.pic_movie_watching
					elif movieFinished:
						pixmap = self.pic_movie_finished
					else:
						pixmap = self.pic_movie_default
				return pixmap

			pixmap = self.pic_movie_default
			progress, length, recording = self.getProgress(service, length, cut_list)

			# Check for recording only if date is within the last day
			if recording:
				datetext = "--- REC ---"
				pixmap = self.pic_movie_rec
				color = self.RecordingColor

			elif RecordingsControl.isCutting(service.getPath()):
				datetext = "--- CUT ---"
				pixmap = self.pic_movie_cut
				color = self.RecordingColor

			else:
				# Media file
				color = self.DefaultColor
				datetext = str2date(date).strftime(config.MVC.movie_date_format.value)
				if config.MVC.movie_icons.value:
					pixmap = getFileIcon(ext)

			return datetext, pixmap, color, length, progress, recording

		#print("MVC: MovieCenterGUI: buildMovieCenterEnty: itemSize.width(): %s, itemSize.height(): %s" % (self.l.getItemSize().width(), self.l.getItemSize().height()))
		progress = 0
		pixmap = None
		color = None
		datetext = None
		self.res = [None]
		self.usedFont = 1
		self.usedSelectFont = 3
		self.usedDateFont = 4
		self.startHPos = self.MVCStartHPos
		self.width = self.l.getItemSize().width() - 10
		self.remainingWidth = self.width

		if (config.MVC.movie_hide_mov.value and self.serviceMoving(service)) or (config.MVC.movie_hide_del.value and self.serviceDeleting(service)):
			return self.res

		#print("MVC: MovieCenterGUI: buildMovieCenterEntry: let's start with startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

		if ext in plyAll:
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: adjusted startHPos: %s, remainingWidth: %s" % (self.startHPos, self.remainingWidth))

			datetext, pixmap, color, length_update, progress, recording = getFileValues(service, date, length, cut_list)
			if length_update != length:
				self.updateLength(service, length_update)

			# SelNum
			selnumtxt = createSelNum(service)
			if not selnumtxt and config.MVC.movie_icons.value:
				# Icon
				createIcon(pixmap, filetype)

			if ext in extTS and config.MVC.movie_picons.value:
				# Picon
				createPicon(service_reference)

			# Title
			createTitle(title, ext, color)

			if config.MVC.movie_progress.value == "PB":
				# Progress Bar
				createProgressBar(progress, color, recording)

			if config.MVC.movie_progress.value == "P":
				# Progress
				createProgressValue(progress, color)

			if config.MVC.movie_date_format.value:
				# DateText
				createDateText(datetext, ext, color, recording)
		elif ext in [cmtBM, cmtDir, cmtTrash, cmtUp]:
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: ext: " + ext)
			# Directory
			datetext, pixmap = getDirValues(path, filetype, ext)

			if config.MVC.movie_icons.value:
				createIcon(pixmap, filetype)

			# Title
			createTitle(title, ext, self.FrontColorSel)

			# DateText
			createDateText(datetext, ext, self.FrontColorSel, False)
		else:
			#print("MVC: MovieCenterGUI: buildMovieCenterEntry: unknown ext: " + ext)
			pass
		#print("MVC: MovieCenterGUI: buildMovieCenterEntry: return")
		return self.res

	def createDirList(self, path):
		filelist = MovieCache.getInstance().getFileList([path])
		subdirlist = MovieCache.getInstance().getDirList([path])
		return subdirlist, filelist

	def reloadDirList(self, path):
		return self.createDirList(path)

	def createCustomList(self, current_path):
		customlist = []

		current_path = os.path.realpath(current_path)
		currentMountPoint = self.mountpoint(current_path)
		currentRelPath = current_path[len(currentMountPoint):]

		if current_path != "" and currentRelPath != config.MVC.movie_pathlimit.value:
			customlist.append(MovieCache.getInstance().getMovie(os.path.join(current_path, "..")))

		# Insert these entries always at last
		if current_path == os.path.realpath(config.MVC.movie_homepath.value):
			if config.MVC.movie_trashcan_enable.value and config.MVC.movie_trashcan_show.value:
				customlist.append(MovieCache.getInstance().getMovie(config.MVC.movie_trashcan_path.value))

			if config.MVC.bookmarks.value:
				bookmarks = self.getBookmarks()
				if bookmarks:
					for bookmark in bookmarks:
						customlist.append(MovieCache.getInstance().newMovieEntry(directory=os.path.dirname(bookmark), filetype=TYPE_ISDIR,
							path=bookmark, filename=os.path.basename(bookmark), ext=cmtBM, name=os.path.basename(bookmark)))
		return customlist

	def reloadInternal(self, current_path):
		#print("MVC: MovieCenterGUI: reloadInternal: current_path: " + current_path)

		customlist, subdirlist, filelist = [], [], []
		resetlist = True
		nextSort = None

		# Create listings
		if not os.path.splitext(current_path)[1]:
			# Read subdirectories and filenames
			subdirlist, filelist = self.createDirList(current_path)
			customlist = self.createCustomList(current_path)

		elif os.path.splitext(current_path)[1] in plyAll:
			# Found file
			#print("MVC: MovieCenterGUI: reloadInternal: file/recording found")
			filelist = []
			filelist.append(MovieCache.getInstance().getFile(current_path))
			resetlist = False
			current_path = None

		else:
			# Found virtual directory
			# No changes done
			return False

		# Add custom entries and sub directories to the list
		tmplist = customlist + subdirlist + filelist

		self.currentSelectionCount = 0
		self.selectionList = None

		if current_path:
			self.current_path = current_path

			if self.returnSort:
				# Restore sorting mode
				self.actualSort = self.returnSort
				self.returnSort = None

			if nextSort:
				# Backup the actual sorting mode
				if self.returnSort is None:
					self.returnSort = self.actualSort
				# Set new sorting mode
				self.actualSort = nextSort

		if resetlist:
			self.list = []
		else:
			tmplist = self.list + tmplist

		self.list = self.doListSort(tmplist)
		return self.list

	def getProgress(self, service, length, cut_list):
		# All calculations are done in seconds
		#print("MVC: MovieCenterGUI: getProgress: path: " + service.getPath())

		# first get last and length
		recording = RecordingsControl.getRecording(service.getPath(), True)
		if recording:
			begin, end, _service_ref = recording
			last = time() - begin
			length = end - begin
		else:
			# Get last position from cut file
			#print("MVC: MovieCenterGUI: getProgress: cut_list: " + str(cut_list))
			last = CutList.getCutListLastInSeconds(cut_list)
			#print("MVC: MovieCenterGUI: getProgress: last: " + str(last))

			if length <= 0:
				if service:
					length = ServiceCenter.getInstance().info(service).getLength()
					#print("MVC: MovieCenterGUI: getProgress: info.getLength(): " + str(length))
				else:
					length = CutList.getCutListLengthInSeconds(cut_list)
					#print("MVC: MovieCenterGUI: getProgress: getCutListLengthinSeconds(): " + str(length))
			#print("MVC: MovieCenterGUI: getProgress: length: " + str(length))

		# second calculate progress
		progress = 0
		if length > 0 and last > 0:
			if last > length:
				last = length
			progress = int(round(float(last) / float(length), 2) * 100)

		#print("MVC: MovieCenterGUI: getProgress: progress = %s, length = %s, recording = %s" % (progress, length, recording))
		return progress, length, recording

	def resetProgressService(self, service):
		CutList(service.getPath()).resetLastCutList()
