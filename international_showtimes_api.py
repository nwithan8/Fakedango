#!/usr/bin/python3

import requests
import logging
import json
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def _convert_to_datetime(date):
    return datetime.strptime(date, '%m/%d/%y')


def _get_midnight(date):
    return datetime.combine(date, datetime.min.time()).timestamp()


def _get_request(url, headers=None, payload: dict = None, stream: bool = False):
    logging.info(f"GET {url}")
    try:
        return requests.get(url, data=payload, stream=stream, headers=(headers if headers else None))
    except requests.exceptions.RequestException:
        logging.error('HTTP Request failed')
        return None


def filter_cinemas(data, name: str = None, city: str = None, zip_code: str = None, state: str = None,
                   cinema_id: str = None):
    results = []
    for cinema in data:
        valid = True
        if name and cinema.get('name') and name != cinema.get('name'):
            valid = False
        if cinema_id and cinema.get('id') and cinema_id != cinema.get('id'):
            valid = False
        location_data = cinema.get('location')
        if location_data:
            location_address_data = location_data.get('address')
            if location_address_data:
                if city and location_address_data.get('city') and city != location_address_data.get('city'):
                    valid = False
                if zip_code:
                    if not location_address_data.get('zipcode'):
                        valid = False
                    elif str(zip_code) != location_address_data.get('zipcode'):
                        valid = False
                if state:
                    if len(state) == 2:
                        if location_address_data.get('state_abbr') and state != location_address_data.get('state_abbr'):
                            valid = False
                    else:
                        if location_address_data.get('state') and state != location_address_data.get('state'):
                            valid = False
        if valid:
            results.append(cinema)
    return results


def filter_movies(movies, title: str = None, movie_id: str = None):
    results = []
    for movie in movies:
        if title and movie.title == title:
            results.append(movie)
        if movie_id and movie.id == movie_id:
            results.append(movie)
    return results


class Cinema:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.slug = data.get('slug')
        self.name = data.get('name')
        self.chainId = data.get('chain_id')
        self.cityId = data.get('city_id')
        self.phoneNumber = data.get('telephone')
        self.email = data.get('email')
        self.website = data.get('website')
        if data.get('location'):
            self.lat = data['location'].get('lat')
            self.lon = data['location'].get('lon')
            if data['location'].get('address'):
                self.address = data['location']['address'].get('display_text')
                self.street = data['location']['address'].get('street')
                self.streetNumber = data['location']['address'].get('house')
                self.zipCode = data['location']['address'].get('zipcode')
                self.city = data['location']['address'].get('city')
                self.state = data['location']['address'].get('state')
                self.stateAbbr = data['location']['address'].get('state_abbr')
                self.country = data['location']['address'].get('country')
                self.countryCode = data['location']['address'].get('country_code')
        self.booking_type = data.get('booking_type')


class Genre:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.name = data.get('name')


class Trailer:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.language = data.get('language')
        self.official = data.get('is_official')
        self.files = data.get('trailer_files')


class Rating:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        if data:
            self.value = data.get('value')
            self.votes = data.get('vote_count')


class Ratings:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.IMDbRating = Rating(data.get('imdb'), self.parent)
        self.TMDbRating = Rating(data.get('tmdb'), self.parent)
        self.RottenTomatoesRating = Rating(data.get('rotten_tomatos'), self.parent)


class ReleaseDate:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.locale = data.get('locale')
        self.region = data.get('region')
        self.data = data.get('date')


class ReleaseDates:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        for k, v in self.data:
            self.data[k] = [ReleaseDate(release_data, self.parent) for release_data in v]


class Image:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data


class Person:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.name = data.get('name')
        self.image = data.get('image')
        self.job = data.get('job')
        self.character = data.get('character')


class Country:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.ISOCode = data.get('iso_code')
        self.name = data.get('name')
        self.APIAccess = data.get('is_access_granted')


class Movie:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.slug = data.get('slug')
        self.title = data.get('title')
        self.originalTitle = data.get('original_title')
        self.originalLanguage = data.get('original_language')
        self.summary = data.get('synopsis')
        self.poster = data.get('poster_image')
        self.posterThumbnail = data.get('poster_image_thumbnail')
        self.scenesImages = data.get('scene_images')
        self.runtime = data.get('runtime')
        if data.get('genres'):
            self.genres = [Genre(genre_data, self.parent) for genre_data in data.get('genres')]
        if data.get('trailers'):
            self.trailers = [Trailer(trailer_data, self.parent) for trailer_data in data.get('trailers')]
        if data.get('ratings'):
            self.ratings = Ratings(data.get('ratings'), self.parent)
        self.ageRestrictions = data.get('age_limits')
        if data.get('release_dates'):
            self.releaseDates = ReleaseDates(data.get('release_dates'), self.parent)
        self.website = data.get('website')
        self.productionCompanies = data.get('production_companies')
        self.keywords = data.get('keywords')
        self.IMDbId = data.get('imdb_id')
        self.TMDbId = data.get('tmdb_id')
        self.rentrakId = data.get('rentrak_film_id')
        if data.get('cast'):
            self.cast = [Person(person_data, self.parent) for person_data in data.get('cast')]
        if data.get('crew'):
            self.crew = [Person(person_data, self.parent) for person_data in data.get('crew')]


class Showtime:
    def __init__(self, data, parent, movie: Movie = None, cinema: Cinema = None,
                 skip_additional_api_calls: bool = False):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.cinemaId = data.get('cinema_id')
        self.cinema = cinema
        self.movieId = data.get('movie_id')
        self.movie = movie
        self.startTime = data.get('start_at')
        self.auditorium = data.get('auditorium')
        self.is3D = data.get('is_3d')
        self.isIMAX = data.get('is_imax')
        self.language = data.get('language')
        self.subtitleLanguage = data.get('subtitle_language')
        self.cinemaMovieTitle = data.get('cinema_movie_title')
        self.bookingType = data.get('booking_type')
        self.bookingLink = data.get('booking_link')
        if not skip_additional_api_calls:
            if self.movieId and not self.movie:
                res = parent.get_movie(movie_id=self.movieId)
                if res:
                    self.movie = res[0]
            if self.cinemaId and not self.cinema:
                res = parent.get_cinemas(cinema_id=self.cinemaId)
                if res:
                    self.cinema = res[0]


class Chain:
    def __init__(self, data, parent):
        self.parent = parent
        self.data = data
        self.id = data.get('id')
        self.name = data.get('name')
        self.websites = data.get('websites')
        self.countries = data.get('countries')


class Cache:
    def __init__(self, parent):
        self.movies = {}
        self.cinemas = {}
        self.showtimes = {}
        self.chains = {}
        self.genres = {}

    def check_for_cached_movie(self, movie_id: str = None, title: str = None):
        if not movie_id and not title:
            raise Exception("Please provide either a movie_id or a title.")
        if movie_id and movie_id in self.movies.keys():
            return self.movies[movie_id]
        else:
            for _, movie in self.movies.items():
                if movie.title == title:
                    return movie
        return None

    def check_for_cached_cinema(self, cinema_id: str = None, latitude: str = None, longitude: str = None):
        if cinema_id in self.cinemas.keys():
            return self.cinemas[cinema_id]
        if latitude and longitude:
            for _, cinema in self.cinemas.items():
                if cinema.lat == latitude and cinema.lon == longitude:
                    return cinema
        return None

    def check_for_cached_showtime(self, showtime_id: str = None):
        if showtime_id and showtime_id in self.showtimes.keys():
            return self.showtimes[showtime_id]
        return None

    def check_for_cached_chain(self, chain_id: str = None, chain_name: str = None):
        if chain_id and chain_id in self.chains.keys():
            return self.chains[chain_id]
        if chain_name:
            for _, chain in self.chains.items():
                if chain.name == chain_name:
                    return chain
        return None

    def check_for_cached_genre(self, genre_id: str = None, genre_name: str = None):
        if genre_id and genre_id in self.genres.keys():
            return self.genres[genre_id]
        if genre_name:
            for _, genre in self.genres.items():
                if genre.name == genre_name:
                    return genre
        return None


class InternationalShowtimes:
    def __init__(self, api_key: str, language: str = None):
        self.key = api_key
        self.baseUrl = 'https://api.internationalshowtimes.com/v4'
        self.headers = {'x-api-key': self.key}
        self.language = (language if language else "en")
        self.cache = Cache(self)
        self.get_all_current_movies()

    def get_genre(self, genre_id: str = None, genre_name: str = None):
        """

        :param genre_id:
        :param genre_name:
        :return: [Genre, ...]
        """
        cached_genre = self.cache.check_for_cached_genre(genre_id=genre_id, genre_name=genre_name)
        if cached_genre:
            return [cached_genre]
        results = []
        query = f'{self.baseUrl}/genres?lang={self.language}'
        res = _get_request(url=query,
                           headers=self.headers)
        if res and res.json().get('genres'):
            for genre_data in res.json()['genres']:
                cached_genre = self.cache.check_for_cached_genre(genre_id=genre_id, genre_name=genre_name)
                if cached_genre:
                    results.append(cached_genre)
                else:
                    new_genre = Genre(genre_data, self)
                    self.cache.genres[genre_data['id']] = new_genre
                    results.append(new_genre)
        if genre_id or genre_name:
            filtered = []
            for genre in results:
                if (genre_id and genre_id == genre.id) or (genre_name and genre_name == genre.name):
                    filtered.append(genre)
            results = filtered
        return results

    def get_all_current_movies(self, cinema_id: str = None):
        """

        :param cinema_id:
        :return: [Movie, ...]
        """
        results = []
        query = f'{self.baseUrl}/movies?lang={self.language}'
        if cinema_id:
            query = f'{query}&cinema_id={cinema_id}'
        res = _get_request(url=query,
                           headers=self.headers)
        if res and res.json().get('movies'):
            self.cache.movies.clear()  # clears the movie cache every time it is run
            for movie_data in res.json()['movies']:
                new_movie = Movie(movie_data, self)
                self.cache.movies[movie_data['id']] = new_movie
                results.append(new_movie)
        return results

    def get_upcoming_movies(self):
        """

        :return: [Movie, ...]
        """
        results = []
        tomorrow = _get_midnight(datetime.today() + timedelta(days=1))
        query = f'{self.baseUrl}/movies?lang={self.language}&include_upcoming=true&release_date_from={tomorrow}'
        res = _get_request(url=query,
                           headers=self.headers)
        if res and res.json().get('movies'):
            for movie_data in res.json()['movies']:
                cached_movie = self.cache.check_for_cached_movie(movie_id=movie_data['id'])
                if cached_movie:
                    results.append(cached_movie)
                else:
                    new_movie = Movie(movie_data, self)
                    self.cache.movies[movie_data['id']] = new_movie
                    results.append(new_movie)
        return results

    def get_movie(self, title: str = None, movie_id: str = None):
        """
        :param title:
        :param movie_id:
        :return: [Movie, ...]
        """
        if not title and not movie_id:
            raise Exception("Please provide a title or a movie_id.")
        cached_movie = self.cache.check_for_cached_movie(movie_id=movie_id, title=title)
        if cached_movie:
            return [cached_movie]
        results = []
        if movie_id:
            query = f'{self.baseUrl}/movies/{movie_id}?lang={self.language}'
            res = _get_request(url=query,
                               headers=self.headers)
            if res and res.json().get('movies'):
                for movie_data in res.json()['movies']:
                    cached_movie = self.cache.check_for_cached_movie(movie_id=movie_data['id'])
                    if cached_movie:
                        results.append(cached_movie)
                    else:
                        new_movie = Movie(movie_data, self)
                        self.cache.movies[movie_data['id']] = new_movie
                        results.append(new_movie)
        elif title:
            title = quote(title)
            query = f'{self.baseUrl}/movies?lang={self.language}&search_query={title}&search_field=title'
            res = _get_request(url=query,
                               headers=self.headers)
            if res and res.json().get('movies'):
                for movie_data in res.json()['movies']:
                    cached_movie = self.cache.check_for_cached_movie(movie_id=movie_data['id'])
                    if cached_movie:
                        results.append(cached_movie)
                    else:
                        new_movie = Movie(movie_data, self)
                        self.cache.movies[movie_data['id']] = new_movie
                        results.append(new_movie)
        else:
            all_movies = self.get_all_current_movies()
            results = filter_movies(all_movies, movie_id=movie_id)
        return results

    def get_cinemas(self, name: str = None, city: str = None, zip_code: int = None, state: str = None,
                    latitude: str = None, longitude: str = None, cinema_id: str = None):
        """

        :param name:
        :param city:
        :param zip_code:
        :param state:
        :param latitude:
        :param longitude:
        :param cinema_id:
        :return: [Cinema, ...]
        """
        cached_cinema = self.cache.check_for_cached_cinema(cinema_id=cinema_id, latitude=latitude, longitude=longitude)
        if cached_cinema:
            return [cached_cinema]
        if cinema_id:  # try searching by cinema_id first for a single cinema
            query = f"{self.baseUrl}/cinemas/{cinema_id}?lang={self.language}"  # this always fails at the moment
            res = _get_request(url=query, headers=self.headers)
            if res and res.json().get('cinemas'):
                new_cinema = Cinema(res.json['cinemas'][0], self)
                self.cache.cinemas[res.json['cinemas'][0]['id']] = new_cinema
                return [new_cinema]
        # otherwise, grab all cinemas and filter by parameters
        results = []
        query = f"{self.baseUrl}/cinemas?lang={self.language}"
        if latitude and longitude:  # narrow down initial result set if possible
            query += f"&location={latitude},{longitude}"
        res = _get_request(url=query, headers=self.headers)
        if res and res.json().get('cinemas'):
            filtered = filter_cinemas(data=res.json()['cinemas'], name=name, city=city, zip_code=zip_code, state=state,
                                      cinema_id=cinema_id)
            if filtered:
                for cinema_data in filtered:
                    cached_cinema = self.cache.check_for_cached_cinema(cinema_id=cinema_data['id'])
                    if cached_cinema:
                        results.append(cached_cinema)
                    else:
                        new_cinema = Cinema(cinema_data, self)
                        self.cache.cinemas[cinema_data['id']] = new_cinema
                        results.append(new_cinema)
        return results

    def get_showtimes(self, movie: Movie = None, title: str = None, cinema: Cinema = None, latitude: str = None,
                      longitude: str = None, startDay: str = None, endDay: str = None, showtime_id: str = None,
                      skip_cinemas: bool = False):
        """

        :param movie:
        :param title:
        :param cinema:
        :param latitude:
        :param longitude:
        :param startDay:
        :param endDay:
        :param showtime_id:
        :param skip_cinemas:
        :return: [Showtime, ...]
        """
        cached_showtime = self.cache.check_for_cached_showtime(showtime_id=showtime_id)
        if cached_showtime:
            return [cached_showtime]
        results = []
        query = f"{self.baseUrl}/showtimes?lang={self.language}&append=cinemas&append=movies"  # times for all movies at all cinemas (default)
        if latitude and longitude:
            query += f"&location={latitude},{longitude}"
        if cinema and (movie or title):  # times for a particular movie at a particular cinema
            if not movie:
                movie = self.get_movie(title=title)
                if movie:
                    query = f"{self.baseUrl}/showtimes?lang={self.language}&cinema_id={cinema.id}&movie_id={movie[0].id}"
        elif cinema:  # times for all movies at a particular cinema
            query = f"{self.baseUrl}/showtimes?lang={self.language}&cinema_id={cinema.id}&append=movies"
        elif movie or title:  # times for a particular movie at all cinemas
            if not movie:
                movie = self.get_movie(title=title)
                if movie:
                    query = f"{self.baseUrl}/showtimes?lang={self.language}&append=cinemas&movie_id={movie[0].id}"
                    if latitude and longitude:
                        query += f"&location={latitude},{longitude}"
        if startDay:
            startDay = _get_midnight(_convert_to_datetime(startDay))
            query += f"{query}&time_from={startDay}"
        if endDay:
            endDay = _get_midnight(_convert_to_datetime(endDay))
            query += f"{query}&time_to={endDay}"
        res = _get_request(url=query, headers=self.headers)
        if res and res.json().get('showtimes'):
            for showtime_data in res.json()['showtimes']:
                cached_showtime = self.cache.check_for_cached_showtime(showtime_id=showtime_data['id'])
                if cached_showtime:
                    results.append(cached_showtime)
                else:
                    new_showtime = Showtime(showtime_data, self, skip_additional_api_calls=skip_cinemas)
                    self.cache.showtimes[showtime_data['id']] = new_showtime
                    results.append(new_showtime)
        return results

    def get_chain(self, chain_name: str = None, chain_id: str = None, country_codes: list = []):
        """

        :param chain_name:
        :param chain_id:
        :param country_codes:
        :return: [Chain, ...]
        """
        results = []
        cached_chain = self.cache.check_for_cached_chain(chain_id=chain_id, chain_name=chain_name)
        if cached_chain:
            return [cached_chain]
        query = f'{self.baseUrl}/chains?lang={self.language}'
        if country_codes:
            query += f"&countries={','.join(country_codes)}"
        res = _get_request(url=query,
                           headers=self.headers)
        if res and res.json().get('chains'):
            for chain_data in res.json()['chains']:
                cached_chain = self.cache.check_for_cached_chain(chain_id=chain_data['id'],
                                                                 chain_name=chain_data['name'])
                if cached_chain:
                    results.append(cached_chain)
                else:
                    new_chain = Chain(chain_data, self)
                    self.cache.chains[chain_data['id']] = new_chain
                    results.append(new_chain)
        if chain_name or chain_id:
            filtered = []
            for chain in results:
                if (chain_name and chain_name.strip() == chain.name.strip()) or (
                        chain_id and chain_id.strip() == chain.id.strip()):
                    filtered.append(chain)
            results = filtered
        return results

    def clear_cache(self):
        self.cache.movies.clear()
        self.cache.cinemas.clear()
        self.cache.showtimes.clear()
        self.cache.chains.clear()
        self.cache.genres.clear()
