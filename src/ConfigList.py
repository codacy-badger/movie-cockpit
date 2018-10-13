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

from __init__ import _
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.HTMLComponent import HTMLComponent
from Components.GUIComponent import GUIComponent
from Components.config import KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_0, KEY_DELETE, KEY_BACKSPACE, KEY_OK, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT, KEY_NUMBERS, ConfigElement, ConfigText, ConfigPassword
from Components.ActionMap import NumberActionMap, ActionMap
from enigma import eListbox, eListboxPythonConfigContent, eTimer, ePoint
from skin import componentSizes


class ConfigList(HTMLComponent, GUIComponent, object):

	def __init__(self, alist, session=None):
		GUIComponent.__init__(self)
		self.l = eListboxPythonConfigContent()
		sizes = componentSizes[componentSizes.CONFIG_LIST]
		self.l.setSeperation(sizes.get("seperation", 400))
		self.l.setDividerHeight(sizes.get("dividerHeight", 2))
		self.timer = eTimer()
		self._headers = []
		self.list = alist
		self.onSelectionChanged = []
		self.current = None
		self.session = session

	def execBegin(self):
		self.timer_conn = self.timer.timeout.connect(self.timeout)

	def execEnd(self):
		self.timer_conn = None

	def toggle(self):
		selection = self.getCurrent()
		selection[1].toggle()
		self.invalidateCurrent()

	def handleKey(self, key):
		selection = self.getCurrent()
		if selection and selection[1].enabled:
			selection[1].handleKey(key)
			self.invalidateCurrent()
			if key in KEY_NUMBERS:
				self.timer.start(1000, 1)

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def getCurrentIndex(self):
		return self.l.getCurrentSelectionIndex()

	def setCurrentIndex(self, index):
		if self.instance:
			self.instance.moveSelectionTo(index)

	def invalidateCurrent(self):
		self.l.invalidateEntry(self.l.getCurrentSelectionIndex())

	def invalidate(self, entry):
		if entry in self.alist:
			self.l.invalidateEntry(self.alist.index(entry))

	GUI_WIDGET = eListbox

	def selectionChanged(self):
		if isinstance(self.current, tuple) and len(self.current) > 1:
			self.current[1].onDeselect(self.session)
		self.current = self.getCurrent()
		if isinstance(self.current, tuple) and len(self.current) > 1:
			self.current[1].onSelect(self.session)
		else:
			return
		for x in self.onSelectionChanged:
			x()

	def postWidgetCreate(self, instance):
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		instance.setContent(self.l)

	def preWidgetRemove(self, instance):
		if isinstance(self.current, tuple) and len(self.current) > 1:
			self.current[1].onDeselect(self.session)
		self.selectionChanged_conn = None
		instance.setContent(None)

	def setList(self, l):
		self.timer.stop()
		self.alist = l
		self.l.setList(self.alist)
		self._headers = []
		self._fake = []
		if l:
			index = 0
			for x in l:
				if len(x) < 2:
					self._headers.append(index)
				elif len(x[0]) < 1:
					self._fake.append(index)
				else:
					if not isinstance(x[1], ConfigElement):
						print("MVC: ConfigList: setList: entry is not a ConfigElement: " + str(x[1]))
						raise AssertionError()
				index += 1

	def pageUp(self):
		self.instance.moveSelection(eListbox.pageUp)

	def pageDown(self):
		self.instance.moveSelection(eListbox.pageDown)

	def jumpToNextSection(self):
		index = self.getCurrentIndex()
		maxlen = len(self.alist)
		while index < maxlen - 1:
			index += 1
			if index in self._headers:
				if index + 1 < maxlen:
					self.setCurrentIndex(index + 1)
					return
				else:
					self.setCurrentIndex(index - 1)
					return
		self.pageDown()

	def jumpToPreviousSection(self):
		index = self.getCurrentIndex() - 1
		maxlen = len(self.alist)
		while index >= 0 and maxlen > 0:
			index -= 1
			if index in self._headers:
				if index + 1 < maxlen:
					self.setCurrentIndex(index + 1)
					return
				else:
					self.setCurrentIndex(index - 1)
					return
		self.pageUp()

	def up(self):
		self.instance.moveSelection(eListbox.moveUp)
		index = self.getCurrentIndex()
		if index in self._fake:
			self.instance.moveSelection(eListbox.moveUp)

	def down(self):
		self.instance.moveSelection(eListbox.moveDown)
		index = self.getCurrentIndex()
		if index in self._fake:
			self.instance.moveSelection(eListbox.moveDown)

	def getList(self):
		return self.alist

	list = property(getList, setList)

	def timeout(self):
		self.handleKey(KEY_TIMEOUT)

	def isChanged(self):
		is_changed = False
		for x in self.list:
			if len(x) > 1:
				if x[1]:
					is_changed |= x[1].isChanged()
				else:
					print("MVC: ConfigList: ERROR: x[1] is None")
		return is_changed


class ConfigListScreen:

	def __init__(self, plist, session=None, on_change=None):
		self["config_actions"] = NumberActionMap(
			["SetupActions", "InputAsciiActions", "KeyboardInputActions"],
			{
				"gotAsciiCode": self.keyGotAscii,
				"ok": self.keyOK,
				"left": self.keyLeft,
				"right": self.keyRight,
				"home": self.keyHome,
				"end": self.keyEnd,
				"up": self.keyUp,
				"down": self.keyDown,
				"deleteForward": self.keyDelete,
				"deleteBackward": self.keyBackspace,
				"toggleOverwrite": self.keyToggleOW,
				"nextBouquet": self.keyPreviousSection,
				"prevBouquet": self.keyNextSection,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal
			},
			-1
		)

		self["VirtualKB"] = ActionMap(
			["VirtualKeyboardActions"],
			{
				"showVirtualKeyboard": self.KeyText,
			},
			-2
		)

		self["VirtualKB"].setEnabled(False)

		self["config"] = ConfigList(plist, session=session)

		if on_change:
			self.__changed = on_change
		else:
			self.__changed = lambda: None

		if self.handleInputHelpers not in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.handleInputHelpers)

	def handleInputHelpers(self):
		if self["config"].getCurrent():
			if isinstance(self["config"].getCurrent()[1], ConfigText) or isinstance(self["config"].getCurrent()[1], ConfigPassword):
				self["VirtualKB"].setEnabled(True)
				if "HelpWindow" in self:
					if self["config"].getCurrent()[1].help_window.instance:
						helpwindowpos = self["HelpWindow"].getPosition()
						self["config"].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0], helpwindowpos[1]))
			else:
				self["VirtualKB"].setEnabled(False)
		else:
			self["VirtualKB"].setEnabled(False)

	def KeyText(self):
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].getValue())

	def VirtualKeyBoardCallback(self, callback=None):
		if callback and len(callback):
			self["config"].getCurrent()[1].setValue(callback)
			self["config"].invalidate(self["config"].getCurrent())

	def keyOK(self):
		self["config"].handleKey(KEY_OK)

	def keyLeft(self):
		self["config"].handleKey(KEY_LEFT)
		self.__changed()

	def keyRight(self):
		self["config"].handleKey(KEY_RIGHT)
		self.__changed()

	def keyHome(self):
		self["config"].handleKey(KEY_HOME)
		self.__changed()

	def keyEnd(self):
		self["config"].handleKey(KEY_END)
		self.__changed()

	def keyDelete(self):
		self["config"].handleKey(KEY_DELETE)
		self.__changed()

	def keyBackspace(self):
		self["config"].handleKey(KEY_BACKSPACE)
		self.__changed()

	def keyToggleOW(self):
		self["config"].handleKey(KEY_TOGGLEOW)
		self.__changed()

	def keyGotAscii(self):
		self["config"].handleKey(KEY_ASCII)
		self.__changed()

	def keyNumberGlobal(self, number):
		self["config"].handleKey(KEY_0 + number)
		self.__changed()

	def keyPreviousSection(self):
		self["config"].jumpToPreviousSection()

	def keyNextSection(self):
		self["config"].jumpToNextSection()

	def keyUp(self):
		self["config"].up()

	def keyDown(self):
		self["config"].down()

	def saveAll(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()

	def keySave(self):
		self.saveAll()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			if len(x) > 1:
				x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()
