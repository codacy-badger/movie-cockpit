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
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from enigma import eTimer
from Components.Harddisk import Util
from Screens.TimerEdit import TimerEditList
from MountPoints import MountPoints
from MovieCache import MovieCache, IDX_PATH
from MovieCenter import MovieCenter
from MovieSelectionMenu import MovieMenu
from Bookmarks import Bookmarks
from MovieOps import MovieOps
from SkinUtils import getSkinPath
from MovieCenter import MOVIE_IDX_SERVICE
from MovieSelectionSummary import MVCSelectionSummary
from MovieSelectionEventInfo import EventInfo
from MovieSelectionMovieInfo import MovieInfo

instance = None


class MVCSelection(EventInfo, MovieInfo, Screen, HelpableScreen, MovieOps, MountPoints, Bookmarks, object):

	# Define static member variables
	def attrgetter(attr, default=None):
		def get_any(self):
			return getattr(MVCSelection, attr, default)
		return get_any

	def attrsetter(attr):
		def set_any(self, value):
			setattr(MVCSelection, attr, value)
		return set_any

	returnService = property(fget=attrgetter('_returnService'), fset=attrsetter('_returnService'))
	current_path = property(fget=attrgetter('_current_path', config.MVC.movie_homepath.value), fset=attrsetter('_current_path'))

	@staticmethod
	def getInstance():
		return instance

	def __init__(self, session, returnService=None, playerInstance=None):
		print("MVC: MovieSelection: __init__")
		global instance
		instance = self

		Screen.__init__(self, session)
		EventInfo.__init__(self)
		MountPoints.__init__(self)

		self.skinName = ["MVCSelection"]
		self.skin = Util.readFile(self.getSkin())

		self.playerInstance = playerInstance
		self.multi_select_index = None

		self.lastservice = None
		self.cursorDir = 0
		self.savedIndex = 0

		self["wait"] = Label(_("Reading directory..."))
		self["wait"].hide()

		self["space_info"] = Label("")
		self["sort_mode"] = Label("")

		self["list"] = MovieCenter()

		if returnService:
			self.returnService = returnService
			set_current_path = True
			for entry in self["list"].list:
				if entry[MOVIE_IDX_SERVICE] == self.returnService:
					set_current_path = False
					break
			if set_current_path:
				self.current_path = os.path.dirname(returnService.getPath())

		self["key_red"] = Button()
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()

		self.cover = config.MVC.cover.value

		helptext = self.initButtons()

		self["actions"] = HelpableActionMap(
			self,
			"PluginMovieSelectionActions",
			{
				"MVCOK":		(self.entrySelected, 		_("Play selected movie(s)")),
				"MVCEXIT":		(self.abort, 			_("Close plugin")),
# 				"MVCEXITpowerdown":	(self.abortAndPowerDown, 	_("Close plugin and do power button action")),
				"MVCMENU":		(self.openMenu, 		_("Open menu")),
				"MVCINFO":		(self.showEventInformation, 	_("Show event info")),
				"MVCINFOL":		(self.openInfoLong, 		_("IMDBSearch / MVC-TMDBInfo / TMDBInfo / TMBDInfo / CSFDInfo")),

				"MVCRed":		(self.redFunc, 			helptext[0]),  # redhelptext),
				"MVCGREEN":		(self.greenFuncShort, 		helptext[2]),  # greenhelptext),
				"MVCYELLOW":		(self.yellowFunc, 		helptext[4]),  # yellowhelptext),
				"MVCBLUE":		(self.blueFunc, 		helptext[6]),  # bluehelptext),

				"MVCREDL":		(self.redFuncLong, 		helptext[1]),  # redlonghelptext),
				"MVCGREENL":		(self.greenFuncLong, 		helptext[3]),  # greenlonghelptext),
				"MVCYELLOWL":		(self.yellowFuncLong, 		helptext[5]),  # yellowlonghelptext),
				"MVCBlueL":		(self.blueFuncLong, 		helptext[7]),  # bluelonghelptext),

				"MVCLeft":		(self.pageUp, 			_("Move cursor page up")),
				"MVCRight":		(self.pageDown, 		_("Move cursor page down")),
				"MVCUp":		(self.moveUp, 			_("Move cursor up")),
				"MVCDown":		(self.moveDown, 		_("Move cursor down")),
				"MVCBqtPlus":		(self.bqtPlus, 			_("Move cursor to the top / Move cursor x entries up / Switch Folders in Movie Home (up)")),
				"MVCBqtMnus":		(self.bqtMnus, 			_("Move cursor to the end / Move cursor x entries down / Switch Folders in Movie Home (down)")),

				"MVCVIDEOB":		(self.toggleSelectionList, 	_("Toggle service selection")),
				"MVCVIDEOL":		(self.resetSelectionList, 	_("Remove service selection")),
				"MVCAUDIO":		(self.openMenuPlugins, 		_("Available plugins menu")),
				"MVCTV":		(self.openTimerList, 		_("Open Timer List")),
				"MVCRADIO":		(self.resetProgress, 		_("Reset movie progress")),
				"MVCTEXT":		(self.multiSelect, 		_("Start / end multiselection")),
				"0":			(self.MVCKey0, 			_("Movie home")),
			},
			prio=-3  # give them a little more priority to win over base class buttons
		)
		self["actions"].csel = self

		HelpableScreen.__init__(self)

		if self.current_path is None:
			self.current_path = config.MVC.movie_homepath.value
		self.last_current_path = None
		self.selection_list = []		# Used for file operations
		self.hide_miniTV = False

		# Key press short long handling
		#TODO We have to rework this key press handling in order to allow different user defined color key functions
		self.toggle = True		# Used for long / short key press detection: Toggle sort mode / order, Toggle selection / reset selection
		self.move = True

		self.delayTimer = eTimer()
		self.delayTimer_conn = self.delayTimer.timeout.connect(self.updateInfoDelayed)

		self.coverTimer = eTimer()
		self.coverTimer_conn = self.coverTimer.timeout.connect(self.showCoverDelayed)

		self.onShow.append(self.onDialogShow)
		self.onHide.append(self.onDialogHide)
		self["list"].onSelectionChanged.append(self.selectionChanged)

	def getSkin(self):
		if config.MVC.skinstyle.value == "right":
			skin = getSkinPath("Selection_right.xml")
		elif config.MVC.skinstyle.value == "rightpig":
			skin = getSkinPath("Selection_right_pig.xml")
		else:
			skin = getSkinPath("Selection_myskin.xml")
		return skin

	def createSummary(self):
		return MVCSelectionSummary

	def openTimerList(self):
		self.checkHideMiniTV_beforeFullscreen()
		self.session.open(TimerEditList)

	def callHelpAction(self, *args):
		HelpableScreen.callHelpAction(self, *args)
		self.checkHideMiniTV_beforeFullscreen()

	def abort(self):
		if config.MVC.MVCStartHome.value == "true":
			# Reload only if path is not movie home
			if self.current_path != config.MVC.movie_homepath.value:
				# we want only to homepath if we close the list when no file is played in background
				if self.playerInstance is None:
					self.current_path = config.MVC.movie_homepath.value
					config.MVC.needsreload.value = True

#		config.av.policy_43.cancel() # reload the default setting

		# Movie preview
		# Restore last service only if no player is active
		if self.lastservice:
			self.session.nav.playService(self.lastservice)
			self.lastservice = None
		self.miniTV_unmute()

		if self.delayTimer.isActive():
			self.delayTimer.stop()
		if self.coverTimer.isActive():
			self.coverTimer.stop()

		# reset selected Files List, to reopen the list without the last selected
		self.resetSelectionList()
		self.close()

	def redFunc(self):
		self.execblueyellowbutton(config.MVC.movie_redfunc.value)

	def greenFuncShort(self):
		if config.MVC.movie_greenfunc.value != "ST":
			self.execblueyellowbutton(config.MVC.movie_greenfunc.value)
		else:
			self.toggleSortMode()

	def yellowFunc(self):
			self.execblueyellowbutton(config.MVC.movie_yellowfunc.value)

	def blueFunc(self):
			self.execblueyellowbutton(config.MVC.movie_bluefunc.value)

	def redFuncLong(self):
		self.execblueyellowbutton(config.MVC.movie_longredfunc.value)

	def greenFuncLong(self):
		if config.MVC.movie_greenfunc.value != "ST":
			self.execblueyellowbutton(config.MVC.movie_greenfunc.value)
		else:
			self.toggleSortOrder()

	def yellowFuncLong(self):
		self.execblueyellowbutton(config.MVC.movie_longyellowfunc.value)

	def blueFuncLong(self):
		self.execblueyellowbutton(config.MVC.movie_longbluefunc.value)

	def execblueyellowbutton(self, value):
		if value == "MH":
			self.returnService = None
			self["list"].resetSorting()
			self.changeDir(config.MVC.movie_homepath.value)
		elif value == "DL":
			self.deleteFile()
		elif value == "MV":
			self.moveMovie()
		elif value == "CS":
			self.imdb()
		elif value == "MI":
			self.MVCTMDBInfo()
		elif value == "CP":
			self.copyMovie()
		elif value == "E2":
			self.openBookmarks()
		elif value == "TC":
			self.toggleCover()

	def bqtPlus(self):
		if config.MVC.bqt_keys.value == "":
			self.moveTop()
		elif config.MVC.bqt_keys.value == "Skip":
			self.moveSkipUp()
		elif config.MVC.bqt_keys.value == "Folder":
			self.bqtNextFolder()

	def bqtMnus(self):
		if config.MVC.bqt_keys.value == "":
			self.moveEnd()
		elif config.MVC.bqt_keys.value == "Skip":
			self.moveSkipDown()
		elif config.MVC.bqt_keys.value == "Folder":
			self.bqtPrevFolder()

	def bqtNextFolder(self):
		dirlist = self.bqtListFolders()
		if len(dirlist) > 0:
			try:
				pos = (dirlist.index(self.current_path) + 1) % len(dirlist)
			except Exception:
				pos = 0
			self.setNextPath(dirlist[pos])

	def bqtPrevFolder(self):
		dirlist = self.bqtListFolders()
		if len(dirlist) > 0:
			try:
				pos = (dirlist.index(self.current_path) - 1) % len(dirlist)
			except Exception:
				pos = len(dirlist) - 1
			self.setNextPath(dirlist[pos])

	def bqtListFolders(self):
		movie_homepath = os.path.realpath(config.MVC.movie_homepath.value)
		dirs = MovieCache.getInstance().getDirList(movie_homepath)
		dirlist = []
		for adir in dirs:
			dirlist.append(adir[IDX_PATH])
		dirlist.sort()
		return dirlist

	def changeDir(self, path, service=None):
		self.returnService = service
		self.reloadList(path)

	def reloadListWithoutCache(self):
		# reload files and directories for current path without using cache
		MovieCache.getInstance().reloadDatabase()
		self.reloadList(self.current_path)

	def MVCKey0(self):
		# Movie home
		if not self.isBookmark(self.current_path):
			self.changeDir(config.MVC.movie_homepath.value)

	def directoryUp(self):
		if self.current_path != "" and self.current_path != "/":
			# Open parent folder
			self.setNextPath()
		else:
			# Move cursor to top of the list
			self.moveTop()

	def setNextPath(self, nextdir=None, service=None):
		if nextdir == ".." or nextdir is None or nextdir.endswith(".."):
			if self.current_path != "" and self.current_path != "/":
				# Open Parent folder
				service = self["list"].getCurrent()
				nextdir = os.path.dirname(self.current_path)
				self.changeDir(nextdir, service)
		return

	def getSelectionList(self):
		if self.multi_select_index:
			self.multi_select_index = None
			self.updateTitle()
		self.toggle = False
		self.selection_list = self["list"].getSelectionList()[:]
		return self.selection_list

	def getCurrent(self):
		return self["list"].getCurrent()

	def moveUp(self):
		print("MVC: MovieSelection: moveUp")
		self.cursorDir = -1
		self["list"].moveUp()
		self.updateAfterKeyPress()

	def moveDown(self):
		print("MVC: MovieSelection: moveDown")
		self.cursorDir = 1
		self["list"].moveDown()
		self.updateAfterKeyPress()

	def pageUp(self):
		self.cursorDir = 0
		self["list"].pageUp()
		self.updateAfterKeyPress()

	def pageDown(self):
		self.cursorDir = 0
		self["list"].pageDown()
		self.updateAfterKeyPress()

	def moveTop(self):
		self["list"].moveTop()
		self.updateAfterKeyPress()

	def moveSkipUp(self):
		self.cursorDir = -1
		for _i in range(int(config.MVC.list_skip_size.value)):
			self["list"].moveUp()
		self.updateAfterKeyPress()

	def moveSkipDown(self):
		self.cursorDir = 1
		for _i in range(int(config.MVC.list_skip_size.value)):
			self["list"].moveDown()
		self.updateAfterKeyPress()

	def moveEnd(self):
		self["list"].moveEnd()
		self.updateAfterKeyPress()

	def multiSelect(self, index=-1):
		if index == -1:
			# User pressed the multiselect key
			if self.multi_select_index is None:
				# User starts multiselect
				index = self.getCurrentIndex()
				# Start new list with first selected item index
				self.multi_select_index = [index]
				# Toggle the first selected item
				self["list"].toggleSelection(index=index)
			else:
				# User stops multiselect
				# All items are already toggled
				self.multi_select_index = None
			self.updateTitle()
		else:
			if self.multi_select_index:
				# Multiselect active
				firstIndex = self.multi_select_index[0]
				lastIndex = self.multi_select_index[-1]
				# Calculate step : selection and range step +1/-1 -> indicates the direction
				selStep = 1 - 2 * (firstIndex > lastIndex)  # >=
				rngStep = 1 - 2 * (lastIndex > index)
				if selStep == rngStep or firstIndex == lastIndex:
					start = lastIndex + rngStep
					end = index + rngStep
				elif index not in self.multi_select_index:
					start = lastIndex
					end = index + rngStep
				else:
					start = lastIndex
					end = index
				# Range from last selected to cursor position (both are included)
				for i in xrange(start, end, rngStep):
					if self.multi_select_index[0] == i:
						# Never untoggle the first index
						continue  # pass
					elif i not in self.multi_select_index:
						# Append index
						self.multi_select_index.append(i)
						# Toggle
						self["list"].toggleSelection(index=i)
					else:
						# Untoggle
						self["list"].toggleSelection(index=i)
						# Remove index
						self.multi_select_index.remove(i)
			else:
				print("MVC: MovieSelection: multiSelect: Not active")

	def openBookmarks(self):
		self.selectDirectory(
			self.openBookmarksCallback,
			_("Bookmarks") + ":"
		)

	def openBookmarksCallback(self, path=None):
		if path:
			self.changeDir(path)

	def menuCallback(self, function=None):
		from MovieSelectionMenu import FUNC_IDX_MOVIE_HOME, FUNC_IDX_DIR_UP, FUNC_IDX_RELOAD_WITHOUT_CACHE, FUNC_IDX_DELETE,\
			FUNC_IDX_DELETE_PERMANENTLY, FUNC_IDX_EMPTY_TRASHCAN, FUNC_IDX_OPEN_TRASHCAN, FUNC_IDX_SELECT_ALL,\
			FUNC_IDX_COPY, FUNC_IDX_MOVE, FUNC_IDX_RELOAD, FUNC_IDX_REMOVE_MARKER, FUNC_IDX_DELETE_CUTLIST
		if function == FUNC_IDX_MOVIE_HOME:
			self.changeDir(config.MVC.movie_homepath.value)
		elif function == FUNC_IDX_COPY:
			self.copyMovie()
		elif function == FUNC_IDX_MOVE:
			self.moveMovie()
		elif function == FUNC_IDX_RELOAD:
			self.initList()
		elif function == FUNC_IDX_OPEN_TRASHCAN:
			self.changeDir(config.MVC.movie_trashcan_path.value)
		elif function == FUNC_IDX_DELETE_PERMANENTLY or function == FUNC_IDX_DELETE:
			self.deleteFile(function == FUNC_IDX_DELETE_PERMANENTLY)
		elif function == FUNC_IDX_DIR_UP:
			self.directoryUp()
		elif function == FUNC_IDX_SELECT_ALL:
			self.markAll()
		elif function == FUNC_IDX_EMPTY_TRASHCAN:
			self.emptyTrashcan()
		elif function == FUNC_IDX_RELOAD_WITHOUT_CACHE:
			self.reloadListWithoutCache()
		elif function == FUNC_IDX_REMOVE_MARKER:
			self.removeCutListMarker()
		elif function == FUNC_IDX_DELETE_CUTLIST:
			self.deleteCutListFile()
		else:
			print("MVC: MovieSelection: menuCallback: unknown function: %s" % function)

	def openMenu(self):
		self.savedIndex = self.getCurrentIndex()
		self.checkHideMiniTV_beforeFullscreen()
		self.session.openWithCallback(
			self.menuCallback,
			MovieMenu,
			"functions",
			self.getCurrent(),
			self["list"].getSelectionList(),
			self.current_path
		)

	def openMenuPlugins(self):
		if self["list"].currentSelIsPlayable():
			self.checkHideMiniTV_beforeFullscreen()
			self.session.openWithCallback(
				self.menuCallback,
				MovieMenu,
				"plugins",
				self.getCurrent(),
				self["list"].getSelectionList(),
				self.current_path
			)

	def markAll(self):
		for i in xrange(len(self["list"])):
			self["list"].toggleSelection(index=i)

	def updateAfterKeyPress(self):
		if self.returnService:
			# Service was stored for a pending update,
			# but user wants to move, copy, delete it,
			# so we have to update returnService
			if self.selection_list:
				self.returnService = self.getNextSelectedService(self.getCurrent())

	def selectionChanged(self):
#		print("MVC: MovieSelection: selectionChanged")
		if self.multi_select_index:
			self.multiSelect(self.getCurrentIndex())
		self.updateInfo()

	def updateInfo(self):
		print("MVC: MovieSelection: updateInfo")
		self.resetInfo()
		self.delayTimer.start(int(config.MVC.movie_descdelay.value), True)
		if self.already_shown and self.shown:
			if config.MVC.cover.value:
				self.coverTimer.start(int(config.MVC.cover_delay.value), True)

	def updateInfoDelayed(self):
		self.updateTitle()
		current = self.getCurrent()
		if current and not self["list"].serviceMoving(current) and not self["list"].serviceDeleting(current):
			self.updateEventInfo(current)

	def resetInfo(self):
#		print("MVC: MovieSelection: resetInfo")
		if self.delayTimer.isActive():
#			print("MVC: MovieSelection: delayTimer.stop()")
			self.delayTimer.stop()
		if self.coverTimer.isActive():
#			print(("MVC: MovieSelection: coverTimer.stop()"))
			self.coverTimer.stop()

		self.updateTitle()
		self.updateEventInfo(None)

		if self.already_shown and self.shown:
			if config.MVC.cover.value:
				self.showCover(None)

	def showCoverDelayed(self):
#		print("MVC: MovieSelection: showCoverDelayed")
		self.showCover(self.getCurrent())

	def updateSpaceInfo(self):
		space_info = ""
		for mount, space_used in MountPoints.space_used_percent:
			if space_info != "":
				space_info += ", "
			space_info += mount + ": " + space_used
		self["space_info"].setText(space_info)

	def updateTitle(self):
		if self.multi_select_index:
			self.setTitle(_("MULTI-SELECTION"))
			return

		title = "MovieCockpit: "
		# Display the current path
		if self.current_path == config.MVC.movie_trashcan_path.value:
			title += _("trashcan")
		else:
			title += _("Recordings")
		self.setTitle(title)

		# Display the actual sorting mode
		from ConfigInit import sort_modes
		actsort = self["list"].getSorting()
		for _k, v in sort_modes.items():
			if v[0] == actsort:
				sort_mode = _("Sort Mode") + ": " + v[1]
				break
		self["sort_mode"].setText(sort_mode)

		self.updateSpaceInfo()

	def toggleCover(self):
		if config.MVC.cover.value:
			if self.cover:
				self.cover = False
				self.hideCover()
			else:
				self.cover = True
				self["Cover"].show()
				self["CoverBg"].show()
		self.initButtons()

	def toggleSortMode(self):
		#WORKAROUND E2 doesn't send dedicated short or long pressed key events
		if self.toggle is False:
			self.toggle = True
		else:
			self["list"].toggleSortingMode()
			self.moveTop()
			self.updateInfo()

	def toggleSortOrder(self):
		self.toggle = False
		self["list"].toggleSortingOrder()
		self.moveTop()
		self.updateInfo()

	def toggleSelectionList(self):
		#WORKAROUND E2 doesn't send dedicated short or long pressed key events
		if self["list"].currentSelIsDirectory():
			self.moveFile()
		else:
			if self.toggle is False:
				self.toggle = True
			else:
				if self["list"].currentSelIsPlayable():
					self["list"].toggleSelection()
				# Move cursor
				if config.MVC.moviecenter_selmove.value != "o":
					if self.cursorDir == -1 and config.MVC.moviecenter_selmove.value == "b":
						self.moveToIndex(max(self.getCurrentIndex() - 1, 0))
					else:
						self.moveToIndex(min(self.getCurrentIndex() + 1, len(self["list"]) - 1))

	def resetSelectionList(self):
		selection_list = self.getSelectionList()
		if selection_list:
			for service in selection_list:
				self["list"].unselectService(service)

	def resetProgress(self):
		selection_list = self.getSelectionList()
		for service in selection_list:
			self["list"].resetProgressService(service)

		self.returnService = self.getCurrent()
		self.reloadList(self.current_path)
		self.setReturnCursor()

#	def openBludiscPlayer(self, blupath):
#		try:
#			from Plugins.Extensions.BludiscPlayer.plugin import BludiscMenu
#			self.checkHideMiniTV_beforeFullscreen()
#			self.session.open(BludiscMenu, bd_mountpoint=blupath)
#		except ImportError:
#			self.checkHideMiniTV_beforeFullscreen()
#			self.session.open(MessageBox, "Plugin not found", MessageBox.TYPE_ERROR)

	def initCursor(self, ifunknown=True):
		if self.returnService:
			# Move to next or last selected entry
			self.moveToService(self.returnService)
			self.returnService = None
		elif ifunknown and self.playerInstance:
			# Get current service from movie player
			service = self.playerInstance.currentlyPlayedMovie()
			self.moveToService(service)
		elif ifunknown:
			# Select first entry
			print("MVC: MovieSelection: initCursor: movetop")
			self.moveTop()

		self.updateInfo()

	def setReturnCursor(self):
		self.moveToService(self.returnService)

	def isCurrentlySeekable(self):
		service = self.session.nav.getCurrentService()
		is_seekable = False
		if service:
			seek = service.seek()
			if seek:
				is_seekable = seek.isCurrentlySeekable()
		return is_seekable

	def onDialogShow(self):
		self.lastservice = self.lastservice or self.session.nav.getCurrentlyPlayingServiceReference()

		self.controlMiniTV()  # turn miniTV off if appropriate
		self.initButtons()

		if config.MVC.needsreload.value:
			config.MVC.needsreload.value = False
			self["list"].resetSorting()
			self.initList()

		if len(self["list"]) == 0:
			self.initList()
		else:
			if config.MVC.needsreload.value:
				self.updateInfo()
			else:
				if self.returnService and self.returnService != self.getCurrent():
					self.initList()
				else:
					self.initCursor(False)   # we need it only if "config.MVC.needsreload.value" is False ! But False from begin !
					self.updateInfo()

	def onDialogHide(self):
		if self.playerInstance:
			self.returnService = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.returnService = self.getCurrent()

	def getCurrentIndex(self):
		return self["list"].getCurrentIndex()

	def moveToIndex(self, index):
		self.multi_select_index = None
		self["list"].moveToIndex(index)
		self.updateInfo()

	def moveToService(self, service):
		self.multi_select_index = None
		self["list"].moveToService(service)
		self.updateInfo()

	def removeService(self, service):
		self["list"].removeService(service)

	def removeServiceOfType(self, service, ptype):
		self["list"].removeServiceOfType(service, ptype)

	def getNextSelectedService(self, current, selectedlist=None):
		if selectedlist is None:
			selectedlist = self.selection_list
		service = self["list"].getNextSelectedService(current, selectedlist)
		self.selection_list = []
		return service

	def loading(self, loading=True):
		if loading:
			self["list"].hide()
			self["wait"].show()
		else:
			self["wait"].hide()
			self["list"].show()

	def initButtons(self):
		def setKeyText(key_config_value, keyhelptext):
			if key_config_value == "TC":
				if config.MVC.cover.value:
					if self.cover:
						keytext = _("Hide Cover")
					else:
						keytext = _("Show Cover")
				else:
					keytext = _("Button disabled")
					keyhelptext = _("Cover disabled in Setup")
			else:
				keytext = keyhelptext
			return keytext, keyhelptext

		# Green button
		if config.MVC.movie_greenfunc.value == "ST":
			greenhelptext = _("Sort Mode")
			greentext = _("Sort Mode")
			greenlonghelptext = _("Sort Order")
		else:
			greentext = config.MVC.movie_greenfunc.description[config.MVC.movie_greenfunc.value]
			greenhelptext = greentext
			greenlonghelptext = greentext
		self["key_green"].text = greentext

		# Red button
		redhelptext = config.MVC.movie_redfunc.description[config.MVC.movie_redfunc.value]
		redlonghelptext = config.MVC.movie_longredfunc.description[config.MVC.movie_longredfunc.value]
		redtext, redhelptext = setKeyText(config.MVC.movie_redfunc.value, redhelptext)
		self["key_red"].text = redtext

		# Yellow button
		yellowhelptext = config.MVC.movie_yellowfunc.description[config.MVC.movie_yellowfunc.value]
		yellowlonghelptext = config.MVC.movie_longyellowfunc.description[config.MVC.movie_longyellowfunc.value]
		yellowtext, yellowhelptext = setKeyText(config.MVC.movie_yellowfunc.value, yellowhelptext)
		self["key_yellow"].text = yellowtext

		# Blue button
		bluehelptext = config.MVC.movie_bluefunc.description[config.MVC.movie_bluefunc.value]
		bluelonghelptext = config.MVC.movie_longbluefunc.description[config.MVC.movie_longbluefunc.value]
		bluetext, bluehelptext = setKeyText(config.MVC.movie_bluefunc.value, bluehelptext)
		self["key_blue"].text = bluetext

		helptext = [redhelptext, redlonghelptext, greenhelptext, greenlonghelptext, yellowhelptext, yellowlonghelptext, bluehelptext, bluelonghelptext]
		return helptext

	def initList(self):
		self.initPig()
		self.reloadList()

	def reloadList(self, path=None):
		self.returnService = self.getNextSelectedService(self.getCurrent())
		if path is None:
			path = self.current_path

		self.multi_select_index = None
		self.resetInfo()
		if config.MVC.moviecenter_loadtext.value:
			self.loading()

		if self["list"].reload(path):
			self.current_path = path
			self.initButtons()
			self.initCursor()

		if config.MVC.moviecenter_loadtext.value:
			self.loading(False)
		self.updateInfo()

	def openPlayer(self, playlist):
		# Force update of event info after playing movie
		self.resetInfo()
		self.loading(False)
		self.miniTV_unmute()
		# Start Player
		print("MVC: MovieSelection: openPlayer: self.playerInstance: " + str(self.playerInstance))
		if self.playerInstance is None:
			print("MVC: MovieSelection: openPlayer: self.close(playlist, lastservice)")
			self.close(playlist, self.lastservice)
		else:
			print("MVC: MovieSelection: openPlayer: self.close()")
			self.close()

	def entrySelected(self):
		current = self.getCurrent()
		if current:
			if self["list"].currentSelIsVirtual():
				# Open folder and reload movielist
				self.setNextPath(self["list"].getCurrentSelDir())
			else:
				if not self["list"].serviceMoving(current) and not self["list"].serviceDeleting(current):
					self.openPlayer([current])
				else:
					self.checkHideMiniTV_beforeFullscreen()
					self.session.open(
						MessageBox,
						_("File not available"),
						MessageBox.TYPE_ERROR,
						10
					)
