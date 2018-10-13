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
from Components.config import config
from MovieCache import MovieCache
from Tasker import mvcTasker
from Cover import Cover
from RecordingsControl import RecordingsControl


class FileOps(Cover, object):

	def execFileOpDelete(self, c, path, file_type):
		print("MVC: FileOps: execFileOpDelete: path: %s, file_type: %s" % (path, file_type))
		MovieCache.getInstance().delete(path)  # name.ts
		if file_type == "file":
			cover_path = self.getCoverPath(path)
			c.append('rm -f "' + cover_path + '"') # name.jpg or different movie dir
			path, _ext = os.path.splitext(path)
			c.append('rm -f "' + path + '."*')     # name.*
		elif file_type == "dir":
			c.append('rm -rf "' + path + '"')
		elif file_type == "link":
			c.append('rm -f "' + path + '"')
		source_path = os.path.dirname(path)
		dest_path = None
		print("MVC: FileOps: execFileOpDelete: c: %s" % c)
		return c, source_path, dest_path

	def execFileOpMove(self, c, path, target_path, file_type):
		print("MVC: FileOps: execFileOpMove: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		MovieCache.getInstance().move(path, target_path)
		path, _ext = os.path.splitext(path)
		if file_type == "file":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path + '."*')
			c.append('mv "' + path + '."* "' + target_path + '/"')
		elif file_type == "dir":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path)
			c.append('mv "' + path + '" "' + target_path + '"')
		elif file_type == "link":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path)
			c.append('mv "' + path + '" "' + target_path + '"')
		source_path = os.path.dirname(path)
		dest_path = target_path
		print("MVC: FileOps: execFileOpMove: c: %s" % c)
		return c, source_path, dest_path

	def execFileOpCopy(self, c, path, target_path):
		print("MVC: FileOps: execFileOpCopy: path: %s, target_path: %s" % (path, target_path))
		MovieCache.getInstance().copy(path, target_path)
		path, _ext = os.path.splitext(path)
		c.append('cp "' + path + '."* "' + target_path + '/"')
		source_path = os.path.dirname(path)
		dest_path = target_path
		print("MVC: FileOps: execFileOpCopy: c: %s" % (c))
		return c, source_path, dest_path

	def moveTimerPath(self, service, target_path):
		path = service.getPath()
		if RecordingsControl.isRecording(path):
			RecordingsControl.fixTimerPath(path, os.path.join(target_path, os.path.basename(path)))

	def execFileOp(self, op, selection_list, target_path=None):

		def changeOwner(c, service, target_path):
			if self.mountpoint(target_path) != self.mountpoint(config.MVC.movie_homepath.value):  # CIFS to HDD is ok!
				# need to change file ownership to match target filesystem file creation
				tfile = "\"" + target_path + "/owner_test" + "\""
				path = service.getPath().replace("'", "\'")
				sfile = "\"" + path + ".\"*"
				c.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
			return c

		self.returnService = self.getNextSelectedService(self.getCurrent(), selection_list)
		if self.returnService:
			print("MVC: FileOps: execFileOp: returnService: " + str(self.returnService.toString()))
		else:
			print("MVC: FileOps: execFileOp: op: %s" % (op))
			print("MVC: FileOps: execFileOp: target_path: " + target_path)
			print("MVC: FileOps: execFileOp: selection_list: %s" % (selection_list))

		cmd = []
		association = []
		source_path = None
		dest_path = None
		delete_ops = ["delete", "delete_dir", "delete_link"]
		move_ops = ["move", "move_dir", "move_link"]

		if target_path:
			target_path = os.path.normpath(target_path)

		for service in selection_list:
			if service.getPath():
				c = []
				if op in delete_ops:
					file_type = ["file", "dir", "link"][delete_ops.index(op)]
					# direct delete from the trashcan or network mount (no copy to trashcan from different mountpoint)
					print("MVC: FileOps: execFileOp: delete: directDelete")
					c, source_path, dest_path = self.execFileOpDelete(c, service.getPath(), file_type)
					cmd.append(c)
					self["list"].highlightService(True, "del", service)
					if config.MVC.movie_hide_del.value:
						self.removeService(service)
						self.setReturnCursor()
					association.append((self.deleteCallback, service))
				elif op in move_ops:
					file_type = ["file", "dir", "link"][move_ops.index(op)]
					if os.path.dirname(service.getPath()) != target_path:
						free = 0
						size = 0
						if file_type != "file":
							_count, size = MovieCache.getInstance().getCountSize(service.getPath())
							free = self.getMountPointSpaceFree(target_path)
							print("MVC: FileOps: move_dir: size: %s, free: %s" % (size, free))
						if free >= size:
							c = changeOwner(c, service, target_path)
							c, source_path, dest_path = self.execFileOpMove(c, service.getPath(), target_path, file_type)
							cmd.append(c)
							association.append((self.moveCallback, service))
							self["list"].highlightService(True, "move", service)
							if config.MVC.movie_hide_mov.value:
								self.removeService(service)
								self.setReturnCursor()
							if file_type == "file":
								self.moveTimerPath(service, target_path)
						else:
							print("MVC: FileOps: move_dir: not enough space left: size: %s, free: %s" % (size, free))

				elif op == "copy":
					if os.path.dirname(service.getPath()) != target_path:
						c = changeOwner(c, service, target_path)
						c, source_path, dest_path = self.execFileOpCopy(c, service.getPath(), target_path)
						cmd.append(c)
						association.append((self.copyCallback, service))	# put in a callback for this particular movie
						self["list"].highlightService(True, "copy", service)

		if cmd:
			print("MVC: FileOps: execFileOp: cmd: %s" % cmd)
			association.append((self.initCursor, False)) # Set new Cursor position
			association.append((self.postFileOp, source_path, dest_path))
			# Sync = True: Run script for one file do association and continue with next file
			mvcTasker.shellExecute(cmd, association, True)	# first move, then delete if expiration limit is 0

		self["list"].resetSelection()
		self.getMountPointsSpaceUsedPercent()

	def postFileOp(self, source_path, dest_path):
		print("MVC: FileOps: postFileOp: source_path: %s, dest_path: %s, current_path: %s" % (source_path, dest_path, self.current_path))
		# reload list to get the new index, otherwise you can not select again after that
		for path in [source_path, dest_path]:
			if path == self.current_path:
				self.reloadList(path)
				break
