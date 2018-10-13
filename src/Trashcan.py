#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 by dream-alpha
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
from time import localtime
from Components.config import config
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup
from DelayedFunction import DelayedFunction
from MovieCache import MovieCache
from MediaTypes import extMedia
from FileOps import FileOps
from MovieCenter import MOVIE_IDX_SERVICE, MOVIE_IDX_PATH


class Trashcan(FileOps, object):

	def __init__(self):
		if self.trashcanExists():
			self.schedulePurge()
		else:
			config.MVC.movie_trashcan_enable.value = False

	def trashcanExists(self):
		trashcan_exists = False
		afile = MovieCache.getInstance().getFile(config.MVC.movie_trashcan_path.value)
		if config.MVC.movie_trashcan_enable.value and afile[MOVIE_IDX_PATH] != "":
			trashcan_exists = True
		return trashcan_exists

	def createTrashcan(self):
		try:
			os.makedirs(config.MVC.movie_trashcan_path.value)
			MovieCache.getInstance().loadDatabaseDir(config.MVC.movie_trashcan_path.value)
			self.reloadList()
		except Exception as e:
			config.MVC.movie_trashcan_enable.value = False
			self.checkHideMiniTV_beforeFullscreen()
			self.session.open(
				MessageBox,
				_("Trashcan creation failed. Check mounts and permissions!"),
				MessageBox.TYPE_ERROR
			)
			print("MVC: Trashcan: createTrashcan: exception:\n" + str(e))

	def enableTrashcan(self):
		print("MVC: Trashcan: enable")
		if not os.path.exists(config.MVC.movie_trashcan_path.value):
			self.createTrashcan()

	def emptyTrashcan(self):
		self.session.openWithCallback(
			self.emptyTrashCallback,
			MessageBox,
			_("Permanently delete all files in trashcan?"),
			MessageBox.TYPE_YESNO
		)

	def emptyTrashcanCallback(self, confirmed):
		if confirmed:
			self.purgeTrashcan(empty_trash=True)

	def purgeTrashcan(self, empty_trash=False):
		print("MVC: Trashcan: purge: empty_trash: %s" % (empty_trash))
		now = localtime()
		if not self.trashcanExists:
			self.createTrashcan()

		if os.path.realpath(config.MVC.movie_trashcan_path.value) in os.path.realpath(config.MVC.movie_homepath.value):
			config.MVC.movie_trashcan_enable.value = False
			AddPopup(
				_("Skipping trashcan cleanup")
				+ "\n"
				+ _("Movie Home path is equal to or a subfolder of the trashcan"),
				MessageBox.TYPE_INFO,
				0,
				"MVC_TRASHCAN_CLEANUP_SKIPPED_ID"
			)
			return

		delete_list = []
		filelist = MovieCache.getInstance().getFileList([config.MVC.movie_trashcan_path.value])
		for afile in filelist:
			service = afile[MOVIE_IDX_SERVICE]
			path = service.getPath()
			# Only check media files
			ext = os.path.splitext(path)[1]
			if ext in extMedia and os.path.exists(path):
				if empty_trash or now > localtime(os.stat(path).st_mtime + 24 * 60 * 60 * int(config.MVC.movie_trashcan_limit.value)):
					print("MVC: Trashcan: purge: path: " + path)
					delete_list.append(service)
		if len(delete_list) > 0:
			print("MVC: Trashcan: deleting files...")
			self.execFileOp("delete", delete_list)
		else:
			print("MVC: Trashcan: purge: nothing to delete")

	def schedulePurge(self):
		if config.MVC.movie_trashcan_enable.value and config.MVC.movie_trashcan_clean.value:
			# Recall setup function in 24 hours
			seconds = 24 * 60 * 60
			DelayedFunction(1000 * seconds, self.schedulePurge)
			# Execute trash cleaning
			DelayedFunction(5000, self.purgeTrashcan)
			print("MVC: Trashcan: scheduleCleanup: next trashcan cleanup in %s minutes" % (seconds / 60))
