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

from enigma import eConsoleAppContainer
from collections import Callable, deque
from pipes import quote
from itertools import izip_longest


class Executioner(object):

	def __init__(self, _identifier):
		self.container = eConsoleAppContainer()
		try:
			self.container_appClosed_conn = self.container.appClosed.connect(self.runFinished)
			# this will cause interfilesystem transfers to stall Enigma
			self.container_dataAvail_conn = self.container.dataAvail.connect(self.dataAvail)
		except Exception:
			self.container_appClosed_conn = None
			self.container_dataAvail_conn = None
			self.container.appClosed.append(self.runFinished)
			self.container.dataAvail.append(self.dataAvail)  # this will cause interfilesystem transfers to stall Enigma
		self.script = deque()
		self.associated = deque()
		self.executing = ""
		self.returnData = ""

	def isIdle(self):
		return len(self.script) == 0

	def shellExecute(self, script, associated=None, sync=False):
		# Parameters:
		#  script = single command:   cmd
		#			list of commands: [cmd, cmd]
		#  associated = single callback: callback
		#				single tuple:    (callback, args)
		#				list of tuples:  [(callback),(callback, args),(...)]
		#    callback = function to be executed
		#    args = single parameter:    arg or (arg) or (a, b) or [a,b]
		#			multiple parameters: arg1, arg2
		#  sync (synchronous callback):
		#    True  = After every command, one callback entry is executed, additionally callbacks will be executed after the last command
		#            If the callback entry is a tuple or list, alle subcallbacks will be executed
		#    False = All callbacks are executed at the end
		if not sync or not isinstance(script, list):
			# Single command execution
			print("MVC: Tasker: shellExecute: single script: " + str(script))
			self.script.append(script)
			self.associated.append(associated)
		else:
			print("MVC: Tasker: shellExecute: list script: " + str(script))
			for s, a in izip_longest(script, associated):
				self.script.append(s)
				self.associated.append([a])

		if self.executing == "":
			print("MVC: Tasker: shellExecute: run script:" + str(self.script))
			self.execCurrent()
		else:
			print("MVC: Tasker: shellExecute: Run after current execution")

	def execCurrent(self):
		script = self.script.popleft()
		if script:
			if isinstance(script, list):
				script = '; '.join(script)
			print("MVC: Tasker: execCurrent: script: " + str(script))
			self.executing = quote(script)
			self.container.execute("sh -c " + self.executing)
			print("MVC: Tasker: execCurrent: executing: " + self.executing)
		else:
			self.runFinished()

	def runFinished(self, retval=None):
		try:
			associated = self.associated.popleft()
			print("MVC: Tasker: runFinished: sh exec %s finished, return status = %s %s" % (self.executing, str(retval), self.returnData))
			if associated:
				#P3 for foo, bar, *other in tuple:
				for fargs in associated:
					try:
						if isinstance(fargs, tuple) or isinstance(fargs, list):
							f, args = [e for e in fargs[:1]] + [fargs[1:]]
							if isinstance(f, Callable):
								if args:
									f(*args)
								else:
									f(args)
						else:
							if isinstance(fargs, Callable):
								fargs()
					except Exception as e:
						print("MVC: Tasker: runFinished: exception:\n" + str(e))
						pass
			self.returnData = ""

			if self.script:
				# There is more to be executed
				print("MVC: Tasker: runFinisched: sh exec rebound")
				self.execCurrent()
			else:
				self.executing = ""

				#TODO MAYBE we want do cleanup the whole container
				#del self.container.dataAvail[:]
				#del self.container.appClosed[:]
				#del self.container

		except Exception as e:
			print("MVC: Tasker: runFinished: exception:\n" + str(e))

	def dataAvail(self, string):
		self.returnData += "\n" + string.replace("\n", "")


class Tasker(object):

	def __init__(self):
		self.minutes = 0
		self.timerActive = False
		self.executioners = []
		#TODO instantiate the executioner as we need them
		self.executioners.append(Executioner("A"))
		self.executioners.append(Executioner("B"))
		self.executioners.append(Executioner("C"))

	def shellExecute(self, script, associated=None, sync=False):
		for x in self.executioners:
			if x.isIdle():
				x.shellExecute(script, associated, sync)
				return
		# all were busy, just append to any task list randomly
		import random
		self.executioners[random.randint(0, 2)].shellExecute(script, associated, sync)


mvcTasker = Tasker()
