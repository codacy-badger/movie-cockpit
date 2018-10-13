#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 dream-alpha
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

import re
import json
from MediaTypes import extVideo, substitutelist
from urllib2 import Request, urlopen
from Cover import Cover
import gettext
try:
	from __init__ import _
except ImportError:
	def _(txt):
		return gettext.dgettext("MovieCockpit", txt) if txt else ""


class TMDB(Cover, object):

	def getMovieNameWithoutExt(self, moviename=""):
		if self.show_format:
			for rem in extVideo:
				rem = rem.replace(".", " ")
				if moviename.lower().endswith(rem):
					moviename = moviename[:-len(rem)]
					break
		return moviename

	def getMovieNameWithoutPhrases(self, moviename=""):
		# Remove phrases which are encapsulated in [*] or (*) from the movietitle
		moviename = re.sub(r'\[.*\]', "", moviename)
		moviename = re.sub(r'\(.*\)', "", moviename)
		moviename = re.sub(r' S\d\dE\d\d .*', "", moviename)
		for (phrase, sub) in substitutelist:
			moviename = moviename.replace(phrase, sub)
		return moviename

	def fetchData(self, url):
		response = None
		retry = 0
		while response is None and retry < 5:
			try:
				headers = {"Accept": "application/json"}
				request = Request(url, headers=headers)
				jsonresponse = urlopen(request).read()
				response = json.loads(jsonresponse)
			except Exception as e:
				print("MVC: Cover: fetchData: exception: " + str(e))
				retry += 1
		return response

	def getMovieList(self, moviename, auto_selection):

		def getMovies(moviename):
			movies_response = self.fetchData("http://api.themoviedb.org/3/search/movie?api_key=3b6703b8734fee1b598de9ed7bbd3b47&query=" + moviename.replace(" ", "+").replace("&", "%26"))
			movielist = []
			if movies_response:
				movies = movies_response["results"]
				for movie in movies:
					print("MVC: TMDB: getMovieList: =============================================")
					print("MVC: TMDB: getMovieList: movie: " + str(movie))
					poster_path = None
					if movie["poster_path"]:
						poster_path = movie["poster_path"].encode('utf-8')
					movielist.append((movie["title"].encode('utf-8') + " - " + _("Movies"), movie["id"], "movie", movie["release_date"].encode('utf-8'), poster_path))
					print("MVC: TMDB: getMovieList: =============================================")
			return movielist

		def getTvShows(moviename):
			tvshows_response = self.fetchData("http://api.themoviedb.org/3/search/tv?api_key=3b6703b8734fee1b598de9ed7bbd3b47&query=" + moviename.replace(" ", "+").replace("&", "%26"))
			tvshowslist = []
			if tvshows_response:
				tvshows = tvshows_response["results"]
				for tvshow in tvshows:
					print("MVC: TMDB: getMovieList: =============================================")
					print("MVC: TMDB: getMovieList: tvshow: " + str(tvshow))
					poster_path = None
					if tvshow["poster_path"]:
						poster_path = tvshow["poster_path"].encode('utf-8')
					tvshowslist.append((tvshow["name"].encode('utf-8') + " - " + _("TV Shows"), tvshow["id"], "tvshow", tvshow["first_air_date"].encode('utf-8'), poster_path))
					print("MVC: TMDB: getMovieList: =============================================")
			return tvshowslist

		movieslist = getMovies(moviename)
		tvshowslist = getTvShows(moviename)

		if auto_selection:
			selected_list = []
			if len(tvshowslist) > 0:
				# first look at tvshowlist
				selection = tvshowslist[0]
				if selection[4] is None:
					# if there is no cover look at movieslist
					if len(movieslist) > 0:
						selection = movieslist[0]
						if selection[4] is None:
							# if there is no cover either select first in tvshowslist
							selected_list.append(tvshowslist[0])
						else:
							selected_list.append(selection)
				else:
					selected_list.append(selection)
			else:
				if len(movieslist) > 0:
					selected_list.append(movieslist[0])
		else:
			selected_list = tvshowslist + movieslist

		return selected_list, len(selected_list)

	def getTMDBInfo(self, p_id, cat, lang):

		def getGenre(response):
			genres = ""
			genrelist = response["genres"]
			for genre in genrelist:
				if genres == "":
					genres = genre["name"]
				else:
					genres = genres + ", " + genre["name"]
			return genres.encode('utf-8')

		def getCountries(response, cat):
			countries = ""
			if cat == "movie":
				countrylist = response["production_countries"]
				for country in countrylist:
					if countries == "":
						countries = country["name"]
					else:
						countries = countries + ", " + country["name"]
			if cat == "tvshow":
				countrylist = response["origin_country"]
				for country in countrylist:
					if countries == "":
						countries = country
					else:
						countries = countries + ", " + country
			return countries.encode('utf-8')

		def getRuntime(response, cat):
			runtime = ""
			if cat == "movie":
				runtime = str(response["runtime"])
				if response["runtime"] == 0:
					runtime = ""
			elif cat == "tvshow":
				if len(response["episode_run_time"]) > 0:
					runtime = str(response["episode_run_time"][0])
					if response["episode_run_time"][0] == 0:
						runtime = ""
			print(runtime)
			return runtime.encode('utf-8')

		def getReleaseDate(response, cat):
			releasedate = ""
			if cat == "movie":
				releasedate = response["release_date"]
			elif cat == "tvshow":
				releasedate = str(response["last_air_date"])
			return releasedate.encode('utf-8')

		def getVote(response):
			vote = str(response["vote_average"])
			if vote == "0.0":
				vote = ""
			return vote.encode('utf-8')

		def parseMovieData(response, cat):
			blurb = response["overview"].encode('utf-8')
			runtime = getRuntime(response, cat)
			releasedate = getReleaseDate(response, cat)
			vote = getVote(response)
			genres = getGenre(response)
			countries = getCountries(response, cat)
			cover_url = response["poster_path"]
			if cover_url is not None:
				cover_url = cover_url.encode('utf-8')
			return blurb, runtime, genres, countries, releasedate, vote, cover_url

		response = None
		if cat == "movie":
			response = self.fetchData("http://api.themoviedb.org/3/movie/" + str(p_id) + "?api_key=3b6703b8734fee1b598de9ed7bbd3b47&language=" + lang)
		if cat == "tvshow":
			response = self.fetchData("http://api.themoviedb.org/3/tv/" + str(p_id) + "?api_key=3b6703b8734fee1b598de9ed7bbd3b47&language=" + lang)

		if response:
			print("MVC: TMDB: getTMDBInfo: response:" + str(response))
			blurb, runtime, genres, countries, releasedate, vote, cover_url = parseMovieData(response, cat)
			if cover_url is not None:
				cover_url = "http://image.tmdb.org/t/p/%s%s" % (self.cover_size, cover_url)
			return blurb, runtime, genres, countries, releasedate, vote, cover_url
		return None
