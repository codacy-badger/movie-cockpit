#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 betonme
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

from time import mktime
from CutList import CutList
from CutListUtils import unpackCutList
from Components.config import config
from enigma import eServiceCenter, iServiceInformation
from MovieCache import MovieCache, TYPE_ISFILE, str2date

instance = None


class ServiceCenter(object):

	def __init__(self):
		global instance
		instance = eServiceCenter.getInstance()
		instance.info = self.info

	@staticmethod
	def getInstance():
		if instance is None:
			ServiceCenter()
		return instance

	def info(self, service):
		return ServiceInfo(service)


class ServiceInfo(object):

	def __init__(self, service):
		self.info = None
		if service:
			self.info = Info(service)

	def cueSheet(self):
		return self.info and self.info.cueSheet()

	def getLength(self, _service=None):
		return self.info and self.info.getLength()

	def getInfoString(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sServiceref:
			return self.info and self.info.getServiceReference()
		if info_type == iServiceInformation.sDescription:
			return self.info and self.info.getShortDescription()
		if info_type == iServiceInformation.sTags:
			return self.info and self.info.getTags()
		return "None"

	def getInfo(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sTimeCreate:
			return self.info and self.info.getMTime()
		return None

	def getInfoObject(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sFileSize:
			return self.info and self.info.getSize()
		return None

	def getName(self, _service=None):
		return self.info and self.info.getName()

	def getEvent(self, _service=None):
		return self.info

	def getStartTime(self, _service=None):
		return self.info and self.info.getMTime()


class Info(object):

	def __init__(self, service):
		self.path = service and service.getPath()
		_dirname, filetype, _path, _filename, _ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = MovieCache.getInstance().getFile(self.path)
		self.__filetype = filetype
		self.__date = str2date(date)
		self.__name = name
		self.__eventname = name
		self.__mtime = int(mktime(self.__date.timetuple()))
		self.__shortdescription = description
		self.__extendeddescription = extended_description
		self.__length = length
		self.__rec_ref_str = service_reference
		self.__size = size
		self.__tags = tags
		self.__cut_list = unpackCutList(cuts)
		self.__id = 0

	def cueSheet(self):
		return CutList(self.path)

	def getName(self):
		#EventName NAME
		return self.__name

	def getServiceReference(self):
		return self.__rec_ref_str

	def getTags(self):
		return self.__tags

	def getEventName(self):
		return self.__eventname

	def getShortDescription(self):
		#TMDBInfo MOVIE_META_DESCRIPTION
		#TMDBInfo SHORT_DESCRIPTION
		#EventName SHORT_DESCRIPTION
		return self.__shortdescription

	def getExtendedDescription(self):
		#EventName EXTENDED_DESCRIPTION
		return self.__extendeddescription

	def getEventId(self):
		#EventName ID
		return self.__id

	def getBeginTimeString(self):
		return self.__date.strftime(config.MVC.movie_date_format.value)

	def getMTime(self):
		return self.__mtime

	def getLength(self):
		return self.__length

#	def getBeginTime(self):
#		return self.getMTime()

	def getDuration(self):
		return self.getLength()

	def getSize(self):
		if self.__filetype == TYPE_ISFILE:
			size = self.__size
		else:
			if config.MVC.directories_info.value or config.MVC.movie_trashcan_info.value:
				_count, size = MovieCache.getInstance().getCountSize(self.path)
		return size
