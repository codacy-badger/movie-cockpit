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

import os
from Components.config import config

class MountPoints(object):

	space_used_percent = []

	def __init__(self):
		print("MVC: MountPoints: __init__")
		MountPoints.space_used_percent = self.getMountPointsSpaceUsedPercent()

	def __dfCommand(self, path):
		import subprocess
		df = subprocess.Popen(["df", path], stdout=subprocess.PIPE)
		output = df.communicate()[0]
		_device, _size, _used, available, percent, _mountpoint = output.split("\n")[1].split()
		return percent, available

	def mountpoint(self, path, first=True):
		if first:
			path = os.path.realpath(path)
		if os.path.ismount(path) or len(path) == 0:
			return path
		return self.mountpoint(os.path.dirname(path), False)

	def getMountPointsSpaceUsedPercent(self):
		MountPoints.space_used_percent = []
		for videodir in config.movielist.videodirs.value:
			mount = self.mountpoint(videodir)
			space_used = self.getMountPointSpaceUsedPercent(mount)
			MountPoints.space_used_percent.append((mount, space_used))
		print("MVC: MountPoints: getMountPointsSpaceUsedPercent: MountPoints.space_used_percent: %s" % MountPoints.space_used_percent)
		return MountPoints.space_used_percent

	def getMountPointSpaceUsedPercent(self, path):
		space_used_percent = "?"
		if os.path.exists(path):
			percent, _available = self.__dfCommand(path)
			space_used_percent = str(percent)
		return space_used_percent

	def getMountPointSpaceFree(self, path):
		available = 0
		if os.path.exists(path):
			_percent, available = self.__dfCommand(path)
			space_free = available * 1024
		return space_free
