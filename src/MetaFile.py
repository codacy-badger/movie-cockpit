#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by betonme
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
from Components.Harddisk import Util

IDX_SERVICE = 0
IDX_NAME = 1
IDX_DESC = 2
IDX_RECTIME = 3
IDX_TAGS = 4
IDX_LENGTH = 5
IDX_FILESIZE = 6


# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT
class MetaFile(object):

	def __init__(self, path=None):
		self.meta_file = None
		self.meta = None
		if path:
			self.meta_file = self.__newPath(path)
			self.meta = self.__readFile(self.meta_file)

	def __newPath(self, path):
		if not os.path.exists(path + ".meta"):
			path, ext = os.path.splitext(path)
			# Strip existing cut number
			if path[-4:-3] == "_" and path[-3:].isdigit():
				path = path[:-4] + ext
		path += ".meta"
		return path

	def __readFile(self, path):
		meta = ["", "", "", "", "", "", ""]

		if os.path.isfile(path):
			lines = Util.readFile(path).splitlines()

			# Parse the lines
			if lines:
				# Strip lines and extract information
				lines = [l.strip() for l in lines]
				meta = lines[:]
		return meta

#	def __mk_int(self, s):
#		if s:
#			try:
#				return int(s)
#			except Exception:
#				return 0
#		else:
#			return 0

#	def __secondsToDate(self, s):
#		return s and datetime.fromtimestamp(s) or None

#	def getFile(self):
#		return self.meta

#	def getMTime(self):
#		return self.meta_mtime

	def getServiceReference(self):
		return self.meta[IDX_SERVICE]

#	def getName(self):
#		return self.meta[IDX_NAME]

#	def getDescription(self):
#		try:
#			self.meta[self.DESC].decode('utf-8')
#		except UnicodeDecodeError:
#			try:
#				self.meta[self.DESC] = self.meta[IDX_DESC].decode("cp1252").encode("utf-8")
#			except UnicodeDecodeError:
#				self.meta[self.DESC] = self.meta[IDX_DESC].decode("iso-8859-1").encode("utf-8")
#		return self.meta[self.DESC]

#	def getRecordingTime(self):
#		# Time in seconds since 1970
#		return self.__mk_int(self.meta[IDX_RECTIME])

	def getTags(self):
		return self.meta[IDX_TAGS]


#	def getLength(self):
#		return self.__ptsToSeconds(self.__mk_int(self.meta[IDX_LENGTH]))

#	def getFileSize(self):
#		return self.__mk_int(self.meta[IDX_FILESIZE])

#	def getDate(self):
#		return self.__secondsToDate(self.getRecordingTime())
