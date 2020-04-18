#!/usr/bin/python3

import international_showtimes_api as isa

S_KEY = 'c87bfbb769147aa04b3390a81dd07e5d'

F = isa.InternationalShowtimes(api_key=S_KEY)

# test movies
# movies = F.get_movie(title="Invisible Man")
movies = F.get_movie(movie_id='59251')
for movie in movies:
    print(movie.id)
    print(movie.title)


# test cinemas
cinemas = F.get_cinemas(city='Atlanta')
for cinema in cinemas:
    print(cinema.address)

# test showtimes
cinema = isa.Cinema(data={'id': '56556'}, parent=None)
times = F.get_showtimes(cinema=cinema)
for time in times:
    if time.movie:
        print(f"{time.movie.title}: {time.startTime}")

times = F.get_showtimes(title='Gladiator', skip_cinemas=True)
# times = F.get_showtimes(latitude='33.783', longitude='-84.333')
for time in times:
    print(time.cinemaId)
    print(F.get_cinemas(cinema_id=time.cinemaId))
    if time.movie:
        print(f"{time.movie.title}: {time.startTime}")


# test chains
chains = F.get_chain(chain_name='Price Theatre', country_codes=['US'])
for chain in chains:
    print(chain.name)

