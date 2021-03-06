﻿#!/usr/bin/python
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

from operator import isCallable
from enigma import eTimer

instanceTab = []  # just seems to be required to keep the instances alive long enough


class DelayedFunction(object):

	def __init__(self, delay, function, *params):
		if isCallable(function):
			global instanceTab
			instanceTab.append(self)
			self.function = function
			self.params = params
			self.timer = None
			self.timer = eTimer()
			self.timer_conn = None
			self.timer_conn = self.timer.timeout.connect(self.timerLaunch)
			self.timer.start(delay, False)

	def cancel(self):
		global instanceTab
		instanceTab.remove(self)
		self.timer.stop()
		self.timer_conn = None
		self.timer = None

	def timerLaunch(self):
		global instanceTab
		instanceTab.remove(self)
		self.timer.stop()
		self.timer_conn = None
		self.timer = None
		self.function(*self.params)

	def exists(self):
		return self in instanceTab
