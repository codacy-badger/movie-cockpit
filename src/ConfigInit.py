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

from __init__ import _
from Components.config import config, ConfigText, ConfigSelection, ConfigSelectionNumber, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave
from Components.Language import language
from Tools.ISO639 import ISO639Language


class Autoselect639Language(ISO639Language, object):

	def __init__(self):
		ISO639Language.__init__(self, self.TERTIARY)

	def getTranslatedChoicesDictAndSortedListAndDefaults(self):
		syslang = language.getLanguage()[:2]
		choices_dict = {}
		choices_list = []
		defaults = []
		for lang, id_list in self.idlist_by_name.iteritems():
			if syslang not in id_list and 'en' not in id_list:
				name = _(lang)
				short_id = sorted(id_list, key=len)[0]
				choices_dict[short_id] = name
				choices_list.append((short_id, name))
		choices_list.sort(key=lambda x: x[1])
		syslangname = _(self.name_by_shortid[syslang])
		choices_list.insert(0, (syslang, syslangname))
		choices_dict[syslang] = syslangname
		defaults.append(syslang)
		if syslang != "en":
			enlangname = _(self.name_by_shortid["en"])
			choices_list.insert(1, ("en", enlangname))
			choices_dict["en"] = enlangname
			defaults.append("en")
		return (choices_dict, choices_list, defaults)


def langList():
	iso639 = Autoselect639Language()
	newlist = iso639.getTranslatedChoicesDictAndSortedListAndDefaults()[1]
	return newlist


def langListSel():
	iso639 = Autoselect639Language()
	newlist = iso639.getTranslatedChoicesDictAndSortedListAndDefaults()[0]
	return newlist


launch_choices = [
	("None",		_("No override")),
	("showMovies",		_("Video-button")),
	("showTv",		_("TV-button")),
	("showRadio",		_("Radio-button")),
	("openQuickbutton",	_("Quick-button")),
	("timeshiftStart",	_("Timeshift-button"))
]

# Date format is implemented using datetime.strftime
date_choices = [
	("%d.%m.%Y",		_("DD.MM.YYYY")),
	("%a %d.%m.%Y",		_("WD DD.MM.YYYY")),

	("%d.%m.%Y %H:%M",	_("DD.MM.YYYY HH:MM")),
	("%a %d.%m.%Y %H:%M",	_("WD DD.MM.YYYY HH:MM")),

	("%d.%m. %H:%M",	_("DD.MM. HH:MM")),
	("%a %d.%m. %H:%M",	_("WD DD.MM. HH:MM")),

	("%Y/%m/%d",		_("YYYY/MM/DD")),
	("%a %Y/%m/%d",		_("WD YYYY/MM/DD")),

	("%Y/%m/%d %H:%M",	_("YYYY/MM/DD HH:MM")),
	("%a %Y/%m/%d %H:%M",	_("WD YYYY/MM/DD HH:MM")),

	("%m/%d %H:%M",		_("MM/DD HH:MM")),
	("%a %m/%d %H:%M",	_("WD MM/DD HH:MM"))
]

dirinfo_choices = [
	("",	_("off")),
	("D",	_("Description")),	# Description
	("C",	_("(#)")),		# Count
	("CS",	_("(#/GB)")),		# Count / Size
	("S",	_("(GB)"))		# Size
]

progress_choices = [
	("PB",	_("Progress Bar")),
	("P",	_("Percent (%)")),
	("",	_("off"))
]

colorbutton_choices = [
	("MH",	_("Movie Home")),
	("DL",	_("Delete")),
	("MV",	_("Move File")),
	("CS",	_("Cover Search")),
	("MI",	_("Download Movie Info")),
	("CP",	_("Copy File")),
	("E2",	_("Open Bookmarks")),
	("TC",	_("Toggle Cover Button")),
	("",	_("Button disabled"))
]

red_choices = colorbutton_choices
green_choices = colorbutton_choices.append(("ST", _("Sort Options")))
yellow_choices = colorbutton_choices
blue_choices = colorbutton_choices

longcolorbutton_choices = colorbutton_choices
longred_choices = longcolorbutton_choices
longyellow_choices = longcolorbutton_choices
longblue_choices = longcolorbutton_choices

move_choices = [
	("d", _("down")),
	("b", _("up/down")),
	("o", _("off"))
]

cover_background_choices = [
	("#00000000",	_("type 1 - OSD + black (#00000000)")),
	("#FFFFFFFF",	_("type 2 - transparent + white (#FFFFFFFF)")),
	("#00FFFFFF",	_("type 3 - OSD + black (#00FFFFFF)")),
	("#FF000000",	_("type 4 - transparent + black (#FF000000)"))
]

bqt_choices = [
	("", 		_("Home/End")),
	("Skip", 	_("Skip")),
	("Folder", 	_("Change Folder"))
]

sort_modes = {
	("D-"): (("D", False),	_("Date sort down")),
	("AZ"): (("A", False),	_("Alpha sort up")),
	("D+"): (("D", True), 	_("Date sort up")),
	("ZA"): (("A", True),	_("Alpha sort down"))
}

#	If you add a new sort order, you have to think about
#	Order false has to be the preferred state
#	Both order possibilities should be in the list
#	Following functions are invoved, but they are all implemented dynamically
#	MovieCenter.reload -> Add new parameter if necessary
#	Don't worry about buildMovieCenterEntry(*args):
#	MovieSelection.initButtons -> Set next button text
#	Green short will go through all types: D A
#	Green long will only toggle the sort order: normal reverse

sort_choices = [(k, v[1]) for k, v in sort_modes.items()]


class ConfigInit(object):

	def checkList(self, cfg):
		for choices in cfg.choices.choices:
			if cfg.value == choices[0]:
				return
		for choices in cfg.choices.choices:
			if cfg.default == choices[0]:
				cfg.value = cfg.default
				return
		cfg.value = cfg.choices.choices[0][0]

	def __init__(self):
		print("MVC: ConfigInit: __init__: constructor")
		config.MVC                           = ConfigSubsection()
		config.MVC.fake_entry                = NoSave(ConfigNothing())
		config.MVC.needsreload               = ConfigYesNo(default=False)
		config.MVC.extmenu_plugin            = ConfigYesNo(default=True)
		config.MVC.extmenu_list              = ConfigYesNo(default=True)
		config.MVC.epglang                   = ConfigSelection(default=language.getActiveLanguage(), choices=langList())
		config.MVC.sublang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.sublang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.sublang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.autosubs                  = ConfigYesNo(default=False)
		config.MVC.autoaudio                 = ConfigYesNo(default=False)
		config.MVC.autoaudio_ac3             = ConfigYesNo(default=False)
		config.MVC.ml_disable                = ConfigYesNo(default=False)
		config.MVC.movie_redfunc             = ConfigSelection(default="DL", choices=red_choices)
		config.MVC.movie_greenfunc           = ConfigSelection(default="ST", choices=green_choices)
		config.MVC.movie_yellowfunc          = ConfigSelection(default="MV", choices=yellow_choices)
		config.MVC.movie_bluefunc            = ConfigSelection(default="MH", choices=blue_choices)
		config.MVC.movie_longredfunc         = ConfigSelection(default="DL", choices=longred_choices)
		config.MVC.movie_longyellowfunc      = ConfigSelection(default="MV", choices=longyellow_choices)
		config.MVC.movie_longbluefunc        = ConfigSelection(default="MH", choices=longblue_choices)
		config.MVC.MVCStartHome              = ConfigYesNo(default=True)
		config.MVC.movie_descdelay           = ConfigSelectionNumber(50, 60000, 50, default=200)
		config.MVC.cover                     = ConfigYesNo(default=False)
		config.MVC.cover_flash               = ConfigYesNo(default=False)
		config.MVC.cover_bookmark            = ConfigText(default="/data/movie", fixed_size=False, visible_width=22)
		config.MVC.cover_delay               = ConfigSelectionNumber(50, 60000, 50, default=250)
		config.MVC.cover_background          = ConfigSelection(default="#00000000", choices=cover_background_choices)
		config.MVC.cover_fallback            = ConfigYesNo(default=False)
		config.MVC.cover_language            = ConfigSelection(default='de', choices=[('en', _('English')), ('de', _('German')), ('it', _('Italian')), ('es', _('Spanish')), ('fr', _('French')), ('pt', _('Portuguese'))])
		config.MVC.cover_size                = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
		config.MVC.hide_miniTV               = ConfigSelection(default='never', choices=[('never', _("never hide")), ('liveTV', _("hide live TV")), ('liveTVorTS', _("hide live TV and timeshift")), ('playback', _("hide playback")), ('all', _("always hide"))])
		config.MVC.cover_hide_miniTV         = ConfigYesNo(default=False)
		config.MVC.cover_auto_selection      = ConfigYesNo(default=False)
		config.MVC.skinstyle                 = ConfigSelection(default='right', choices=[('right', _("Show info on the right")), ('rightpig', _("Show info on the right (with MiniTV)")), ('custom', _("Show custom layout ('Selection_myskin.xml')"))])
		config.MVC.movie_icons               = ConfigYesNo(default=True)
		config.MVC.link_icons                = ConfigYesNo(default=True)
		config.MVC.movie_picons              = ConfigYesNo(default=False)
		config.MVC.movie_picons_path         = ConfigText(default="/usr/share/enigma2/picon", fixed_size=False, visible_width=35)
		config.MVC.movie_progress            = ConfigSelection(default="PB", choices=progress_choices)
		config.MVC.movie_watching_percent    = ConfigSelectionNumber(0, 30, 1, default=10)
		config.MVC.movie_finished_percent    = ConfigSelectionNumber(50, 100, 1, default=90)
		config.MVC.movie_date_format         = ConfigSelection(default="%d.%m.%Y %H:%M", choices=date_choices)
		config.MVC.movie_ignore_firstcuts    = ConfigYesNo(default=True)
		config.MVC.movie_jump_first_mark     = ConfigYesNo(default=False)
		config.MVC.movie_rewind_finished     = ConfigYesNo(default=True)
		config.MVC.record_eof_zap            = ConfigSelection(default='1', choices=[('0', _("yes, without Message")), ('1', _("yes, with Message")), ('2', _("no"))])
		config.MVC.movie_exit                = ConfigYesNo(default=False)
		config.MVC.movie_reopen              = ConfigYesNo(default=True)
		config.MVC.movie_reopenEOF           = ConfigYesNo(default=True)
		config.MVC.movie_show_format         = ConfigYesNo(default=False)
		config.MVC.movie_real_path           = ConfigYesNo(default=True)
		config.MVC.movie_homepath            = ConfigText(default="/media/hdd/movie", fixed_size=False, visible_width=22)
		config.MVC.movie_pathlimit           = ConfigText(default="/movie", fixed_size=False, visible_width=22) # relative to mount point e.g. /media/hdd
		config.MVC.movie_trashcan_enable     = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_path       = ConfigText(default="/media/hdd/movie/trashcan", fixed_size=False, visible_width=22)
		config.MVC.movie_trashcan_show       = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_info       = ConfigSelection(default="C", choices=dirinfo_choices)
		config.MVC.movie_trashcan_clean      = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_limit      = ConfigSelectionNumber(1, 99, 1, default=3)
		config.MVC.movie_delete_validation   = ConfigYesNo(default=True)
		config.MVC.directories_show          = ConfigYesNo(default=False)
		config.MVC.directories_ontop         = ConfigYesNo(default=False)
		config.MVC.directories_info          = ConfigSelection(default="", choices=dirinfo_choices)
		config.MVC.count_size_position       = ConfigSelection(default='0', choices=[('0', _("center")), ('1', _("right")), ('2', _("left"))])
		config.MVC.color_recording           = ConfigSelection(default="#ff0000", choices=[("#ffff00", _("Yellow")), ("#ff0000", _("Red")), ("#ff9999", _("Light red")), ("#990000", _("Dark red"))])
		config.MVC.color_highlight           = ConfigSelection(default="#ffffff", choices=[("#ffffff", _("White")), ("#cccccc", _("Light grey")), ("#bababa", _("Grey")), ("#666666", _("Dark grey")), ("#000000", _("Black"))])
		config.MVC.bookmarks                 = ConfigYesNo(default=False)
		config.MVC.movie_hide_mov            = ConfigYesNo(default=False)
		config.MVC.movie_hide_del            = ConfigYesNo(default=False)
		config.MVC.moviecenter_sort          = ConfigSelection(default=("D-"), choices=sort_choices)
		config.MVC.moviecenter_selmove       = ConfigSelection(default="d", choices=move_choices)
		config.MVC.moviecenter_loadtext      = ConfigYesNo(default=True)
		config.MVC.timer_autoclean           = ConfigYesNo(default=False)
		config.MVC.movie_launch              = ConfigSelection(default="showMovies", choices=launch_choices)
#		config.MVC.scan_linked               = ConfigYesNo(default=False)
		config.MVC.bqt_keys                  = ConfigSelection(default="", choices=bqt_choices)
		config.MVC.list_skip_size            = ConfigSelectionNumber(3, 10, 1, default=5)
		config.MVC.InfoLong                  = ConfigSelection(default="MVC-TMDBInfo", choices=[("", _("Button disabled")), ("IMDbSearch", _("IMDb Search")), ("MVC-TMDBInfo", _("MVC-TMDB Info")), ("TMDBInfo", _("TMDB Info")), ('CSFDInfo', _('CSFD Info'))])

		self.checkList(config.MVC.epglang)
		self.checkList(config.MVC.sublang1)
		self.checkList(config.MVC.sublang2)
		self.checkList(config.MVC.sublang3)
		self.checkList(config.MVC.audlang1)
		self.checkList(config.MVC.audlang2)
		self.checkList(config.MVC.audlang3)
