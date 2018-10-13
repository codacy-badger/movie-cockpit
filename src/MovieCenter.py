#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#               2018 by dream_alpha
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

from ServiceCenter import ServiceCenter
from MediaTypes import virAll, cmtBM, cmtDir
from MediaTypes import virToE, extMedia
from Components.config import config
from enigma import eListboxPythonMultiContent, gFont
from MovieCenterGUI import MovieCenterGUI

#         0        1     2      3     4       5       6    7         8     9
# Tuple: (service, date, title, path, selnum, length, ext, filetype, cuts, service_reference)
MOVIE_IDX_SERVICE = 0
MOVIE_IDX_DATE = 1
MOVIE_IDX_TITLE = 2
MOVIE_IDX_PATH = 3
MOVIE_IDX_SELNUMBER = 4
MOVIE_IDX_LENGTH = 5
MOVIE_IDX_EXT = 6
MOVIE_IDX_FILETYPE = 7
MOVIE_IDX_CUTLIST = 8
MOVIE_IDX_SERVICE_REFERENCE = 9


class MovieCenter(MovieCenterGUI, object):

	def __init__(self):
		print("MVC: MovieCenter: __init__")

		self.current_path = config.MVC.movie_homepath.value
		self.list = []

		from ConfigInit import sort_modes
		self.actualSort = sort_modes.get(config.MVC.moviecenter_sort.value)[0]
		self.returnSort = None
		self.selectionList = None

		self.currentSelectionCount = 0
		self.highlightsMov = []
		self.highlightsDel = []
		self.highlightsCpy = []

		MovieCenterGUI.__init__(self)

		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, self.MVCFont)
		self.l.setFont(2, gFont("Regular", 20))
		self.l.setFont(3, self.MVCSelectFont)
		self.l.setFont(4, self.MVCDateFont)
		self.l.setBuildFunc(self.buildMovieCenterEntry)

		self.onSelectionChanged = []
		self.l.setList(self.getList())

	def selectionChanged(self):
		for f in self.onSelectionChanged:
			try:
				f()
			except Exception as e:
				print("MVC: MovieCenter: selectionChanged: External observer exception:\n" + str(e))

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[MOVIE_IDX_SERVICE]

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		if l and l[MOVIE_IDX_SERVICE]:
			return ServiceCenter.getInstance().info(l[MOVIE_IDX_SERVICE]).getEvent()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def removeService(self, service):
		if service:
			alist = self.removeServiceInternal(service)
			self.l.setList(alist)

	def removeServiceOfType(self, service, service_type):
		if service:
			alist = self.removeServiceOfTypeInternal(service, service_type)
			self.l.setList(alist)

	def __len__(self):
		return len(self.getList())

	def getSelectionList(self):
		selList = []
		if self.currentSelectionCount == 0:
			# if no selections made, select the current cursor position
			single = self.l.getCurrentSelection()
			if single:
				selList.append(single[0])
		else:
			selList = self.selectionList
		return selList

	def unselectService(self, service):
		if service:
			if self.selectionList:
				if service in self.selectionList:
					# Service is in selection - unselect it
					self.toggleSelection(service)
				else:
					self.invalidateService(service)
			else:
				self.invalidateService(service)

	def invalidateCurrent(self):
		self.l.invalidateEntry(self.getCurrentIndex())

	def invalidateService(self, service):
		idx = self.getIndexOfService(service)
		if idx < 0:
			return
		self.l.invalidateEntry(idx)	# force redraw of the item

# 	def refreshList(self):
# 		self.l.invalidate()

	def reload(self, path=None):
		if path is None:
			path = self.current_path
		print("MVC: MovieCenter: reload: current_path: " + str(path))
		alist = self.reloadInternal(path)
		self.l.setList(alist)
		return alist

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def pageUp(self):
		self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		self.instance.moveSelection(self.instance.pageDown)

	def moveTop(self):
		self.instance.moveSelection(self.instance.moveTop)

	def moveEnd(self):
		self.instance.moveSelection(self.instance.moveEnd)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def moveToService(self, service):
		if service:
			index = self.getIndexOfService(service)
			if index:
				self.instance.moveSelectionTo(index)

	def currentSelIsPlayable(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) in extMedia

	def currentSelIsDirectory(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) == cmtDir

	def currentSelIsVirtual(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) in virAll

	def currentSelIsBookmark(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) == cmtBM

	def indexIsDirectory(self, index):
		return self.getTypeOfIndex(index) == cmtDir

	def indexIsPlayable(self, index):
		return self.getTypeOfIndex(index) in extMedia

	def getCurrentSelDir(self):
		return self.getListEntry(self.getCurrentIndex())[MOVIE_IDX_PATH]

	def getCurrentSelName(self):
		return self.getListEntry(self.getCurrentIndex())[MOVIE_IDX_TITLE]

	def highlightService(self, enable, mode, service):
		if enable:
			self.unselectService(service)
			self.highlightServiceInternal(enable, mode, service)
		elif service:
			self.highlightServiceInternal(enable, mode, service)

	def toggleSelection(self, service=None, index=-1, overrideNum=None):
		entry = None
		if service is None:
			if index == -1:
				if self.l.getCurrentSelection() is None:
					return
				index = self.getCurrentIndex()
			entry = self.list[index]
		else:
			index = 0
			for e in self.list:
				if e[MOVIE_IDX_SERVICE] == service:
					entry = e
					break
				index += 1
		if entry is None:
			return

		# We have entry, index, overrideNum
		if not self.indexIsPlayable(index):
			return
		self.toggleSelectionInternal(entry, index, overrideNum, self.l.invalidateEntry)

	def toggleSortingMode(self):
		from ConfigInit import sort_modes
		sorts = [v[0] for v in sort_modes.values()]
		mode, order = self.actualSort
		# Get all sorting modes as a list of unique ids
		modes = list(set([m for m, _o in sorts]))
		if mode in modes:
			idx = modes.index(mode)
			if order:
				mode = modes[(idx + 1) % len(modes)]
			order = not order
		else:
			# fallback
			mode = modes[0]
			order = False
		self.setSortingMode(mode, order)

	def toggleSortingOrder(self):
		mode, order = self.actualSort
		self.setSortingMode(mode, not order)

	def setSortingMode(self, mode=None, order=None):
		self.returnSort = None

		if mode is None:
			mode = self.actualSort[0]
		if order is None:
			order = self.actualSort[1]

		self.actualSort = (mode, order)
		self.list = self.doListSort(self.list)
		self.l.setList(self.list)

	def getNextSelectedService(self, current, selectedlist=None):
		curSerRef = None

		if selectedlist is None:
			# Selectedlist is empty
			curSerRef = current
		elif current and current not in selectedlist:
			# Current is not within the selectedlist
			curSerRef = current
		else:
			# Current is within the selectedlist
			last_idx = len(self.list) - 1
			len_sel = len(selectedlist)
			first_sel_idx = last_idx
			last_sel_idx = 0

			# Get first and last selected item indexes
			for sel in selectedlist:
				idx = self.getIndexOfService(sel)
				if idx < 0:
					idx = 0
				if idx < first_sel_idx:
					first_sel_idx = idx
				if idx > last_sel_idx:
					last_sel_idx = idx

			# Calculate previous and next item indexes
			prev_idx = first_sel_idx - 1
			next_idx = last_sel_idx + 1
			len_fitola = last_sel_idx - first_sel_idx + 1

			# Check if there is a not selected item between the first and last selected item
			if len_fitola > len_sel:
				for entry in self.list[first_sel_idx:last_sel_idx]:
					if entry[MOVIE_IDX_SERVICE] not in selectedlist:
						# Return first entry which is not in selectedlist
						curSerRef = entry[MOVIE_IDX_SERVICE]
						break
			# Check if next calculated item index is within the movie list
			elif next_idx <= last_idx:
				# Select item behind selectedlist

				curSerRef = self.getServiceOfIndex(next_idx)
			# Check if previous calculated item index is within the movie list
			elif prev_idx >= 0:
				# Select item before selectedlist
				curSerRef = self.getServiceOfIndex(prev_idx)
			else:
				# The whole list must be selected
				# First and last item is selected
				# Recheck and find first not selected item
				for entry in self.list:
					if entry[MOVIE_IDX_SERVICE] not in selectedlist:
						# Return first entry which is not in selectedlist
						curSerRef = entry[MOVIE_IDX_SERVICE]
						break
		return curSerRef

	def getList(self):
		return self.list

	def getListEntry(self, index):
		return self.list[index]

	def getTypeOfIndex(self, index):
		return self.list[index][MOVIE_IDX_EXT]

	def getSorting(self):
		# Return the actual sorting mode
		return self.actualSort

	def resetSorting(self):
		from ConfigInit import sort_modes
		self.actualSort = sort_modes.get(config.MVC.moviecenter_sort.value)[0]

	def doListSort(self, sortlist):
		virToD = virAll
		if config.MVC.directories_ontop.value:
			virToD = virToE
		# This will find all unsortable items
		tmplist = [i for i in sortlist if i[MOVIE_IDX_EXT] in virToD]
		# Extract list items to be sorted
		sortlist = [i for i in sortlist if i[MOVIE_IDX_EXT] not in virToD]
		# Always sort via extension and sorttitle and never reversed
		tmplist.sort(key=lambda x: (x[MOVIE_IDX_EXT], x[MOVIE_IDX_TITLE].lower()))

		mode, order = self.actualSort

		if mode == "D": # Date sort
			if not order:
				sortlist.sort(key=lambda x: (x[MOVIE_IDX_DATE], x[MOVIE_IDX_TITLE].lower()), reverse=True)
			else:
				sortlist.sort(key=lambda x: (x[MOVIE_IDX_DATE], x[MOVIE_IDX_TITLE].lower()))

		elif mode == "A": # Alpha sort
			if not order:
				sortlist.sort(key=lambda x: (x[MOVIE_IDX_TITLE].lower(), x[MOVIE_IDX_DATE]))
			else:
				sortlist.sort(key=lambda x: (x[MOVIE_IDX_TITLE].lower(), x[MOVIE_IDX_DATE]), reverse=True)

		return tmplist + sortlist

	def updateLength(self, service, length):
		# Update entry in list... so next time we don't need to recalc
		idx = self.getIndexOfService(service)
		if idx >= 0:
			x = self.list[idx]
			if x[MOVIE_IDX_LENGTH] != length:
				l = list(x)
				l[MOVIE_IDX_LENGTH] = length
				self.list[idx] = tuple(l)

	def serviceBusy(self, service):
		return service in self.highlightsMov or service in self.highlightsDel or service in self.highlightsCpy

	def serviceMoving(self, service):
		return service and service in self.highlightsMov

	def serviceDeleting(self, service):
		return service and service in self.highlightsDel

	def serviceCopying(self, service):
		return service and service in self.highlightsCpy

	def resetSelection(self):
		self.selectionList = None
		self.currentSelectionCount = 0

	def getFilePathOfService(self, service):
		if service:
			for entry in self.list:
				if entry[MOVIE_IDX_SERVICE] == service:
					return entry[MOVIE_IDX_PATH]
		return ""

	def getNameOfService(self, service):
		if service:
			for entry in self.list:
				if entry[MOVIE_IDX_SERVICE] == service:
					return entry[MOVIE_IDX_TITLE]
		return ""

	def getLengthOfService(self, service):
		if service:
			for entry in self.list:
				if entry[MOVIE_IDX_SERVICE] == service:
					return entry[MOVIE_IDX_LENGTH]
		return 0

	def getIndexOfService(self, service):
		if service:
			idx = 0
			for entry in self.list:
				if entry[MOVIE_IDX_SERVICE] == service:
					return idx
				idx += 1
		return -1

	def getServiceOfIndex(self, index):
		return self.list[index] and self.list[index][MOVIE_IDX_SERVICE]

	def removeServiceInternal(self, service):
		if service:
			for l in self.list[:]:
				if l[MOVIE_IDX_SERVICE] == service:
					self.list.remove(l)
					break
			return self.doListSort(self.list)

	def removeServiceOfTypeInternal(self, service, service_type):
		if service:
			for l in self.list[:]:
				if l[MOVIE_IDX_SERVICE] == service and l[MOVIE_IDX_EXT] == service_type:
					self.list.remove(l)
					break
			return self.doListSort(self.list)

	def toggleSelectionInternal(self, entry, index, overrideNum, invalidateFunction=None):
		if self.selectionList is None:
			self.selectionList = []
		newselnum = entry[MOVIE_IDX_SELNUMBER]	# init with old selection number
		if overrideNum is None:
			if self.serviceBusy(entry[MOVIE_IDX_SERVICE]):
				return	# no toggle if file being operated on
			# basic selection toggle
			if newselnum == 0:
				# was not selected
				self.currentSelectionCount += 1
				newselnum = self.currentSelectionCount
				self.selectionList.append(entry[MOVIE_IDX_SERVICE]) # append service
			else:
				# was selected, reset selection number and decrease all that had been selected after this
				newselnum = 0
				self.currentSelectionCount -= 1
				count = 0
				if entry:
					if entry[MOVIE_IDX_SERVICE] in self.selectionList:
						self.selectionList.remove(entry[MOVIE_IDX_SERVICE]) # remove service
				for i in self.list:
					if i[MOVIE_IDX_SELNUMBER] > entry[MOVIE_IDX_SELNUMBER]:
						l = list(i)
						l[MOVIE_IDX_SELNUMBER] = i[MOVIE_IDX_SELNUMBER] - 1
						self.list[count] = tuple(l)
						if invalidateFunction:
							invalidateFunction(count) # force redraw
					count += 1
		else:
			newselnum = overrideNum * (newselnum == 0)
		l = list(entry)
		l[MOVIE_IDX_SELNUMBER] = newselnum
		self.list[index] = tuple(l)
		if invalidateFunction:
			invalidateFunction(index) # force redraw of the modified item

	def highlightServiceInternal(self, enable, mode, service):
		if enable:
			if mode == "move":
				self.highlightsMov.append(service)
			elif mode == "del":
				self.highlightsDel.append(service)
			elif mode == "copy":
				self.highlightsCpy.append(service)
		elif service:
			# Reset the length to force progress recalculation
			self.updateLength(service, 0)
			if mode == "move":
				if service in self.highlightsMov:
					self.highlightsMov.remove(service)
			elif mode == "del":
				if service in self.highlightsDel:
					self.highlightsDel.remove(service)
			elif mode == "copy":
				if service in self.highlightsCpy:
					self.highlightsCpy.remove(service)
