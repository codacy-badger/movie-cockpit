#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#        This program is free software: you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#        GNU General Public License for more details.
#
#        For more information on the GNU General Public License see:
#        <http://www.gnu.org/licenses/>.
#

import os
import re
from Components.config import config
from Components.AVSwitch import AVSwitch
from enigma import ePicLoad, gPixmapPtr
from Bookmarks import Bookmarks

class Cover(Bookmarks, object):
	def downloadCover(self, cover_url, cover_path):
		if cover_url is not None:
			if os.path.isfile(cover_path):
				os.remove(cover_path)
			try:
				print("MVC: Cover: downloadCover: url: %s, cover_path: %s" % (cover_url, cover_path))
				os.system("wget -O \"" + cover_path + "\" " + cover_url)
			except Exception as e:
				print('MVC: Cover: downloadCover: exception failure:\n', str(e))
		else:
			print("MVC: Cover: downloadCover: cover_url is None")

	def deleteCover(self, cover_path):
		try:
			os.remove(cover_path)
		except Exception as e:
			print("MVC: Cover: deleteCover: exception:\n" + str(e))

	def getCoverPath(self, path):
		print("MVC: Cover: getCoverPath: path: " + path)
		file_format = "(\.ts|\.avi|\.mkv|\.divx|\.f4v|\.flv|\.img|\.iso|\.m2ts|\.m4v|\.mov|\.mp4|\.mpeg|\.mpg|\.mts|\.vob|\.asf|\.wmv|.\stream|.\webm)"
		cover_path = re.sub(file_format + "$", '.jpg', path, flags=re.IGNORECASE)
		if config.MVC.cover_flash.value:
			bookmarks = self.getBookmarks()
			for bookmark in bookmarks:
				if cover_path.find(bookmark) == 0:
					cover_relpath = cover_path[len(bookmark):]
			cover_path = config.MVC.cover_bookmark.value + cover_relpath
		print("MVC: Cover: getCoverPath: cover_path: " + cover_path)
		return cover_path

	def displayCover(self, cover_path, cover_ptr, nocover_path=None):
		print("MVC: Cover: displayCover: cover_path: %s, nocover_path: %s" % (cover_path, nocover_path))
		self.cover_ptr = cover_ptr
		path = nocover_path
		if os.path.exists(cover_path):
			path = cover_path

		if path is not None and self.cover_ptr is not None:
			print("MVC: Cover: displayCover: showing cover now")
			scale = AVSwitch().getFramebufferScale()
			size = self.cover_ptr.instance.size()
			self.cover_ptr.instance.setPixmap(gPixmapPtr())
			self.picload = ePicLoad()
			self.picload_conn = self.picload.PictureData.connect(self.displayCoverCallback)
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, config.MVC.cover_background.value))
			self.picload.startDecode(path, True)

	def displayCoverCallback(self, picinfo=None):
		print("MVC: Cover: displayCoverCallback")
		if self.picload and picinfo:
			ptr = self.picload.getData()
			if ptr:
				self.cover_ptr.instance.setPixmap(ptr)
