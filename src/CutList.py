#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 cmikula, betonme
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

import os
from Screens.InfoBarGenerics import InfoBarCueSheetSupport
from CutListUtils import packCutList, unpackCutList, ptsToSeconds, readCutsFile, writeCutsFile, deleteCutsFile,\
	replaceLast, replaceLength, removeMarks, getCutListLast, getCutListLength, mergeCutList, verifyCutList

# [Cutlist.Workaround] Enable Cutlist-Workaround:
# Creates a backup of the cutlist during recording and merge it with the cutlist-file from enigma after recording
DO_CUTLIST_WORKAROUND = True

# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT

# cut_list data structure
# cut_list[x][0] = pts  = long long
# cut_list[x][1] = what = long

class CutList(object):

	ENABLE_RESUME_SUPPORT = True

	def __init__(self, path):
		#print("MVC: CutList: __init__: path: %s" % path)
		path = self.__newPath(path)
		if path:
			if (hasattr(self, 'cut_list') and hasattr(self, 'cut_file')) and (self.cut_file == path):
				#print("MVC: CutList: __init__: cuts are still available: " + str(self.cut_list))
				pass
			else:
				self.cut_file = path
				self.cut_list = self.__readCutFile(self.cut_file)
				#print("MVC: CutList: __init__: cuts were read form cache: " + str(self.cut_list))

	def __newPath(self, path):
		if path:
			path += ".cuts"
		return path

	def __getCuesheet(self):
		service = self.session.nav.getCurrentService()
		return service and service.cueSheet()

	# InfoBarCueSheetSupport
	def downloadCuesheet(self):
		#print("MVC: CutList: downloadCuesheet")
		service = hasattr(self, "service") and self.service

		# Is there native cuesheet support
		cue = self.__getCuesheet()  # InfoBarCueSheetSupport._InfoBarCueSheetSupport__getCuesheet(self)
		if cue is None or (cue and not cue.getCutList()):
			# No native cuesheet support
			if service:
				path = service.getPath()
				self.cut_file = self.__newPath(path)
				self.cut_list = self.__readCutFile(self.cut_file)
		else:
			# Native cuesheet support
			self.cut_list = cue.getCutList()

		#print("MVC: CutList: downloadCuesheet: CUTSTEST0 " + str(self.cut_list))

	# InfoBarCueSheetSupport
	def uploadCuesheet(self):
		#print("MVC: CutList: uploadCuesheet")
		# Is there native cuesheet support
		cue = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getCuesheet(self)

		if cue is None or (cue and not cue.getCutList()):
			# No native cuesheet support
			# Update local cut list, maybe there is a newer one
			if hasattr(self, "service") and self.service:
				path = self.service.getPath()
				self.cut_file = self.__newPath(path)
				self.__writeCutFile(self.cut_file, self.cut_list)
		else:
			# Native cuesheet support
			if self.service:
				if self.service.getPath().rsplit('.')[-1] == "mkv":
					path = self.service.getPath()
					self.cut_file = self.__newPath(path)
					self.__writeCutFile(self.cut_file, self.cut_list)
				else:
					cue.setCutList(self.cut_list)
			else:
				cue.setCutList(self.cut_list)

	def updateFromCuesheet(self):
		#print("MVC: CutList: updateFromCuesheet")
		# Use non native cuesheet support
		# [Cutlist.Workaround] merge with Backup-File if exists
		if DO_CUTLIST_WORKAROUND:
			path = self.cut_file + ".save"
			if os.path.exists(path):
				#print("MVC: CutList: updateFromCuesheet: reading from Backup-File")
				data = readCutsFile(path)
				self.cut_list = mergeCutList(self.cut_list, unpackCutList(data))
				#print("MVC: CutList: updateFromCuesheet: delete Backup-File ")
				os.remove(path)
			else:
				#print("MVC: CutList: updateFromCuesheet: no Backup-File found: " + path)
				pass
		cut_list = self.__readCutFile(self.cut_file)
		self.cut_list = mergeCutList(self.cut_list, cut_list)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def setCutList(self, cut_list):
		#print("MVC: CutList: setCutList: " + str(cut_list))
		self.cut_list = cut_list
		self.__writeCutFile(self.cut_file, self.cut_list)

	def getCutList(self):
		return self.cut_list

	@staticmethod
	def getCutListLastInSeconds(cut_list):
		return ptsToSeconds(getCutListLast(cut_list))

	@staticmethod
	def getCutListLengthInSeconds(cut_list):
		return ptsToSeconds(getCutListLength(cut_list))

	def resetLastCutList(self):
		#print("MVC: resetLastCutList: self.cut_file: %s, self.cut_list: %s" % (self.cut_file, self.cut_list))
		self.cut_list = replaceLast(self.cut_list, 0)
		#print("MVC: resetLastCutList: self.cut_list: %s" % self.cut_list)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def updateCutList(self, play, length):
		#print("MVC: CutList: updateCutList: play: " + str(play) + ", length: " + str(length))
		self.cut_list = replaceLast(self.cut_list, play)
		self.cut_list = replaceLength(self.cut_list, length)
		self.uploadCuesheet()

	def removeMarksCutList(self):
		self.cut_list = removeMarks(self.cut_list)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def deleteFileCutList(self):
		from MovieCache import MovieCache
		data = ""
		MovieCache.getInstance().update(os.path.splitext(self.cut_file)[0], pcuts=data)
		deleteCutsFile(self.cut_file)

	def reloadCutListFromFile(self):
		from MovieCache import MovieCache
		data = readCutsFile(self.cut_file)
		MovieCache.getInstance().update(os.path.splitext(self.cut_file)[0], pcuts=data)
		self.cut_list = verifyCutList(unpackCutList(data))
		return self.cut_list

	def __readCutFile(self, path):
		from MovieCache import MovieCache, IDX_CUTS
		if path:
			#print("MVC: CutList: __readCutFile: reading cut_list from cache: " + os.path.splitext(path)[0])
			filedata = MovieCache.getInstance().getFile(os.path.splitext(path)[0])
			data = filedata[IDX_CUTS]
			cut_list = unpackCutList(data)
			#print("MVC: CutList: __readCutFile: cut_list: " + str(cut_list))
		else:
			cut_list = []
			#print("MVC: CutList: __readCutFile: no path specified")
		return cut_list

	def __writeCutFile(self, path, cut_list):
		from MovieCache import MovieCache
		#print("MVC: CutList: __writeCutFile: %s, cut_list: %s" % (path, cut_list))
		if path:
			data = packCutList(cut_list)
			writeCutsFile(path, data)

			# update file in cache
			#print("MVC: CutList: __writeCutFile: cut_list: " + str(cut_list))
			#print("MVC: CutList: __writeCutFile: updating cut_list in cache: " + os.path.splitext(path)[0])
			MovieCache.getInstance().update(os.path.splitext(path)[0], pcuts=data)

			# [Cutlist.Workaround]
			# Always make a backup-copy when recording, it will be merged with enigma-cutfile after recording
			if DO_CUTLIST_WORKAROUND:
				ts_path, __ = os.path.splitext(path)
				from RecordingsControl import RecordingsControl
				recording = RecordingsControl.getRecording(ts_path, True)
				if recording:
					path += ".save"
					#print("MVC: CutList: __writeCutFile: creating backup file: " + path)
					writeCutsFile(path, data)
