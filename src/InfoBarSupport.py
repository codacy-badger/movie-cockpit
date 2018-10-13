#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by betonme
#               2018 dream-alpha
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
from Components.ActionMap import HelpableActionMap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import iPlayableService
from Screens.InfoBarGenerics import InfoBarExtensions, InfoBarSeek, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection, InfoBarSimpleEventView, \
	InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarPlugins, InfoBarNumberZap, \
	InfoBarPiP, InfoBarEPG, InfoBarShowHide, InfoBarNotifications, InfoBarServiceNotifications, Notifications
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from DelayedFunction import DelayedFunction
from CutListUtils import secondsToPts, ptsToSeconds, verifyCutList, getCutListLast

SeekbarPlg = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/Seekbar/plugin.py")

# Overwrite Seekbar
def MVCkeyOK(self):
	from MediaCenter import MediaCenter
	sel = self["config"].getCurrent()[1]
	if sel == self.positionEntry:
		if self.length:
			# seekTo() doesn't work for DVD Player
			oldPosition = self.seek.getPlayPosition()[1]
			newPosition = int(float(self.length[1]) / 100.0 * self.percent)
			if newPosition > oldPosition:
				pts = newPosition - oldPosition
			else:
				pts = -1 * (oldPosition - newPosition)
			MediaCenter.doSeekRelative(self.infobarInstance, pts)
			self.exit()
	elif sel == self.minuteInput:
		pts = secondsToPts(self.minuteInput.value * 60)
		if self.fwd is False:
			pts = -1 * pts
		MediaCenter.doSeekRelative(self.infobarInstance, pts)
		self.exit()

class InfoBarSupport(InfoBarBase, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection,
	InfoBarSimpleEventView, InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin,
	InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarNumberZap, InfoBarPiP, InfoBarEPG, object):

	def __init__(self):
		self.allowPiP = True
		self.allowPiPSwap = False

		for x in InfoBarShowHide, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarShowMovies, InfoBarAudioSelection, InfoBarSimpleEventView, InfoBarServiceNotifications, InfoBarPVRState, \
			InfoBarSubtitleSupport, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications, InfoBarPlugins, InfoBarNumberZap, \
			InfoBarPiP, InfoBarEPG:
			#InfoBarCueSheetSupport
			#InfoBarMoviePlayerSummarySupport
			x.__init__(self)

		actionmap = "InfobarCueSheetActions"
		self["CueSheetActions"] = HelpableActionMap(
			self,
			actionmap,
			{
				"jumpPreviousMark": (self.jumpPreviousMark, _("jump to previous marked position")),
				"jumpNextMark": (self.jumpNextMark, _("jump to next marked position")),
				"toggleMark": (self.toggleMark, _("toggle a cut mark at the current position"))
			},
			prio=1
		)

		self.cut_list = []
		self.is_closing = False
		self.resume_point = 0

		self.__event_tracker = ServiceEventTracker(
			screen=self,
			eventmap={
				iPlayableService.evStart: self.__serviceStarted,
			}
		)

	##############################################################################
	## Override from InfoBarGenerics.py

	# InfoBarCueSheetSupport
	def __serviceStarted(self):
		if not self.is_closing:
			print("MVC: InfoBarSupport: __serviceStarted: new service started, trying to download cuts")
			self.downloadCuesheet()

			if config.usage.on_movie_start.value == "beginning" and config.MVC.movie_jump_first_mark.value:
				self.jumpToFirstMark()
			else:
				if self.ENABLE_RESUME_SUPPORT:
					last = getCutListLast(verifyCutList(self.cut_list))
					if last > 0:
						self.resume_point = last
						l = ptsToSeconds(last)
						val = config.usage.on_movie_start.value
						if val == "ask" or val == "ask yes" or val == "ask no":
							Notifications.AddNotificationWithCallback(
								self.playLastCallback,
								MessageBox,
								_("Do you want to resume this playback?")
								+ "\n"
								+ (_("Resume position at %s") % ("%d:%02d:%02d" % (l / 3600, l % 3600 / 60, l % 60))),
								timeout=10,
								default=not (val == "ask no")
							)
						elif val == "resume":
							Notifications.AddNotificationWithCallback(
								self.playLastCallback,
								MessageBox,
								_("Resuming playback"),
								timeout=2,
								type=MessageBox.TYPE_INFO
							)
					elif config.MVC.movie_jump_first_mark.value:
						self.jumpToFirstMark()
				elif config.MVC.movie_jump_first_mark.value:
					self.jumpToFirstMark()

	def playLastCallback(self, answer):
		if answer:
			self.doSeek(self.resume_point)
		elif config.MVC.movie_jump_first_mark.value:
			self.jumpToFirstMark()
		self.showAfterSeek()

	def numberEntered(self, retval):
		if retval and retval > 0 and retval != "":
			self.zapToNumber(retval)

	def zapToNumber(self, number):
		if self.service:
			seekable = self.getSeek()
			if seekable:
				seekable.seekChapter(number)

	def jumpToFirstMark(self):
		firstMark = None
		current_pos = self.cueGetCurrentPosition() or 0
		# Increase current_pos by 2 seconds to make sure we get the correct mark
		current_pos = current_pos + 180000
		# MVC enhancement: increase recording margin to make sure we get the correct mark
		margin = config.recording.margin_before.value * 60 * 90000 * 2 or 20 * 60 * 90000
		middle = (self.getSeekLength() or 90 * 60 * 90000) / 2

		for (pts, what) in self.cut_list:
			if what == self.CUT_TYPE_MARK:
				if pts and (current_pos < pts and pts < margin and pts < middle):
					if firstMark is None or pts < firstMark:
						firstMark = pts
		if firstMark:
			self.start_point = firstMark
			#== wait to seek - in OE2.5 not seek without wait
			DelayedFunction(500, self.doSeek, self.start_point)

	def jumpNextMark(self):
		if not self.jumpPreviousNextMark(lambda x: x - 90000):
			# There is no further mark
			self.doSeekEOF()
		else:
			if config.usage.show_infobar_on_skip.value:
				# InfoBarSeek
				self.showAfterSeek()

	# InfoBarSeek
	# Seekbar workaround
	def seekFwdManual(self):
		if fileExists("%so" % SeekbarPlg) or fileExists("%sc" % SeekbarPlg):
			from Plugins.Extensions.Seekbar.plugin import Seekbar, seekbar
			Seekbar.keyOK = MVCkeyOK
			seekbar(self)
			Seekbar.keyOK = Seekbar.keyOK
		else:
			# InfoBarSeek
			InfoBarSeek.seekFwdManual(self)

	# Seekbar workaround
	def seekBackManual(self):
		if fileExists("%so" % SeekbarPlg) or fileExists("%sc" % SeekbarPlg):
			from Plugins.Extensions.Seekbar.plugin import Seekbar, seekbarBack
			Seekbar.keyOK = MVCkeyOK
			seekbarBack(self)
			Seekbar.keyOK = Seekbar.keyOK
		else:
			# InfoBarSeek
			InfoBarSeek.seekBackManual(self)

	def doSeekRelative(self, pts):
		if self.getSeekLength() < self.getSeekPlayPosition() + pts:
			# Relative jump is behind the movie length
			self.doSeekEOF()
		else:
			# Call base class function
			InfoBarSeek.doSeekRelative(self, pts)

	def doSeek(self, pts):
		length = self.getSeekLength()
		if length and length < pts:
			# PTS is behind the movie length
			self.doSeekEOF()
		else:
			# Call baseclass function
			InfoBarSeek.doSeek(self, pts)
			if pts and config.usage.show_infobar_on_skip.value:
				# InfoBarSeek
				self.showAfterSeek()

	def getSeekPlayPosition(self):
		try:
			# InfoBarCueSheetSupport
			return self.cueGetCurrentPosition() or 0
		except Exception as e:
			print("MVC: InfoBarSupport: getSeekPlayPosition: exception:\n" + str(e))
			return 0

	def getSeekLength(self):
		try:
			# Call private InfoBarCueSheetSupport function
			seek = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getSeekable(self)
		except Exception as e:
			print("MVC: InfoBarSupport: getSeekLength: exception:\n" + str(e))
		if seek is None:
			return None
		length = seek.getLength()
		return long(length[1])

	# Handle EOF
	def doSeekEOF(self):
		# Stop one second before eof : 1 * 90 * 1000
		state = self.seekstate
		play = self.getSeekPlayPosition()
		length = self.getSeekLength()
		end = length and length - 2 * 90000

		# Validate play and end values
		if play and end and play < end and 0 < end:
			# InfoBarSeek
			InfoBarSeek.doSeek(self, end)

		# If player is in pause mode do not call eof
		if state != self.SEEK_STATE_PAUSE:
			InfoBarSeek._InfoBarSeek__evEOF(self)
