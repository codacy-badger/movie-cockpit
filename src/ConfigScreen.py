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
from Components.config import config, getConfigListEntry, configfile
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from enigma import eTimer
from Components.Harddisk import Util
from ConfigList import ConfigListScreen
from Version import VERSION
from plugin import setEPGLanguage
from SkinUtils import getSkinPath
from Trashcan import Trashcan


class ConfigScreen(ConfigListScreen, Screen, Trashcan, object):
	skin = Util.readFile(getSkinPath("ConfigScreen.xml"))

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "ConfigScreenMenu"

		self["actions"] = ActionMap(
			["SetupActions", "OkCancelActions", "MVCConfigActions"],
			{
				"ok": self.keyOK,
				"cancel": self.keyCancel,
				"red": self.keyCancel,
				"up": self.keyUp,
				"down": self.keyDown,
				"green": self.keySaveNew,
	#			"bluelong": self.loadPredefinedSettings,
				"blueshort": self.loadDefaultSettings,
				"nextBouquet": self.keyPreviousSection,
				"prevBouquet": self.keyNextSection,
			},
			-2  # higher priority
		)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_blue"] = Button(_("Defaults"))
		self["help"] = StaticText()

		self.list = []
		self.MVCConfig = []
		ConfigListScreen.__init__(self, self.list, on_change=self.changedEntry)
		self.needsRestartFlag = False
		self.defineConfig()
		self.createConfig()

		self.reloadTimer = eTimer()
		self.reloadTimer_conn = self.reloadTimer.timeout.connect(self.createConfig)

		# Override selectionChanged because our config tuples have a size bigger than 2
		def selectionChanged():
			current = self["config"].getCurrent()
			if self["config"].current != current:
				if self["config"].current:
					try:
						self["config"].current[1].onDeselect()
					except Exception:
						pass
				if current:
					try:
						current[1].onSelect()
					except Exception:
						pass
				self["config"].current = current
			for x in self["config"].onSelectionChanged:
				try:
					x()
				except Exception:
					pass
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)

	def defineConfig(self):
		self.section = 400 * "¯"
		#    _config list entry
		#    _                                                      , config element
		#          _                                                ,                                      , function called on save
		#          _                                                ,                                      ,                       , function called if user has pressed OK
		#          _                                                ,                                      ,                       ,                      , usage setup level from E2
		#          _                                                ,                                      ,                       ,                      ,   0: simple+
		#          _                                                ,                                      ,                       ,                      ,   1: intermediate+
		#          _                                                ,                                      ,                       ,                      ,   2: expert+
		#          _                                                ,                                      ,                       ,                      ,       , depends on relative parent entries
		#          _                                                ,                                      ,                       ,                      ,       ,   parent config value < 0 = true
		#          _                                                ,                                      ,                       ,                      ,       ,   parent config value > 0 = false
		#          _                                                ,                                      ,                       ,                      ,       ,             , _context sensitive help text
		#          _                                                ,                                      ,                       ,                      ,       ,             ,                                                         ,
		#       _ 0                                                 , 1                                    , 2                     , 3                    , 4     , 5           , 6                                                       ,
		self.MVCConfig = [
			(self.section                                       , _("GENERAL")                        , None                  , None                  , 0     , []          , ""),
			(_("About")                                         , config.MVC.fake_entry               , None                  , self.showInfo         , 0     , []          , _("HELP About")),
			(_("Disable plugin")                                , config.MVC.ml_disable               , self.needsRestart     , None                  , 1     , []          , _("Help Disable Plugin")),
			(_("Start plugin with")                             , config.MVC.movie_launch             , self.launchListSet    , None                  , 0     , []          , _("Help Start plugin with")),
			(_("Show plugin config in extensions menu")         , config.MVC.extmenu_plugin           , self.needsRestart     , None                  , 0     , []          , _("Help Show plugin config in extensions menu")),
			(_("Show plugin in extensions menu")                , config.MVC.extmenu_list             , self.needsRestart     , None                  , 0     , []          , _("Help Show plugin in extensions menu")),
			(_("Movie home at start")                           , config.MVC.MVCStartHome             , None                  , None                  , 0     , []          , _("Help Movie home at start")),
			(_("Default sort mode")                             , config.MVC.moviecenter_sort         , None                  , None                  , 0     , []          , _("Help Sort mode at startup")),
			(_("Movie home home path")                          , config.MVC.movie_homepath           , self.validatePath     , self.openLocationBox  , 0     , []          , _("Help Movie home home path")),
			(_("Path access limit")                             , config.MVC.movie_pathlimit          , None                  , None                  , 1     , []          , _("Help Path access limit")),
			(_("Display directory reading text")                , config.MVC.moviecenter_loadtext     , None                  , None                  , 1     , []          , _("Help Display directory reading text")),
			(self.section                                       , _("KEYMAPPING")                     , None                  , None                  , 0     , []          , ""),
			(_("Bouquet buttons behaviour")                     , config.MVC.bqt_keys                 , None                  , None                  , 0     , []          , _("Help Bouquet buttons behaviour")),
			(_("List entries to skip")                          , config.MVC.list_skip_size           , None                  , None                  , 0     , []          , _("Help List entries to skip")),
			(_("Red button function")                           , config.MVC.movie_redfunc            , None                  , None                  , 0     , []          , _("Help Red button function")),
			(_("Long Red button function")                      , config.MVC.movie_longredfunc        , None                  , None                  , 0     , []          , _("Help Long Red button function")),
			(_("Yellow button function")                        , config.MVC.movie_yellowfunc         , None                  , None                  , 0     , []          , _("Help Yellow button function")),
			(_("Long Yellow button function")                   , config.MVC.movie_longyellowfunc     , None                  , None                  , 0     , []          , _("Help Long Yellow button function")),
			(_("Blue button function")                          , config.MVC.movie_bluefunc           , None                  , None                  , 0     , []          , _("Help Blue button function")),
			(_("Long Blue button function")                     , config.MVC.movie_longbluefunc       , None                  , None                  , 0     , []          , _("Help Long Blue button function")),
			(_("LongInfo Button")                               , config.MVC.InfoLong                 , None                  , None                  , 0     , []          , _("Help LongInfo Button")),
			(self.section                                       , _("PLAYBACK")                       , None                  , None                  , 0     , []          , ""),
			(_("No resume below 10 seconds")                    , config.MVC.movie_ignore_firstcuts   , None                  , None                  , 1     , []          , _("Help No resume below 10 seconds")),
			(_("Jump to first mark when playing movie")         , config.MVC.movie_jump_first_mark    , None                  , None                  , 1     , []          , _("Help Jump to first mark when playing movie")),
			(_("Rewind finished movies before playing")         , config.MVC.movie_rewind_finished    , None                  , None                  , 1     , []          , _("Help Rewind finished movies before playing")),
			(_("Zap to channel after record EOF")               , config.MVC.record_eof_zap           , None                  , None                  , 1     , []          , _("Help Zap to channel after record EOF")),
			(_("Re-open list after stop")                       , config.MVC.movie_reopen             , None                  , None                  , 1     , []          , _("Help Re-open list after STOP-press")),
			(_("Re-open list after movie end")                  , config.MVC.movie_reopenEOF          , None                  , None                  , 1     , []          , _("Help Re-open list after Movie end")),
			(_("Leave movie with Exit")                         , config.MVC.movie_exit               , None                  , None                  , 0     , []          , _("Help Leave Movie with Exit")),
			(_("Automatic timers list cleaning")                , config.MVC.timer_autoclean          , None                  , None                  , 1     , []          , _("Help Automatic timers list cleaning")),
			(self.section                                       , _("DISPLAY-SETTINGS")               , None                  , None                  , 0     , []          , ""),
			(_("Show directories")                              , config.MVC.directories_show         , None                  , None                  , 0     , []          , _("Help Show directories")),
			(_("Show directories within movielist")             , config.MVC.directories_ontop        , None                  , None                  , 0     , [-1]        , _("Help Show directories within movielist")),
			(_("Show directories information")                  , config.MVC.directories_info         , None                  , None                  , 0     , [-2]        , _("Help Show directories information")),
			(_("Hide movies being moved")                       , config.MVC.movie_hide_mov           , None                  , None                  , 1     , []          , _("Help Hide movies being moved")),
			(_("Hide movies being deleted")                     , config.MVC.movie_hide_del           , None                  , None                  , 1     , []          , _("Help Hide movies being deleted")),
			(_("Cursor predictive move after selection")        , config.MVC.moviecenter_selmove      , None                  , None                  , 0     , []          , _("Help Cursor predictive move after selection")),
			(_("Show bookmarks in movielist")                   , config.MVC.bookmarks                , None                  , None                  , 0     , []          , _("Help Show Bookmarks in movielist")),
			(_("Description field update delay")                , config.MVC.movie_descdelay          , None                  , None                  , 2     , []          , _("Help Description field update delay")),
			(self.section                                       , _("SKIN-SETTINGS")                  , None                  , None                  , 0     , []          , ""),
			(_("Skin style (needs reopen)")                     , config.MVC.skinstyle                , None                  , None                  , 0     , []          , _("Help Skin style (needs reopen)")),
			(_("Date format")                                   , config.MVC.movie_date_format        , None                  , None                  , 0     , []          , _("Help Date format")),
			(_("Horizontal alignment for count/size")	    , config.MVC.count_size_position      , None                  , None                  , 0     , []          , _("Help Horizontal alignment for count / size")),
			(_("Show movie icons")                              , config.MVC.movie_icons              , None                  , None                  , 0     , []          , _("Help Show movie icons")),
			(_("Show link arrow")                               , config.MVC.link_icons               , None                  , None                  , 0     , [-1]        , _("Help Show link arrow")),
			(_("Show movie picons")                             , config.MVC.movie_picons             , None                  , None                  , 0     , []          , _("Help Show movie picons")),
			(_("Path to movie picons")                          , config.MVC.movie_picons_path        , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Help Path to movie picons")),
			(_("Show movie progress")                           , config.MVC.movie_progress           , None                  , None                  , 0     , []          , _("Help Show movie progress")),
			(_("Short watching percent")                        , config.MVC.movie_watching_percent   , None                  , None                  , 0     , [-1]        , _("Help Short watching percent")),
			(_("Finished watching percent")                     , config.MVC.movie_finished_percent   , None                  , None                  , 0     , [-2]        , _("Help Finished watching percent")),
			(_("Default color for recording movie")             , config.MVC.color_recording          , None                  , None                  , 0     , [-3]        , _("Help Default color recording")),
			(_("Default color for highlighted movie")           , config.MVC.color_highlight          , None                  , None                  , 0     , [-4]        , _("Help Default color highlighted")),
			(_("Hide MiniTV")                                   , config.MVC.hide_miniTV              , None                  , None                  , 0     , []          , _("Help hide_MiniTV")),
			(self.section                                       , _("COVER DISPLAY")                  , None                  , None                  , 0     , []          , ""),
			(_("Show Cover")                                    , config.MVC.cover                    , None                  , None                  , 0     , []          , _("Help Show Cover")),
			(_("Cover delay in ms")                             , config.MVC.cover_delay              , None                  , None                  , 0     , [-1]        , _("Help Cover delay in ms")),
			(_("Cover background")                              , config.MVC.cover_background         , None                  , None                  , 0     , [-2]        , _("HELP_Cover background")),
			(_("Show fallback cover")                           , config.MVC.cover_fallback           , None                  , None                  , 0     , [-3]        , _("Help Cover fallback")),
			(_("Hide MiniTV if Cover is shown")                 , config.MVC.cover_hide_miniTV        , None                  , None                  , 0     , [-4]        , _("Help Cover hide_MiniTV")),
			(self.section                                       , _("COVER SEARCH")                   , None                  , None                  , 0     , []          , ""),
			(_("Cover language")                                , config.MVC.cover_language           , None                  , None                  , 0     , []          , _("Help Cover language")),
			(_("Cover size")                                    , config.MVC.cover_size               , None                  , None                  , 0     , []          , _("Help Cover size")),
			(_("Cover automatic selection")                     , config.MVC.cover_auto_selection     , None                  , None                  , 0     , []          , _("Help Cover auto selection")),
			(_("Cover in flash")                                , config.MVC.cover_flash              , None                  , None                  , 0     , []          , _("Help Cover in flash")),
			(_("Cover bookmark")                                , config.MVC.cover_bookmark           , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Help Cover bookmark")),
			(self.section                                       , _("TRASHCAN")                       , None                  , None                  , 0     , []          , ""),
			(_("Trashcan enable")                               , config.MVC.movie_trashcan_enable    , self.activateTrashcan , None                  , 0     , []          , _("Help Trashcan enable")),
			(_("Trashcan path")                                 , config.MVC.movie_trashcan_path      , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Help Trashcan path")),
			(_("Show trashcan directory")                       , config.MVC.movie_trashcan_show      , None                  , None                  , 0     , [-2]        , _("Help Show trashcan directory")),
			(_("Show trashcan information")                     , config.MVC.movie_trashcan_info      , None                  , None                  , 0     , [-3, -1]    , _("Help Dynamic trashcan")),
			(_("Delete validation")                             , config.MVC.movie_delete_validation  , None                  , None                  , 0     , [-4]        , _("Help Delete validation")),
			(_("Enable auto trashcan cleanup")                  , config.MVC.movie_trashcan_clean     , None                  , None                  , 0     , [-5]        , _("Help Enable auto trashcan cleanup")),
			(_("How many days files may remain in trashcan")    , config.MVC.movie_trashcan_limit     , None                  , None                  , 0     , [-6, -1]    , _("Help How many days files may remain in trashcan")),
			(self.section                                       , _("LANGUAGE")                       , None                  , None                  , 1     , []          , ""),
			(_("Preferred EPG language")                        , config.MVC.epglang                  , setEPGLanguage        , None                  , 1     , []          , _("Help Preferred EPG language")),
			(_("Enable playback auto-subtitling")               , config.MVC.autosubs                 , None                  , None                  , 1     , []          , _("Help Enable playback auto-subtitling")),
			(_("Primary playback subtitle language")            , config.MVC.sublang1                 , None                  , None                  , 1     , [-1]        , _("Help Primary playback subtitle language")),
			(_("Secondary playback subtitle language")          , config.MVC.sublang2                 , None                  , None                  , 1     , [-2]        , _("Help Secondary playback subtitle language")),
			(_("Tertiary playback subtitle language")           , config.MVC.sublang3                 , None                  , None                  , 1     , [-3]        , _("Help Tertiary playback subtitle language")),
			(_("Enable playback auto-language selection")       , config.MVC.autoaudio                , None                  , None                  , 1     , []          , _("Help Enable playback auto-language selection")),
			(_("Enable playback AC3-track first")               , config.MVC.autoaudio_ac3            , None                  , None                  , 1     , [-1]        , _("Help Enable playback AC3-track first")),
			(_("Primary playback audio language")               , config.MVC.audlang1                 , None                  , None                  , 1     , [-2]        , _("Help Primary playback audio language")),
			(_("Secondary playback audio language")             , config.MVC.audlang2                 , None                  , None                  , 1     , [-3]        , _("Help Secondary playback audio language")),
			(_("Tertiary playback audio language")              , config.MVC.audlang3                 , None                  , None                  , 1     , [-4]        , _("Help Tertiary playback audio language")),
		]

	def createConfig(self):
		self.list = []
		for i, conf in enumerate(self.MVCConfig):
			# 0 entry text
			# 1 variable
			# 2 validation
			# 3 pressed ok
			# 4 setup level
			# 5 parent entries
			# 6 help text
			# Config item must be valid for current usage setup level
			if config.usage.setup_level.index >= conf[4]:
				# Parent entries must be true
				for parent in conf[5]:
					if parent < 0:
						if not self.MVCConfig[i + parent][1].value:
							break
					elif parent > 0:
						if self.MVCConfig[i - parent][1].value:
							break
				else:
					# Loop fell through without a break
					if conf[0] == self.section:
						if len(self.list) > 1:
							self.list.append(getConfigListEntry("", config.MVC.fake_entry, None, None, 0, [], ""))
						if conf[1] == "":
							self.list.append(getConfigListEntry("<DUMMY CONFIGSECTION>",))
						else:
							self.list.append(getConfigListEntry(conf[1],))
					else:
						self.list.append(getConfigListEntry(conf[0], conf[1], conf[2], conf[3], conf[4], conf[5], conf[6]))
		self["config"].setList(self.list)
		self.setTitle(_("Setup"))

	def loadDefaultSettings(self):
		self.session.openWithCallback(
			self.loadDefaultSettingsCB,
			MessageBox,
			_("Loading default settings will overwrite all settings, really load them?"),
			MessageBox.TYPE_YESNO
		)

	def loadDefaultSettingsCB(self, result):
		if result:
			# Refresh is done implicitly on change
			for conf in self.MVCConfig:
				if len(conf) > 1 and conf[0] != self.section:
					conf[1].value = conf[1].default
			self.createConfig()

	def changedEntry(self, _addNotifier=None):
		if self.reloadTimer.isActive():
			self.reloadTimer.stop()
		self.reloadTimer.start(50, True)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		self["help"].text = cur and cur[6] or ""

	def dirSelected(self, res):
		if res:
			res = os.path.normpath(res)
			self["config"].getCurrent()[1].value = res

	def keyOK(self):
		try:
			current = self["config"].getCurrent()
			if current:
				current[3](current[1])
		except Exception:
			pass

	def keySaveNew(self):
		config.MVC.needsreload.value = True

		for i, entry in enumerate(self.list):
			if len(entry) > 1:
				if entry[1].isChanged():
					if entry[2]:
						# execute value changed -function
						if entry[2](entry[1]):
							# Stop exiting, user has to correct the config
							return
					# Check parent entries
					for parent in entry[5]:
						try:
							if self.list[i + parent][2]:
								# execute parent value changed -function
								if self.list[i + parent][2](self.MVCConfig[i + parent][1]):
									# Stop exiting, user has to correct the config
									return
						except Exception:
							continue
					entry[1].save()
		configfile.save()
		if self.needsRestartFlag:
			self.session.open(MessageBox, _("Some changes require a GUI restart"), MessageBox.TYPE_INFO, 10)
		self.close()

	def activateTrashcan(self, element):
		if element:
			self.enableTrashcan()

	def launchListSet(self, element):
		if element:
			self.needsRestart()

	def needsRestart(self, dummy=None):
		self.needsRestartFlag = True

	def openLocationBox(self, element):
		if element:
			path = os.path.normpath(element.value)
			self.session.openWithCallback(
				self.dirSelected,
				LocationBox,
				windowTitle=_("Select Location"),
				text=_("Select directory"),
				currDir=str(path) + "/",
				bookmarks=config.movielist.videodirs,
				autoAdd=False,
				editDir=True,
				inhibitDirs=["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/var"],
				minFree=100
			)

	def showInfo(self, dummy=None):
		self.session.open(MessageBox, "MovieCockpit" + ": Version " + VERSION, MessageBox.TYPE_INFO)

	def validatePath(self, element):
		element.value = os.path.normpath(element.value)
		if not os.path.exists(element.value):
			self.session.open(MessageBox, _("Path does not exist") + ": " + str(element.value), MessageBox.TYPE_ERROR)
			return False
