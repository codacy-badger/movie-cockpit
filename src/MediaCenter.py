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
from time import time
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.Pixmap import Pixmap
from enigma import iSubtitleType_ENUMS
from Screens.Screen import Screen
from Screens.AudioSelection import SUB_FORMATS, GST_SUB_FORMATS
from Screens.InfoBarGenerics import InfoBarSubtitleSupport, InfoBarShowHide
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Tools.ISO639 import LanguageCodes as langC
from Components.Language import language
from Components.Harddisk import Util
from Tools.Notifications import AddPopup
from ServiceReference import ServiceReference
from DelayedFunction import DelayedFunction
from CutList import CutList
from InfoBarSupport import InfoBarSupport
from Components.Sources.MVCCurrentService import MVCCurrentService
from ServiceCenter import ServiceCenter
from MediaTypes import sidDVB, extTS
from Cover import Cover
from RecordingsControl import RecordingsControl
from SkinUtils import getSkinPath
from IMDbEventViewSimple import IMDbEventViewSimple


# Just a dummy to prevent crash
class InfoBarTimeshift(object):

	def __init__(self):
		pass

	def startTimeshift(self):
		pass


class MVCMoviePlayerSummary(Screen, object):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self.skinName = "MVCMoviePlayerSummary"
		self["Service"] = MVCCurrentService(session.nav, parent)


class MediaCenter(CutList, Screen, HelpableScreen, Cover, InfoBarTimeshift, InfoBarSupport, object):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, playlist, lastservice=None):

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarTimeshift.__init__(self)
		InfoBarSupport.__init__(self)

		self.skinName = "MediaCenter"
		self.skin = Util.readFile(getSkinPath("MediaCenter.xml"))

		self.serviceHandler = ServiceCenter.getInstance()

		self["Service"] = MVCCurrentService(session.nav, self)

		if config.MVC.movie_exit.value:
			self["actions"] = HelpableActionMap(
				self,
				"MVCPlayerActions",
				{
					"leavePlayer": (self.leavePlayer, _("Stop playback"))
				},
				-1
			)
		else:
			self["actions"] = HelpableActionMap(
				self,
				"MVCPlayerActions2",
				{
					"leavePlayer": (self.leavePlayer, _("Stop playback"))
				},
				-1
			)

		self["MenuActions"].prio = 2
		if "TeletextActions" in self:
			self["TeletextActions"].prio = 2
			self["TeletextActions"].setEnabled(True)

		self["NumberActions"].prio = 2

		self["Cover"] = Pixmap()
		self["mvcPic"] = Pixmap()

		self.firstStart = True
		self.closedByDelete = False
		self.closeAll = False

		self.lastservice = lastservice or self.session.nav.getCurrentlyPlayingServiceReference()
		if not self.lastservice:
			self.lastservice = InfoBar.instance.servicelist.servicelist.getCurrent()
		self.service = playlist[0]
		self.allowPiP = True
		self.allowPiPSwap = False
		self.realSeekLength = None
		self.servicelist = InfoBar.instance.servicelist

		# Dialog Events
		self.onShown.append(self.__onShow)  # Don't use onFirstExecBegin() it will crash
		self.onClose.append(self.__onClose)
		self.file_format = "(.ts|.avi|.mkv|.divx|.f4v|.flv|.img|.iso|.m2ts|.m4v|.mov|.mp4|.mpeg|.mpg|.mts|.vob|.asf|.wmv|.stream|.webm)"

	def showCover(self):
		if config.MVC.cover.value:
			jpgpath = self.getCoverPath(self.service.getPath())
			print("MVC: MediaCenter: showCover: jpgpath: " + jpgpath)
			if not os.path.exists(jpgpath):
				self["Cover"].hide()
				self["mvcPic"].show()
			else:
				self["Cover"].show()
				self["mvcPic"].hide()
			self.displayCover(jpgpath, self["Cover"])

	def getCurrentEvent(self):
		service = self.currentlyPlayedMovie()
		if service:
			return self.serviceHandler.info(service).getEvent()

	def infoMovie(self):
		try:
			service = self.currentlyPlayedMovie()
			evt = self.getCurrentEvent()
			if evt:
				self.session.open(IMDbEventViewSimple, evt, ServiceReference(service))
		except Exception as e:
			print("MVC: MediaCenter: infoMovie: detail exception:\n" + str(e))

	def __onShow(self):
		if self.firstStart:
			# Avoid new playback if the user switches between MovieSelection and MoviePlayer
			self.firstStart = False
			self.evEOF()	# begin playback
			if self.service and self.service.type != sidDVB:
				self.realSeekLength = self.getSeekLength()

	def evEOF(self, needToClose=False):
		print("MVC: MediaCenter: evEOF")

		path = self.service and self.service.getPath()
		if os.path.exists(path):
#			MovieCenterGUI.toggleProgressService(self.service, True)

			# Start playing movie
			self.session.nav.playService(self.service)

			if self.service and self.service.type != sidDVB:
				self.realSeekLength = self.getSeekLength()

			#TODO AutoSelect subtitle for DVD Player is not implemented yet
			DelayedFunction(250, self.setAudioTrack)
			DelayedFunction(250, self.setSubtitleState, True)

			self.showCover()
		else:
			self.session.open(
				MessageBox,
				_("Skipping movie, the file does not exist.") + self.service.getPath(),
				MessageBox.TYPE_ERROR,
				10
			)
			self.evEOF(needToClose)

	def leavePlayer(self, stopped=True):
		print("MVC: MediaCenter: leavePlayer: %s" % stopped)

		self.setSubtitleState(False)

		if self.service and self.service.type != sidDVB:
			self.makeUpdateCutList()

		reopen = False
		if stopped:
			print("MVC: MediaCenter: leavePlayer: closed by user")
			if config.MVC.movie_reopen.value:
				reopen = True
		elif self.closedByDelete:
			print("MVC: MediaCenter: leavePlayer: closed due to file delete")
			reopen = True
		else:
			print("MVC: MediaCenter: leavePlayer: closed due to playlist EOF")
			if self.closeAll:
				if config.MVC.record_eof_zap.value == "1":
					AddPopup(
						_("Zap to Live TV of recording"),
						MessageBox.TYPE_INFO,
						3,
						"MVCCloseAllAndZap"
					)
			else:
				if config.MVC.movie_reopenEOF.value:  # did the player close while movie list was open?
					reopen = True

		self.session.nav.stopService()
		# [Cutlist.Workaround] - part 2
		# Always make a backup-copy when recording is running and we stopped the playback
		if stopped and self.service and self.service.type == sidDVB:
			path = self.service.getPath()
			if RecordingsControl.isRecording(path):
				cutspath = self.service.getPath() + '.cuts'
				bcutspath = cutspath + '.save'
				if os.path.exists(cutspath):
					import shutil
					shutil.copy2(cutspath, bcutspath)

			print("MVC: MediaCenter: leavePlayer: update cuts: " + self.service.getPath())
			cuts = CutList(self.service.getPath())
			cut_list = cuts.getCutList()
			print("MVC: MediaCenter: leavePlayer: cut_list before update: " + str(cut_list))
			cut_list = cuts.reloadCutListFromFile()
			print("MVC: MediaCenter: leavePlayer: cut_list after  reload: " + str(cut_list))
		self.close(reopen, self.service)

	def __onClose(self):
		if self.lastservice:
			self.session.nav.playService(self.lastservice)

	##############################################################################
	## Recordings relevant function
	def getLength(self):
		service = self.service
		path = service and service.getPath()
		if path:
			record = RecordingsControl.getRecording(path, True)
			if record:
				begin, end, _service_ref = record
				return (end - begin) * 90000

			if os.path.splitext(path)[1] in extTS:
				length = self.serviceHandler.info(service).getLength()
				return (length + config.recording.margin_before.value * 60) * 90000

		# fallback for non-ts movies
		seek = self.getSeek()
		if seek is None:
			return None

		length = seek.getLength()
#		print("MVC: MediaCenter: getLength: seek.getLength(): " + str(length))
		if length[0]:
			return 0
		return length[1]

	def getPosition(self):
		service = self.service
		path = service and service.getPath()
		record = RecordingsControl.getRecording(path, True)
		if record:
			begin, _end, _service_ref = record
			return int((time() - begin) * 90000)

		# fallback
		seek = self.getSeek()
		if seek is None:
			return None

		pos = seek.getPlayPosition()
#		print("MVC: MediaCenter: getPosition: getPlayPosition(): " + str(pos))
		if pos[0]:
			return 0
		return pos[1]

	##############################################################################
	## List functions

	def currentlyPlayedMovie(self):
		return self.service

	##############################################################################
	## Audio and Subtitles
	def setAudioTrack(self):
		try:
			print("MVC: MediaCenter: setAudioTrack: ###############################################audio")
			if not config.MVC.autoaudio.value:
				return
			service = self.session.nav.getCurrentService()
			tracks = service and self.getServiceInterface("audioTracks")
			nTracks = tracks and tracks.getNumberOfTracks() or 0
			if not nTracks:
				return
			idx = 0
			trackList = []
			for i in xrange(nTracks):
				audioInfo = tracks.getTrackInfo(i)
				lang = audioInfo.getLanguage()
				print("MVC: MediaCenter: setAudioTrack: lang %s") % lang
				desc = audioInfo.getDescription()
				print("MVC: MediaCenter: setAudioTrack: desc %s") % desc
#				audio_type = audioInfo.getType()
				track = idx, lang, desc, type
				idx += 1
				trackList += [track]
			seltrack = tracks.getCurrentTrack()
			# we need default selected language from image
			# to set the audio track if "config.MVC.autoaudio.value" are not set
			syslang = language.getLanguage()[:2]
			if config.MVC.autoaudio.value:
				audiolang = [config.MVC.audlang1.value, config.MVC.audlang2.value, config.MVC.audlang3.value]
			else:
				audiolang = syslang
			useAc3 = config.MVC.autoaudio_ac3.value	  # mvc has new value, in some images it gives different values for that
			if useAc3:
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
				return
			else:
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			print("MVC: MediaCenter: setAudioTrack: ###############################################audio1")
		except Exception as e:
			print("MVC: MediaCenter: setAudioTrack: exception:\n" + str(e))

	def tryAudioTrack(self, tracks, audiolang, trackList, seltrack, useAc3):
		for entry in audiolang:
			entry = langC[entry][0]
			print("MVC: MediaCenter: tryAudioTrack: ###############################################audio2")
			for x in trackList:
				try:
					x1val = langC[x[1]][0]
				except Exception:
					x1val = x[1]
				print(x1val)
				print("entry %s") % entry
				print(x[0])
				print("seltrack %s") % seltrack
				print(x[2])
				print(x[3])
				if entry == x1val and seltrack == x[0]:
					if useAc3:
						print("MVC: MediaCenter: tryAudioTrack: ###############################################audio3")
						if x[3] == 1 or x[2].startswith('AC'):
							print("MVC: MediaCenter: [MVCPlayer] audio track is current selected track: " + str(x))
							return True
					else:
						print("MVC: MediaCenter: tryAudioTrack: ###############################################audio4")
						print("MVC: MediaCenter: tryAudioTrack: currently selected track: " + str(x))
						return True
				elif entry == x1val and seltrack != x[0]:
					if useAc3:
						print("MVC: MediaCenter: tryAudioTrack: ###############################################audio5")
						if x[3] == 1 or x[2].startswith('AC'):
							print("MVC: MediaCenter: tryAudioTrack: match: " + str(x))
							tracks.selectTrack(x[0])
							return True
					else:
						print("###############################################audio6")
						print("MVC: MediaCenter: tryAudioTrack: match: " + str(x))
						tracks.selectTrack(x[0])
						return True
		return False

	def trySubEnable(self, slist, match):
		for e in slist:
			print("e: " + str(e))
			print("match %s" % (langC[match][0]))
			if langC[match][0] == e[2]:
				print("MVC: MediaCenter: trySubEnable: match: " + str(e))
				if self.selected_subtitle != e[0]:
					self.subtitles_enabled = False
					self.selected_subtitle = e[0]
					self.subtitles_enabled = True
					return True
			else:
				print("MVC: MediaCenter: trySubEnable: nomatch")
		return False

	def setSubtitleState(self, enabled):
		try:
			if not config.MVC.autosubs.value or not enabled:
				return

			subs = isinstance(self, InfoBarSubtitleSupport) and self.getCurrentServiceSubtitle() or None
			n = subs and subs.getNumberOfSubtitleTracks() or 0
			if n == 0:
				return

			self.sub_format_dict = {}
			self.gstsub_format_dict = {}
			for idx, (short, _text, rank) in sorted(SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.sub_format_dict[idx] = short
			for idx, (short, _text, rank) in sorted(GST_SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.gstsub_format_dict[idx] = short
			lt = []
			l = []
			for idx in range(n):
				info = subs.getSubtitleTrackInfo(idx)
				languages = info.getLanguage().split('/')
				print("MVC: MediaCenter: setSubtitleState: lang %s") % languages
				iType = info.getType()
				print("MVC: MediaCenter: setSubtitleState: type %s") % iType
				if iType == iSubtitleType_ENUMS.GST:
					iType = info.getGstSubtype()
					codec = iType in self.gstsub_format_dict and self.gstsub_format_dict[iType] or "?"
				else:
					codec = iType in self.sub_format_dict and self.sub_format_dict[iType] or "?"
				print("MVC: MediaCenter: setSubtitleState: codec %s") % codec
				lt.append((idx, (iType == 1 and "DVB" or iType == 2 and "TTX" or "???"), languages))
			if lt:
				print("MVC: MediaCenter: setSubtitleState: " + str(lt))
				for e in lt:
					l.append((e[0], e[1], e[2][0] in langC and langC[e[2][0]][0] or e[2][0]))
					if l:
						print("MVC: MediaCenter: setSubtitleState: " + str(l))
						for sublang in [config.MVC.sublang1.value, config.MVC.sublang2.value, config.MVC.sublang3.value]:
							if self.trySubEnable(l, sublang):
								break
		except Exception as e:
			print("MVC: MediaCenter: setSubtitleState: exception:\n" + str(e))

	##############################################################################
	## Implement functions for InfoBarGenerics.py
	# InfoBarShowMovies
	def showMovies(self):
		return
#		try:
#			from MovieSelection import MVCSelection
#			self.session.open(MVCSelection, returnService=self.service, playerInstance=self)
#		except Exception as e:
#			print("MVC: MediaCenter: showMovies: exception:\n" + str(e))

	##############################################################################
	## Override functions from InfoBarGenerics.py
	# InfoBarShowHide
# 	def serviceStarted(self): #override InfoBarShowHide function
# 		if self.dvdScreen:
# 			subTracks = self.getCurrentServiceSubtitle()
# 			subTracks.enableSubtitles(self.dvdScreen.instance, 0) # give parent widget reference to service for drawing menu highlights in a repurposed subtitle widget
# 			self.dvdScreen.show()

	def doShow(self):
		InfoBarShowHide.doShow(self)

	# InfoBarNumberZap
# 	def keyNumberGlobal(self, _number):
# 		if self.service and self.service.type == sidDVD:
# 			if fileExists("%so" % dvdPlayerPlg) or fileExists("%sc" % dvdPlayerPlg):
# 				if fileExists('/usr/lib/enigma2/python/Screens/DVD.pyo') or fileExists('/usr/lib/enigma2/python/Screens/DVD.pyc'):
# 					from Screens.DVD import ChapterZap
# 					self.session.openWithCallback(self.numberEntered, ChapterZap, "0")
# 				else:
# 					from Plugins.Extensions.DVDPlayer.plugin import ChapterZap
# 					self.session.openWithCallback(self.numberEntered, ChapterZap, "0")

	# InfoBarShowHide Key_Ok
	def toggleShow(self):
		self.LongButtonPressed = False
		# Call base class function
		InfoBarShowHide.toggleShow(self)

	def doEofInternal(self, playing):
		print("MVC: MediaCenter: doEofInternal")
		if self.execing and playing:
			val = config.MVC.record_eof_zap.value
			if val == "0" or val == "1" and self.service:
				recording = RecordingsControl.getRecording(self.service.getPath(), True)
				if recording:
					_begin, _end, service_ref = recording
					# Zap to new channel
					self.lastservice = service_ref
					self.service = None
					self.closeAll = True
					self.leavePlayer(False)
					return

			if self.service.type != sidDVB:
				self.makeUpdateCutList()

			self.evEOF()

	def makeUpdateCutList(self):
#		print("MVC: MediaCenter: makeUpdateCutList")
		if self.getSeekPlayPosition() == 0:
			if self.realSeekLength:
				self.updateCutList(self.realSeekLength, self.realSeekLength)
			else:
				self.updateCutList(self.getSeekLength(), self.getSeekLength())
		else:
			self.updateCutList(self.getSeekPlayPosition(), self.getSeekLength())
		print("MVC: MediaCenter: makeUpdateCutList: pos: " + str(self.getSeekPlayPosition()) + ", length: " + str(self.getSeekLength()))


	def createSummary(self):
		return MVCMoviePlayerSummary

	##############################################################################
	## Oozoon image specific and make now the PiPzap possible
	def up(self):
		try:
			if self.servicelist and self.servicelist.dopipzap:
				if "keep" not in config.usage.servicelist_cursor_behavior.value:
					self.servicelist.moveUp()
				self.session.execDialog(self.servicelist)
			else:
				self.showMovies()
		except Exception:
			self.showMovies()

	def down(self):
		try:
			if self.servicelist and self.servicelist.dopipzap:
				if "keep" not in config.usage.servicelist_cursor_behavior.value:
					self.servicelist.moveDown()
				self.session.execDialog(self.servicelist)
			else:
				self.showMovies()
		except Exception:
			self.showMovies()

	##############################################################################
	## LT image specific
	def startCheckLockTimer(self):
		pass
