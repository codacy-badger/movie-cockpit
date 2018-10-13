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
from Components.config import config
from Components.Label import Label
from enigma import getDesktop, gPixmapPtr, eDVBVolumecontrol
from Components.VideoWindow import VideoWindow
from Components.Pixmap import Pixmap
from Components.Sources.MVCServiceEvent import MVCServiceEvent
from ServiceCenter import ServiceCenter
from SkinUtils import getSkinPath
from Cover import Cover


class EventInfo(Cover, object):

	def __init__(self):
		print("MVC: MovieSelectionEventInfo: EventInfo: __init__")
		self["Service"] = MVCServiceEvent(ServiceCenter.getInstance())
		# Movie preview
		desktopSize = getDesktop(0).size()
		self["Video"] = VideoWindow(decoder=0, fb_width=desktopSize.width(), fb_height=desktopSize.height())
		# Movie Cover
		self["Cover"] = Pixmap()
		self["Cover"].hide()
		self["CoverBg"] = Pixmap()
		self["CoverBg"].hide()
		self["CoverBgLbl"] = Label()
		self["CoverBgLbl"].hide()
		self.volctrl = eDVBVolumecontrol.getInstance()
		self.preMute_muteState = None

	def initPig(self):
		if not config.MVC.cover.value:
			self["Video"].show()
			self.miniTV_resume(True)
		else:
			self["Video"].hide()
			self["Cover"].instance.setPixmap(gPixmapPtr())

		self["Cover"].hide()
		self["CoverBg"].hide()
		self["CoverBgLbl"].hide()

	def isMuted(self):
		if self.volctrl:
			return self.volctrl.isMuted()
		else:
			return None

	def volumeMute(self):
		if self.volctrl:
			self.volctrl.volumeMute()

	def volumeUnMute(self):
		if self.volctrl:
			self.volctrl.volumeUnMute()

	def checkHideMiniTV_beforeFullscreen(self):
		return

	def controlMiniTV(self):
		if config.MVC.hide_miniTV.value == "all":
			self.miniTV_off()
		else:
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			if ref:
				try:
					mypath = ref.getPath()
					print("MVC: MovieSelection: onDialogShow: mypath: " + mypath)
					# playback
					if config.MVC.hide_miniTV.value == "playback":
						self.miniTV_off()
				except Exception:
					if self.isCurrentlySeekable(): # timeshift active and play position "in the past"
						# timeshift
						if config.MVC.hide_miniTV.value == "liveTVorTS":
							self.miniTV_off()
					else:
						# live TV
						if config.MVC.hide_miniTV.value in ("liveTVorTS", "liveTV"):
							self.miniTV_off()

	def miniTV_off(self):
		self.session.nav.stopService()
		if config.MVC.cover_hide_miniTV.value:
			self.session.nav.playService(self.lastservice)  # we repeat this to make framebuffer black
			self.session.nav.stopService()

	def miniTV_unmute(self):
		if self.preMute_muteState:
			if not self.preMute_muteState:
				self.volumeUnMute()
			self.preMute_muteState = None

	def miniTV_resume(self, calledFromInitPig):
		if self.lastservice and not self.hide_miniTV:
			self.session.nav.playService(self.lastservice)
			if calledFromInitPig:
				self.lastservice = None
			else:
				self["Video"].show()
			self.miniTV_unmute()
		elif not self.lastservice:
			self.session.nav.stopService()
			self.miniTV_off()
		else:
			self.miniTV_off()

	def updateEventInfo(self, service):
		self["Service"].newService(service)

	def hideCover(self):
		self["Cover"].hide()
		self["CoverBg"].hide()
		self["CoverBgLbl"].hide()
		if config.MVC.cover_hide_miniTV.value:
			self.miniTV_resume(False)

	def showCover(self, service=None):
		if service:
			jpgpath = self.getCoverPath(service.getPath())
			if not os.path.exists(jpgpath):
				jpgpath = None
				if config.MVC.cover_fallback.value:
					jpgpath = getSkinPath("img/no_cover.svg")

			print("MVC: MovieSelectionEventInfo: showCover: jpgpath " + str(jpgpath))
			if jpgpath:
				if config.MVC.cover.value:
					if self.cover:
						self["Cover"].show()
						self["CoverBg"].show()
						self["CoverBgLbl"].show()
						if config.MVC.cover_hide_miniTV.value:
							self.miniTV_off()

						self.displayCover(jpgpath, self["Cover"])
			else:
				self.hideCover()
		else:
			self["Cover"].hide()
