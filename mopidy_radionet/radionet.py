#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import time
import urllib

from urllib.request import urlopen, Request

import math

logger = logging.getLogger(__name__)

REGIONS = {
    'at': 'de-AT',
    'au': 'en-AU',
    'br': 'pt-BR',
    'ca': 'en-CA',
    'co': 'es-CO',
    'de': 'de-DE',
    'dk': 'da-DK',
    'es': 'es-ES',
    'fr': 'fr-FR',
    'ie': 'en-IE',
    'it': 'it-IT',
    'mx': 'es-MX',
    'nl': 'nl-NL',
    'nz': 'en-NZ',
    'pl': 'pl-PL',
    'pt': 'pt-PT',
    'se': 'sv-SE',
    'uk': 'en-GB',
    'us': 'en-US',
    'za': 'en-ZA',
}


class Station(object):
    id = None
    continent = None
    country = None
    city = None
    genres = None
    name = None
    stream_url = None
    image_tiny = None
    image_small = None
    image_medium = None
    image_large = None
    description = None
    playable = False


class RadioNetClient(object):
    base_url = "https://prod.radio-api.net"
    language = REGIONS['us']
    user_agent = 'Radio.net - Web V5'

    min_bitrate = 96
    max_top_stations = 100
    station_bookmarks = None
    api_key = None

    stations_images = []
    favorites = []

    cache = {}

    stations_by_id = {}
    stations_by_slug = {}

    category_param_map = {
        "genres": "genre",
        "topics": "topic",
        "languages": "language",
        "cities": "city",
        "countries": "country",
    }

    def __init__(self, proxy_config=None, user_agent=None):
        super(RadioNetClient, self).__init__()

    def set_lang(self, lang):
        if lang in REGIONS:
            self.language = REGIONS[lang]
        else:
            logging.warning("Radio.net not supported language: %s, defaulting to English", str(lang))

    def do_get(self, api_suffix, url_params=None):
        try:
            url = self.base_url + api_suffix
            if url_params is not None:
                url += "?" + urllib.parse.urlencode(url_params)
            req = Request(url)
            req.add_header('accept-language', self.language)
            req.add_header('user-agent', self.user_agent)
            response = urlopen(req).read()
        except Exception as err:
            logging.error(f'_open_url error: {err}')
            response = None

        return json.loads(response)

    def get_cache(self, key):
        if self.cache.get(key) is not None and self.cache[key].expired() is False:
            return self.cache[key].value()
        return None

    def set_cache(self, key, value, expires):
        self.cache[key] = CacheItem(value, expires)
        return value

    def get_station_by_id(self, station_id):
        if not self.stations_by_id.get(station_id):
            return self._get_station_by_id(station_id)
        return self.stations_by_id.get(station_id)

    def get_station_by_slug(self, station_slug):
        if not self.stations_by_slug.get(station_slug):
            return self._get_station_by_id(station_slug)
        return self.stations_by_slug.get(station_slug)

    def _get_station_by_id(self, station_id):
        cache_key = "station/" + str(station_id)
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        api_suffix = "/stations/details"

        url_params = {
            "stationIds": station_id,
        }

        response = self.do_get(api_suffix, url_params)

        if response is None or len(response) == 0:
            logger.error("Radio.net: Error on get station by id " + str(station_id))
            return False

        logger.debug("Radio.net: Done get top stations list")

        json = response[0]

        station = self._get_station_from_search_result(json)

        self.set_cache(cache_key, station, 1440)
        return station

    def _get_station_from_search_result(self, result):
        if not self.stations_by_id.get(result["id"]):
            station = Station()
            station.playable = True
        else:
            station = self.stations_by_id[result["id"]]

        station.id = result["id"]

        if "country" in result:
            station.country = result["country"]
        else:
            station.country = ""

        if "city" in result:
            station.city = result["city"]
        else:
            station.city = ""

        if "name" in result:
            station.name = result["name"]
        else:
            station.name = ""

        if "shortDescription" in result:
            station.description = result["shortDescription"]
        else:
            station.description = ""

        if "genres" in result:
            station.genres = ", ".join(result["genres"])
        else:
            station.genres = ""

        if "logo44x44" in result:
            station.image_tiny = result["logo44x44"]
        else:
            station.image_tiny = ""

        if "logo100x100" in result:
            station.image_tiny = result["logo100x100"]
        else:
            station.image_tiny = ""

        if "logo175x175" in result:
            station.image_medium = result["logo175x175"]
        else:
            station.image_medium = ""

        if "logo300x300" in result:
            station.image_large = result["logo300x300"]
        else:
            station.image_large = ""

        if "streams" in result:
            station.stream_url = self._get_stream_url(result["streams"], self.min_bitrate)

        self.stations_by_id[station.id] = station
        return station

    def get_genres(self):
        return self._get_items("genres")

    def get_topics(self):
        return self._get_items("topics")

    def get_languages(self):
        return self._get_items("languages")

    def get_cities(self):
        return self._get_items("cities")

    def get_countries(self):
        return self._get_items("countries")

    def _get_items(self, key):
        cached = self.get_cache(key)
        if cached is not None:
            return cached

        api_suffix = "/stations/tags"
        response = self.do_get(api_suffix)
        if response is None:
            logger.error("Radio.net: Error on get item list")
            return False

        return self.set_cache(key, self._filter_result(response, key, 0), 1440)

    def _filter_result(self, data, tag, min_count_stations):
        api_result = data.get(tag, [])

        if api_result and min_count_stations:
            # filter result by minimum count of stations
            result = []

            for item in api_result:
                if item['count'] >= min_count_stations:
                    result.append(item)

            return result

        return api_result

    def get_category(self, category, name, page=1):
        results = []
        for result in self._get_category(category, name, page):
            results.append(self._get_station_from_search_result(result))
        return results

    def _get_category(self, category, name, page=1):

        cache_key = category + "/" + name + "/" + str(page)
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        api_suffix = "/stations/by-tag"
        url_params = {
            "tagType": category,
            "slug": name,
            "count": 50,
            "offset": (page - 1) * 50,
        }

        response = self.do_get(api_suffix, url_params)

        if response is None:
            logger.error("Radio.net: Error on get station by " + str(category))
            return False

        self.set_cache(category + "/" + name, int(math.ceil(response["totalCount"] / 50)), 10)
        return self.set_cache(cache_key, response["playables"], 10)

    def get_simple_category(self, category, page=1):
        results = []
        for result in self._get_simple_category(category, page):
            results.append(self._get_station_from_search_result(result))
        return results

    def _get_simple_category(self, category, page=1):
        cache_key = category + "/" + str(page)
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        api_suffix = "/stations/" + category
        url_params = {"count": 50, "offset": (page - 1) * 50}

        response = self.do_get(api_suffix, url_params)

        if response is None:
            logger.error("Radio.net: Error on get station by " + str(category))
            return False

        self.set_cache(category, int(math.ceil(response["totalCount"] / 50)), 10)
        return self.set_cache(cache_key, response["playables"], 10)

    def get_category_pages(self, category, name):
        cache_key = category + "/" + name
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        self.get_category(category, name, 1)

        return self.get_cache(cache_key)

    def get_simple_category_pages(self, category):
        cache_key = category
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        self.get_simple_category(category, 1)

        return self.get_cache(cache_key)

    def set_favorites(self, favorites):
        self.favorites = favorites

    def get_favorites(self):
        cache_key = "favorites"
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache

        favorite_stations = []
        for station_slug in self.favorites:

            station = self.get_station_by_id(station_slug)

            if station is False:
                api_suffix = "/stations/search"
                url_params = {
                    "query": station_slug,
                    "count": 1,
                    "offset": 0,
                }
                response = self.do_get(api_suffix, url_params)

                if response is None:
                    logger.error("Radio.net: Search error")
                else:
                    logger.debug("Radio.net: Done search")

                    if "playables" in response and len(response["playables"]) > 0:
                        # take only the first match!
                        station = self._get_station_from_search_result(response["playables"][0])
                    else:
                        logger.warning("Radio.net: No results for %s", station_slug)

            if station and station.playable:
                favorite_stations.append(station)

        logger.info(
            "Radio.net: Loaded " + str(len(favorite_stations)) + " favorite stations."
        )
        return self.set_cache(cache_key, favorite_stations, 1440)

    def do_search(self, query_string, page_index=1, search_results=None):

        api_suffix = "/stations/search"
        url_params = {
            "query": query_string,
            "count": 50,
            "offset": (page_index - 1) * 50,
        }
        logger.info(url_params)
        response = self.do_get(api_suffix, url_params)

        if response is None:
            logger.error("Radio.net: Search error")
        else:
            logger.info("Radio.net: Done search")
            if search_results is None:
                search_results = []
            for match in response["playables"]:
                station = self._get_station_from_search_result(match)
                if station and station.playable:
                    search_results.append(station)

            number_pages = int(math.ceil(response["totalCount"] / 50))
            # Search is utterly broken, don't retrieve more than 10 pages
            logger.info(page_index)
            if number_pages > page_index and page_index < 10:
                self.do_search(query_string, page_index + 1, search_results)
            else:
                logger.info(
                    "Radio.net: Found " + str(len(search_results)) + " stations."
                )
        return search_results

    def get_stream_url(self, station_id):
        station = self.get_station_by_id(station_id)
        if not station.stream_url:
            station = self._get_station_by_id(station.id)
        return station.stream_url

    def _get_stream_url(self, stream_json, bit_rate):
        stream_url = None

        for stream in stream_json:
            logger.info("Radio.net: Found stream URL " + stream["url"])
            if ("bitRate" in stream and int(stream["bitRate"]) >= bit_rate) and stream["status"] == "VALID":
                stream_url = stream["url"]
                break

        if stream_url is None and len(stream_json) > 0:
            stream_url = stream_json[0]["url"]

        return stream_url


class CacheItem(object):
    def __init__(self, value, expires=10):
        self._value = value
        self._expires = time.time() + expires * 60

    def expired(self):
        return self._expires < time.time()

    def value(self):
        return self._value
