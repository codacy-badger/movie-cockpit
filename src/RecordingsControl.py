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
#import datetime
from Components.config import config
from RecordTimer import AFTEREVENT
import NavigationInstance
from timer import TimerEntry
from DelayedFunction import DelayedFunction
from ServiceCenter import ServiceCenter
from Tasker import mvcTasker


class RecordingsControl(object):
	def __init__(self):
		#print("MVC: RecordingsControl: __init__")
		# Register for record events
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recEvent)
		# check for active recordings not yet in cache
		self.check4ActiveRecordings()

	def recEvent(self, timer):
		# StateWaiting=0, StatePrepared=1, StateRunning=2, StateEnded=3
		from MovieCache import MovieCache
		if timer and not timer.justplay:
			#print("MVC: RecordingsControl: recEvent: timer.Filename: %s, timer.state: %s" % (timer.Filename, timer.state))

			if timer.state == TimerEntry.StatePrepared:
#				#print("MVC: RecordingsControl: recEvent: timer.StatePrepared")
				pass

			elif timer.state == TimerEntry.StateRunning:
				#print("MVC: RecordingsControl: recEvent: REC START for: " + timer.Filename)
				DelayedFunction(250, MovieCache.getInstance().loadDatabaseFile, timer.Filename)
				DelayedFunction(500, self.reloadList)

			elif timer.state == TimerEntry.StateEnded or timer.state == TimerEntry.StateWaiting:
				#print("MVC: RecordingsControl: recEvent: REC END for: " + timer.Filename)
				MovieCache.getInstance().update(timer.Filename, psize=os.path.getsize(timer.Filename))
				DelayedFunction(500, self.reloadList)
				# [Cutlist.Workaround] Initiate the Merge
				DelayedFunction(500, self.mergeCutListAfterRecording, timer.Filename)
				if hasattr(timer, "fixMoveCmd"):
					#print("MVC: RecordingsControl: recEvent: file had been moved while recording was in progress, moving left over files...")
					mvcTasker.shellExecute(timer.fixMoveCmd)

		if config.MVC.timer_autoclean.value:
			DelayedFunction(2000, self.timerCleanup)  # postpone to avoid crash in basic timer delete by user

	def check4ActiveRecordings(self):
		from MovieCache import MovieCache, IDX_PATH
		#print("MVC: RecordingsControl: check4ActiveRecordings")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			# check if file is in cache
			if timer.Filename and timer.isRunning() and not timer.justplay:
				afile = MovieCache.getInstance().getFile(timer.Filename)
				if not afile[IDX_PATH]:
					#print("MVC: RecordingsControl: check4ActiveRecordings: loadDatabaseFile: " + timer.Filename)
					MovieCache.getInstance().loadDatabaseFile(timer.Filename)

	def mergeCutListAfterRecording(self, path):
		#print("MVC: RecordingsControl: mergeCutListAfterRecording: %s" % path)
		from CutList import CutList
		CutList(path).updateFromCuesheet()

	def reloadList(self):
		#print("MVC: RecordingsControl: reloadList")
		try:
			from MovieSelection import MVCSelection
			movie_selection = MVCSelection.getInstance()
			if movie_selection:
				#print("MVC: RecordingsControl: reloadList: calling movie_selection.reloadList")
				DelayedFunction(500, movie_selection.reloadList)
		except Exception:
			#print("MVC: RecordingsControl: reloadList: movie_selection.reloadList exception")
			pass

	def timerCleanup(self):
		NavigationInstance.instance.RecordTimer.cleanup()

	@staticmethod
	def isRecording(filename):
		#print("MVC: RecordingsControl: isRecording: filename: %s" % filename)
		recording = False
		if filename:
			#print("MVC: RecordingsControl: isRecording: filename: " + filename)
			filename = os.path.basename(filename)
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if filename == os.path.basename(timer.Filename) and timer.state == TimerEntry.StateRunning:
					recording = True
					break
		return recording

	@staticmethod
	def stopRecording(filename):
		if filename[0] == "/":
			filename = os.path.basename(filename)
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.isRunning() and not timer.justplay and timer.Filename.find(filename) >= 0:
				if timer.repeated:
					timer.enable()
					timer_afterEvent = timer.afterEvent
					timer.afterEvent = AFTEREVENT.NONE
					timer.processRepeated(findRunningEvent=False)
					NavigationInstance.instance.RecordTimer.doActivate(timer)
					timer.afterEvent = timer_afterEvent
					NavigationInstance.instance.RecordTimer.timeChanged(timer)
				else:
					timer.afterEvent = AFTEREVENT.NONE
					NavigationInstance.instance.RecordTimer.removeEntry(timer)
				#print("MVC: RecordingsControl: stopRecording: REC STOP for: " + filename)
				return True

	@staticmethod
	def isCutting(filename):
		return filename.lower().endswith("_.ts") and not os.path.exists(filename[:-2] + "eit")

	@staticmethod
	def fixTimerPath(old_filename, new_filename):
		try:
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if timer.isRunning() and not timer.justplay and timer.Filename == old_filename:
					timer.dirname = os.path.dirname(new_filename) + "/"
					timer.fixMoveCmd = 'mv "' + timer.Filename + '."* "' + timer.dirname + '"'
					timer.Filename = new_filename
					#print("MVC: Recordingscontrol fixTimerPath: fixed path: " + new)
					break
		except Exception as e:
			print("MVC: RecordingsControl: fixTimerPath: exception:\n" + str(e))
			pass

	@staticmethod
	def getRecording(path, include_margin_before=True):
		recording = None
		if path:
			##print("MVC: RecordingsControl: getRecording: filename: " + path)
			filename = os.path.basename(path)
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if filename == os.path.basename(timer.Filename) and timer.state == TimerEntry.StateRunning and not timer.justplay:
					#print("MVC: RecordingsControl: getRecording: include_margin_before: %s" % include_margin_before)
					if include_margin_before:
						from MovieCache import getPlayerService
						service = getPlayerService(timer.Filename, "", ".ts")
						#print("MVC: ServiceCenter: getRecording: service path: " + service.getPath())
						actual_start = ServiceCenter.getInstance().info(service).getStartTime()
						#print("MVC: RecordingsControl: getRecording: actual_start: " + str(datetime.datetime.fromtimestamp(actual_start)))
						delta = actual_start - timer.begin
						if delta > 0 and delta < config.recording.margin_before.value * 60:
							#print("MVC: RecordingsControl: getRecording: late recording but within margin_before")
							recording = (
								actual_start - (config.recording.margin_before.value - delta),
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
						if delta > config.recording.margin_before.value * 60:
							#print("MVC: RecordingsControl: getRecording: late recording")
							recording = (
								actual_start,
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
						else:   # delta == config.recording.margin_before.value * 60
							#print("MVC: RecordingsControl: getRecording: ontime recording")
							recording = (
								actual_start - config.recording.margin_before.value * 60,
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
					else:
						recording_start = int(os.stat(path).st_mtime)  # timestamp from file
						#print("MVC: RecordingsControl: getRecording: recording_start: " + str(datetime.datetime.fromtimestamp(recording_start)))
						delta = recording_start - timer.begin
						#print("MVC: MovieCache: loadDatabaseFile: recording delta: %s" % delta)
						if delta > 0 and delta < config.recording.margin_before.value * 60:
							# case 1: recording starts before event start but after planned start
							#print("MVC: RecordingsControl: getRecording: late recording but within margin_before")
							recording = (
								timer.begin + config.recording.margin_before.value,
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
						elif delta > config.recording.margin_before.value * 60:
							# case 2: recordings starts after event start
							#print("MVC: RecordingsControl: getRecording: late recording")
							recording = (
								recording_start,
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
						else:
							# case 3: recording starts on time
							#print("MVC: RecordingsControl: getRecording: ontime recording")
							recording = (
								timer.begin + config.recording.margin_before.value * 60,
								timer.end - config.recording.margin_after.value * 60,
								timer.service_ref.ref
							)
		return recording
