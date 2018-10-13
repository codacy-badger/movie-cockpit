#!/usr/bin/python
# encoding: utf-8
#
# EitSupport
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
import struct
import re
from Components.Harddisk import Util
from Components.config import config
from Tools.ISO639 import LanguageCodes


def parseMJD(MJD):
	# Parse 16 bit unsigned int containing Modified Julian Date,
	# as per DVB-SI spec
	# returning year, month, day
	YY = int((MJD - 15078.2) / 365.25)
	MM = int((MJD - 14956.1 - int(YY * 365.25)) / 30.6001)
	D = MJD - 14956 - int(YY * 365.25) - int(MM * 30.6001)
	K = 0
	if MM == 14 or MM == 15:
		K = 1

	return (1900 + YY + K), (MM - 1 - K * 12), D


def unBCD(byte):
	return (byte >> 4) * 10 + (byte & 0xf)


def language_iso639_2to3(alpha2):
	ret = alpha2
	if alpha2 in LanguageCodes:
		language = LanguageCodes[alpha2]
		for alpha, name in LanguageCodes.items():
			if name == language:
				if len(alpha) == 3:
					return alpha
	return ret


def convertToUtf8(descriptor, codepage=""):
	if descriptor:
		try:
			if codepage != 'utf-8':
				descriptor = descriptor.decode(codepage).encode("utf-8")
			else:
				descriptor.decode('utf-8')
		except (UnicodeDecodeError, AttributeError) as e:
			print("MVC: EitFile: convertToUtf8: exception:\n" + str(e))
			pass
	return descriptor.strip()


# http://de.wikipedia.org/wiki/Event_Information_Table
class EitFile(object):

	def __init__(self, path=None):
		self.eit = {}
		if path:
			eit_file = self.__newPath(path)
			data = self.__readFile(eit_file)
			if data and len(data) >= 12:
				self.__parse(data)

	def __newPath(self, path):
		path, __ = os.path.splitext(path)
		if not os.path.exists(path + ".eit"):
			# Strip existing cut number
			if path[-4:-3] == "_" and path[-3:].isdigit():
				path = path[:-4]
		path += ".eit"
		return path

	def __readFile(self, path):
		data = None
		if os.path.isfile(path):
			data = Util.readFile(path)
		return data

	def __mk_int(self, s):
		return int(s) if s else 0

#	def __toDate(self, d, t):
#		if d and t:
#			try:
#				return datetime(int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]))
#			except ValueError:
#				return None
#		else:
#			return None

	##############################################################################
	## Get Functions
#	def getsid(self):
#		return self.eit.get('service', "")
#
#	def getTsId(self):
#		return self.eit.get('transportstream', "")
#
#	def getWhen(self):
#		return self.eit.get('when', "")
#
#	def getStartDate(self):
#		return self.eit.get('startdate', "")
#
#	def getStartTime(self):
#		return self.eit.get('starttime', "")
#
#	def getDuration(self):
#		return self.eit.get('duration', "")
#
	def getName(self):
		return self.eit.get('name', "")

	def getShortDescription(self):
		return self.eit.get('short_description', "")

	def getExtendedDescription(self):
		return self.eit.get('description', "")

	def getLengthInSeconds(self):
		length = self.eit.get('duration', "")
		if len(length) > 2:
			return self.__mk_int((length[0] * 60 + length[1]) * 60 + length[2])
		elif len(length) > 1:
			return self.__mk_int(length[0] * 60 + length[1])
		else:
			return self.__mk_int(length)

#	def getDate(self):
#		return self.__toDate(self.getStartDate(), self.getStartTime())

	def __parse(self, data):
		EIT_LINKAGE_DESCRIPTOR = 0x4a
		EIT_SHORT_EVENT_DESCRIPTOR = 0x4d
		EIT_EXTENDED_EVENT_DESCRIPTOR = 0x4e
		EIT_COMPONENT_DESCRIPTOR = 0x50
		EIT_CONTENT_DESCRIPTOR = 0x54
		EIT_PARENTAL_RATING_DESCRIPTOR = 0x55
		EIT_PDC_DESCRIPTOR = 0x69

		def determineCodepage(byte):
			codepage = None
			if byte == "1":
				codepage = 'iso-8859-5'
			elif byte == "2":
				codepage = 'iso-8859-6'
			elif byte == "3":
				codepage = 'iso-8859-7'
			elif byte == "4":
				codepage = 'iso-8859-8'
			elif byte == "5":
				codepage = 'iso-8859-9'
			elif byte == "6":
				codepage = 'iso-8859-10'
			elif byte == "7":
				codepage = 'iso-8859-11'
			elif byte == "9":
				codepage = 'iso-8859-13'
			elif byte == "10":
				codepage = 'iso-8859-14'
			elif byte == "11":
				codepage = 'iso-8859-15'
			elif byte == "21":
				codepage = 'utf-8'
			return codepage

		def parseHeader(data, pos):
			e = struct.unpack(">HHBBBBBBH", data[pos:pos + 12])
			#event_id = e[0]
			date = parseMJD(e[1])					# Y, M, D
			time = unBCD(e[2]), unBCD(e[3]), unBCD(e[4])		# HH, MM, SS
			duration = unBCD(e[5]), unBCD(e[6]), unBCD(e[7])	# HH, MM, SS
			running_status = (e[8] & 0xe000) >> 13
			#free_CA_mode = e[8] & 0x1000
			#descriptors_loop_length = e[8] & 0x0fff

			if running_status in [1, 2]:
				self.eit['when'] = "NEXT"
			elif running_status in [3, 4]:
				self.eit['when'] = "NOW"

			self.eit['startdate'] = date
			self.eit['starttime'] = time
			self.eit['duration'] = duration

		def parseShortEventDescriptor(data, pos):
			ISO_639_language_code = str(data[pos + 2:pos + 5]).upper()
			event_name_length = ord(data[pos + 5])
			name_event_description = ""
			for i in range(pos + 6, pos + 6 + event_name_length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					name_event_description += data[i]
			if not self.name_event_codepage:
				try:
					byte1 = str(ord(data[pos + 6]))
				except Exception:
					byte1 = ''
				self.name_event_codepage = determineCodepage(byte1)

			short_event_description = ""
			if not self.short_event_codepage:
				try:
					byte1 = str(ord(data[pos + 7 + event_name_length]))
				except Exception:
					byte1 = ''
				self.short_event_codepage = determineCodepage(byte1)
			for i in range(pos + 7 + event_name_length, pos + length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					short_event_description += data[i]
			if ISO_639_language_code == lang:
				self.short_event_descriptor.append(short_event_description)
				self.name_event_descriptor.append(name_event_description)
			if (ISO_639_language_code == self.prev1_ISO_639_language_code) or (self.prev1_ISO_639_language_code == "x"):
				self.short_event_descriptor_multi.append(short_event_description)
				self.name_event_descriptor_multi.append(name_event_description)
			else:
				self.short_event_descriptor_multi.append("\n\n" + short_event_description)
				self.name_event_descriptor_multi.append(" " + name_event_description)
			self.prev1_ISO_639_language_code = ISO_639_language_code

		def parseExtendedEventDescriptor(data, pos):
			ISO_639_language_code = ""
			for i in range(pos + 3, pos + 6):
				ISO_639_language_code += data[i]
			ISO_639_language_code = ISO_639_language_code.upper()
			extended_event_description = ""
			if not self.extended_event_codepage:
				try:
					byte1 = str(ord(data[pos + 8]))
				except Exception:
					byte1 = ''
				self.extended_event_codepage = determineCodepage(byte1)
			for i in range(pos + 8, pos + length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					extended_event_description += data[i]
			if ISO_639_language_code == lang:
				self.extended_event_descriptor.append(extended_event_description)
			if (ISO_639_language_code == self.prev2_ISO_639_language_code) or (self.prev2_ISO_639_language_code == "x"):
				self.extended_event_descriptor_multi.append(extended_event_description)
			else:
				self.extended_event_descriptor_multi.append("\n\n" + extended_event_description)
			self.prev2_ISO_639_language_code = ISO_639_language_code

		def parseContentDescriptor(_data, _pos):
			print("MVC: EitFile: parseContentDescriptor")
			self.content_descriptor.append("n/a")

		self.eit = {}
		epglang = config.MVC.epglang.value
		lang = (language_iso639_2to3(epglang.lower()[:2])).upper()

		# Parse the data
		pos = 0
		parseHeader(data, pos)
		pos += 12

		self.name_event_descriptor = []
		self.name_event_descriptor_multi = []
		self.name_event_codepage = None
		self.short_event_descriptor = []
		self.short_event_descriptor_multi = []
		self.short_event_codepage = None
		self.extended_event_descriptor = []
		self.extended_event_descriptor_multi = []
		self.extended_event_codepage = None
		self.component_descriptor = []
		self.content_descriptor = []
		self.linkage_descriptor = []
		self.parental_rating_descriptor = []
		self.pdc_descriptor = []
		self.prev1_ISO_639_language_code = "x"
		self.prev2_ISO_639_language_code = "x"

		while pos < len(data) - 2:
			rec = ord(data[pos])
			length = ord(data[pos + 1]) + 2

			if rec == EIT_SHORT_EVENT_DESCRIPTOR:
				parseShortEventDescriptor(data, pos)

			elif rec == EIT_EXTENDED_EVENT_DESCRIPTOR:
				parseExtendedEventDescriptor(data, pos)

			elif rec == EIT_COMPONENT_DESCRIPTOR:
				self.component_descriptor.append(data[pos + 8:pos + length])

			elif rec == EIT_CONTENT_DESCRIPTOR:
				parseContentDescriptor(data, pos)
				self.eit['content'] = self.content_descriptor

			elif rec == EIT_LINKAGE_DESCRIPTOR:
				self.linkage_descriptor.append(data[pos + 8:pos + length])

			elif rec == EIT_PARENTAL_RATING_DESCRIPTOR:
				self.parental_rating_descriptor.append(data[pos + 2:pos + length])

			elif rec == EIT_PDC_DESCRIPTOR:
				self.pdc_descriptor.append(data[pos + 5:pos + length])

			else:
				print("MVC: EitFile: __parse: unsupported descriptor: %x %x" % (rec, length))
				print("MVC: EitFile: __parse: %s" % (data[pos:pos + length]))
				pass

			pos += length

		if self.name_event_descriptor:
			self.name_event_descriptor = "".join(self.name_event_descriptor)
		else:
			self.name_event_descriptor = ("".join(self.name_event_descriptor_multi)).strip()
		self.eit['name'] = convertToUtf8(self.name_event_descriptor, self.name_event_codepage)

		if self.short_event_descriptor:
			self.short_event_descriptor = "".join(self.short_event_descriptor)
		else:
			self.short_event_descriptor = ("".join(self.short_event_descriptor_multi)).strip()
		self.eit['short_description'] = convertToUtf8(self.short_event_descriptor, self.short_event_codepage)

		if self.extended_event_descriptor:
			self.extended_event_descriptor = "".join(self.extended_event_descriptor)
		else:
			self.extended_event_descriptor = ("".join(self.extended_event_descriptor_multi)).strip()
		self.extended_event_descriptor = convertToUtf8(self.extended_event_descriptor, self.extended_event_codepage)
		if self.extended_event_descriptor:
			# This will fix EIT data of RTL group with missing line breaks in extended event description
			self.extended_event_descriptor = re.sub('((?:Moderat(?:ion:|or(?:in){0,1})|Vorsitz: |Jur(?:isten|y): |G(?:\xC3\xA4|a)st(?:e){0,1}: |Mit (?:Staatsanwalt|Richter(?:in){0,1}|den Schadenregulierern) |Julia Leisch).*?[a-z]+)(\'{0,1}[0-9A-Z\'])', r'\1\n\n\2', self.extended_event_descriptor)
		self.eit['description'] = self.extended_event_descriptor
