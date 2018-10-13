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
from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.LocationBox import LocationBox
from Tools.BoundFunction import boundFunction
from MountPoints import MountPoints
from DelayedFunction import DelayedFunction
from CutList import CutList
from MediaTypes import cmtBM
from RecordingsControl import RecordingsControl
from Trashcan import Trashcan
from FileOps import FileOps


class MovieOps(Trashcan, MountPoints, FileOps, object):

	stoppedRecordings = True

	### Utils

	def selectDirectory(self, callback, title):
		self.checkHideMiniTV_beforeFullscreen()
		self.session.openWithCallback(
			callback,
			LocationBox,
			windowTitle=title,
			text=_("Select directory"),
			currDir=str(self.current_path) + "/",
			bookmarks=config.movielist.videodirs,
			autoAdd=False,
			editDir=True,
			inhibitDirs=["/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"],
			minFree=100
		)

	### Recording

	def stopRecordConfirmed(self, confirmed):
		if confirmed:
			filenames = ""
			for service in self.recordings_to_stop:
				path = service.getPath()
				stoppedResult = RecordingsControl.stopRecording(path)
				print("MVC: MovieOps: stopRecordConfirmed: stoppedResult: %s" % stoppedResult)
				self.stoppedRecordings = self.stoppedRecordings and stoppedResult
				if stoppedResult is False:
					filenames += "\n" + path.split("/")[-1][:-3]
					if service in self.delete_file_list:
						self.delete_file_list.remove(service)
					elif service in self.trashcan_file_list:
						self.trashcan_file_list.remove(service)
			if not self.stoppedRecordings:
				print("MVC: MovieOps: stopRecordConfirmed: not all stopped")
				self.checkHideMiniTV_beforeFullscreen()
				self.session.openWithCallback(
					self.deleteMovieQ,
					MessageBox,
					_("Not all timers have been stopped. Modify them with the timer editor.") + filenames,
					MessageBox.TYPE_INFO,
					10
				)
			else:
				self.deleteMovieQ()

	def stopRecordQ(self):
		filenames = ""
		for service in self.recordings_to_stop:
			path = service.getPath()
			filenames += "\n" + path.split("/")[-1][:-3]
		self.checkHideMiniTV_beforeFullscreen()
		self.session.openWithCallback(
			self.stopRecordConfirmed,
			MessageBox,
			_("Stop ongoing recording(s)?") + filenames,
			MessageBox.TYPE_YESNO
		)


	### File I/O functions
	### Delete

	def deleteFile(self, delete_permanently=False):

		def deletePermanently(path, delete_permanently):
			if path:
				directory = os.path.dirname(path)
				delete_permanently |= not config.MVC.movie_trashcan_enable.value
				delete_permanently |= directory == config.MVC.movie_trashcan_path.value
				delete_permanently |= self.mountpoint(directory) != self.mountpoint(config.MVC.movie_trashcan_path.value)
			return delete_permanently

		selection_list = self.getSelectionList()
		self.delete_file_list = []
		self.trashcan_file_list = []
		self.delete_dir_list = []
		self.trashcan_dir_list = []
		self.delete_link_list = []
		self.trashcan_link_list = []
		self.recordings_to_stop = []

		for service in selection_list:
			path = service.getPath()
			print("MVC: MovieOps: deleteFile: %s" % path)
			if deletePermanently(path, delete_permanently):
				if os.path.isfile(path):
					self.delete_file_list.append(service)
				elif os.path.isdir(path):
					self.delete_dir_list.append(service)
				elif os.path.islink(path):
					self.delete_link_list.append(service)
			else:
				if os.path.isfile(path):
					self.trashcan_file_list.append(service)
				elif os.path.isdir(path):
					self.trashcan_dir_list.append(service)
				elif os.path.islink(path):
					self.trashcan_link_list.append(service)

		for service in self.delete_file_list + self.trashcan_file_list:
			path = service.getPath()
			if RecordingsControl.isRecording(path):
				self.recordings_to_stop.append(service)

		if len(self.recordings_to_stop) > 0:
			self.stopRecordQ()
		else:
			self.deleteMovieQ()

	def deleteMovieQ(self, _confirmed=True):

		def movieList(delete_list):
			names = ""
			movies = len(delete_list)
			for i, service in enumerate(delete_list):
				if i >= 5 and movies > 5:  # show only 5 entries in the file list
					names += "..."
					break
				name = self["list"].getNameOfService(service)
				if len(name) > 48:
					name = name[:48] + "..."  # limit the name string
				names += name + "\n" * (i < movies)
			return names

		def ask4Confirmation(msg):
			self.checkHideMiniTV_beforeFullscreen()
			self.session.openWithCallback(
				self.delayDeleteMovieConfirmed,
				MessageBox,
				msg,
				MessageBox.TYPE_YESNO
			)

		delete_list = self.delete_file_list + self.delete_dir_list + self.delete_link_list
		delete_permanently = len(delete_list) > 0
		if (config.MVC.movie_trashcan_enable.value and config.MVC.movie_delete_validation.value) or delete_permanently:
			msg = [_("Delete"), _("Permanently delete")][delete_permanently]
			names = movieList(delete_list)
			msg += " " + _("the selected video file(s), dir(s), link(s)") + "?\n" + names
			ask4Confirmation(msg)
		else:
			self.delayDeleteMovieConfirmed(True)

	def delayDeleteMovieConfirmed(self, confirmed):
		print("MVC: MovieOps: delayDeleteMovieConfirmed: confirmed: %s" % confirmed)
		delay = [0, 500][self.stoppedRecordings]
		DelayedFunction(delay, boundFunction(self.deleteMovieConfirmed, confirmed))

	def deleteMovieConfirmed(self, confirmed):
		print("MVC: MovieOps: deleteMovieConfirmed: confirmed: %s" % confirmed)
		if confirmed:
			self.execFileOp("delete", self.delete_file_list)
			self.execFileOp("delete_dir", self.delete_dir_list)
			self.execFileOp("delete_link", self.delete_link_list)
			self.execFileOp("move", self.trashcan_file_list, config.MVC.movie_trashcan_path.value)
			self.execFileOp("move_dir", self.trashcan_dir_list, config.MVC.movie_trashcan_path.value)
			self.execFileOp("move_link", self.trashcan_link_list, config.MVC.movie_trashcan_path.value)

	def deleteCallback(self, service):
		print("MVC: MovieOps: deleteCallback: service.getPath(): " + str(service.getPath()))
		self["list"].highlightService(False, "del", service)  # remove the highlight
		if not config.MVC.movie_hide_del.value:
			self.removeService(service)
			self.setReturnCursor()
		self.updateInfo()

	###  Move

	def moveMovie(self):
		# Avoid starting move and copy at the same time
		#WORKAROUND E2 doesn't send dedicated short or long pressed key events
		if self.move is False:
			self.move = True
		else:
			self.move_file_list = []
			self.move_dir_list = []
			self.move_link_list = []
			selection_list = self.getSelectionList()
			for service in selection_list:
				path = service.getPath()
				print("MVC: MovieOps: moveTargetDirSelected: %s" % path)
				if os.path.isfile(path):
					self.move_file_list.append(service)
				elif os.path.isdir(path):
					self.move_dir_list.append(service)
				elif os.path.islink(path):
					self.move_link_list.append(service)
			self.selectDirectory(
				self.moveTargetDirSelected,
				_("Move file(s)")
			)

	def moveTargetDirSelected(self, target_path):
		print("MVC: MovieOps: moveTargetDirSelected: target_path:" + str(target_path))
		if target_path:
			self.execFileOp("move", self.move_file_list, target_path)
			self.execFileOp("move_dir", self.move_dir_list, target_path)
			self.execFileOp("move_link", self.move_link_list, target_path)

	def moveCallback(self, service):
		print("MVC: MovieOps: moveCallback: service.getPath(): " + str(service.getPath()))
		self["list"].highlightService(False, "move", service)  # remove the highlight
		if not config.MVC.movie_hide_mov.value:
			self.removeService(service)
			self.setReturnCursor()
		self.updateInfo()

	### Copy

	def copyMovie(self):
		# Avoid starting move and copy at the same time
		self.move = False
		self.selectDirectory(
			self.copyDirSelected,
			_("Copy file(s)"),
		)

	def copyDirSelected(self, target_path):
		print("MVC: MovieOps: copyDirSelected")
		if target_path:
			selection_list = self.getSelectionList()
			self.execFileOp("copy", selection_list, target_path)

	def copyCallback(self, service):
		print("MVC: MovieOps: copyCallback: service.getPath(): " + str(service.getPath()))
		self["list"].highlightService(False, "copy", service)	# remove the highlight
		self["list"].invalidateService(service)
		self.setReturnCursor()
		self.updateInfo()

	# Trashcan

	def emptyTrashcan(self):
		self.session.openWithCallback(
			self.emptyTrashcanConfirmed,
			MessageBox,
			_("Permanently delete all files in trashcan?"),
			MessageBox.TYPE_YESNO
		)

	def emptyTrashcanConfirmed(self, confirmed):
		if confirmed:
			self.purgeTrashcan(empty_trash=True)

	### Bookmark

	def deleteBookmark(self, service):
		if service:
			if self.isBookmark(service.getPath()):
				if config.MVC.movie_delete_validation.value:
					self.checkHideMiniTV_beforeFullscreen()
					self.session.openWithCallback(
						boundFunction(self.deleteBookmarkConfirmed, service),
						MessageBox,
						_("Do you really want to remove bookmark?") + "\n" + service.getPath()
					)
				else:
					self.deleteBookmarkConfirmed(service, True)

	def deleteBookmarkConfirmed(self, service, confirm):
		if confirm and service:
			self.removeBookmark(service.getPath())
			self.removeServiceOfType(service, cmtBM)
			self.setReturnCursor()

	### Cutlist

	def removeCutListMarker(self):
		selection_list = self.getSelectionList()
		for service in selection_list:
			cuts = CutList(service.getPath())
			cuts.removeMarksCutList()
			self["list"].unselectService(service)
		print("MVC: MovieOps: removeCutListMarker: removed marker")

	def deleteCutListFile(self):
		selection_list = self.getSelectionList()
		for service in selection_list:
			cuts = CutList(service.getPath())
			cuts.deleteFileCutList()
			self["list"].unselectService(service)
		print("MVC: MovieOps: deleteCutListFile: deleted file")
