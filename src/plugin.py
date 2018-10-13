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
from Plugins.Plugin import PluginDescriptor
from enigma import eServiceEvent
from skin import loadSkin
from MovieCache import MovieCache
from ConfigInit import ConfigInit
from RecordingsControl import RecordingsControl
from Version import VERSION
from SkinUtils import getSkinPath
from Trashcan import Trashcan

gSession = None


def setEPGLanguage(_self=None):
	if config.MVC.epglang.value:
		print("MVC: plugin: Setting EPG language: %s" % config.MVC.epglang.value)
		eServiceEvent.setEPGLanguage(config.MVC.epglang.value)

def loadLCDSkin():
	loadSkin(getSkinPath("MediaCenter_LCD.xml"))


def MVCStartup():
	print("MVC: plugin: +++")
	print("MVC: plugin: +++ MVC: " + VERSION + " starts...")
	print("MVC: plugin: +++")

	loadLCDSkin()
	setEPGLanguage()
	MovieCache.getInstance()
	RecordingsControl()
	Trashcan()


def MVCShutdown():
	print("MVC: plugin: ---")
	print("MVC: plugin: --- MVC: Shutdown")
	print("MVC: plugin: ---")

	MovieCache.getInstance().close()


def showMoviesNew(dummy_self=None):
	from MovieSelection import MVCSelection
	gSession.openWithCallback(showMoviesCallback, MVCSelection)


def showMoviesCallback(*args):
	print("MVC: plugin: showMoviesCallback: *args: " + str(args))
	if args:
		from MediaCenter import MediaCenter
		gSession.openWithCallback(playerCallback, MediaCenter, *args)


def playerCallback(reopen=False, *args):
	print("MVC: plugin: playerCallback: *args: " + str(args))
	if reopen:
		showMoviesNew(*args)


def autostart(reason, **kwargs):
	for key in kwargs:
		print("MVC: plugin: autostart: **kwargs: %s: %s" % (key, kwargs[key]))
	if reason == 0: # start
		if "session" in kwargs:
			global gSession
			gSession = kwargs["session"]
			MVCStartup()

			if not config.MVC.ml_disable.value:
				try:
					from Screens.InfoBar import InfoBar
					value = config.MVC.movie_launch.value
					if value == "showMovies":
						InfoBar.showMovies = showMoviesNew
					elif value == "showTv":
						InfoBar.showTv = showMoviesNew
					elif value == "showRadio":
						InfoBar.showRadio = showMoviesNew
					elif value == "openQuickbutton":
						InfoBar.openQuickbutton = showMoviesNew
					elif value == "timeshiftStart":
						InfoBar.startTimeshift = showMoviesNew
				except Exception as e:
					print("MVC: plugin: autostart: launch override exception:\n" + str(e))
	elif reason == 1: # shutdown
		MVCShutdown()
	else:
		print("MVC: plugin: autostart: reason not handled: " + str(reason))


def settingsOpen(session, *args, **kwargs):
	print("MVC: plugin: settingsOpen: *args: " + str(args))
	for key in kwargs:
		print("MVC: plugin: settingsOpen: **kwargs: %s: %s" % (key, kwargs[key]))
	from ConfigScreen import ConfigScreen
	session.open(ConfigScreen)


def recordingsOpen(session, *args, **kwargs):
	print("MVC: plugin: recordingsOpen: *args: " + str(args))
	for key in kwargs:
		print("MVC: plugin: recordingsOpen: **kwargs: %s: %s" % (key, kwargs[key]))
	from MovieSelection import MVCSelection
	session.openWithCallback(showMoviesCallback, MVCSelection)


def Plugins(**kwargs):
	for key in kwargs:
		print("MVC: plugin: Plugins: **kwargs: %s: %s" % (key, kwargs[key]))

	ConfigInit()

	descriptors = []
	descriptors.append(
		PluginDescriptor(
			where=[
				PluginDescriptor.WHERE_SESSIONSTART,
				PluginDescriptor.WHERE_AUTOSTART
			],
			fnc=autostart))

	if config.MVC.extmenu_plugin.value:
		descriptors.append(
			PluginDescriptor(name="MovieCockpit" + " (" + _("Setup") + ")",
			description=_("Manage recordings"),
			icon="MovieCockpit.svg",
			where=[
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			fnc=settingsOpen))

	if config.MVC.extmenu_list.value and not config.MVC.ml_disable.value:
		descriptors.append(
			PluginDescriptor(name="MovieCockpit",
			where=PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=recordingsOpen))
	return descriptors
