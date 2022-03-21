# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import datetime
import sys
import dateutil.parser
import babel
from sqlalchemy import and_, or_
from flask import render_template, request, Response, flash, redirect, url_for, abort
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from app_config import app, db
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
from models import Venue, Genres, Artist, Show, Availability


# TODO: connect to a local postgresql database


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    artist_list = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    venue_list = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    return render_template('pages/home.html', artists=artist_list, venues=venue_list)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venue_list = []
    city_list = list(Venue.query.distinct(Venue.city).values(Venue.city, Venue.state))
    for city in city_list:
        venue_in_city = Venue.query.filter_by(city=city[0]).values(Venue.id, Venue.name)
        venue_data = []
        for venue in venue_in_city:
            num_upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).count()
            venue_data.append({
                "id": venue[0],
                "name": venue[1],
                "num_upcoming_shows": num_upcoming_shows
            })
        venue_list.append({
            "city": city[0],
            "state": city[1],
            "venues": venue_data
        })
    return render_template('pages/venues.html', areas=venue_list)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    search_venue_list = []
    data = search_term.split(",")
    if len(data) > 1:
        venue_search = Venue.query.filter(Venue.state.ilike("%" + data[1].strip() + "%"),
                                          Venue.city.ilike("%" + data[0].strip() + "%")).values(Venue.id,
                                                                                                Venue.name,
                                                                                                Venue.city,
                                                                                                Venue.state)
    else:
        venue_search = Venue.query.filter(
            Venue.name.ilike("%" + search_term + "%") | Venue.state.ilike("%" + search_term + "%") |
            Venue.city.ilike("%" + search_term + "%")).values(Venue.id, Venue.name, Venue.state, Venue.city)
    for venue in venue_search:
        num_upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).count()
        search_venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows,
            "state": venue.state,
            "city": venue.city
        })
    response = {
        "count": len(search_venue_list),
        "data": search_venue_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue_detail = {}
    venue = Venue.query.get(venue_id)
    genres_list = [genres.name for genres in venue.genres]
    past_shows_query = Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now())
    upcoming_shows_query = Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now())
    past_shows_list = []
    upcoming_shows_list = []
    for past_show in past_shows_query:
        artist_data = Artist.query.get(past_show.artist_id)
        past_shows_list.append({
            "artist_id": past_show.artist_id,
            "artist_name": artist_data.name,
            "artist_image_link": artist_data.image_link,
            "start_time": str(past_show.start_time)
        })
    for upcoming_show in upcoming_shows_query:
        artist_data = Artist.query.get(upcoming_show.artist_id)
        upcoming_shows_list.append({
            "artist_id": upcoming_show.artist_id,
            "artist_name": artist_data.name,
            "artist_image_link": artist_data.image_link,
            "start_time": str(upcoming_show.start_time)
        })
    venue_detail.update({
        "id": venue.id,
        "name": venue.name,
        "genres": genres_list,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "past_shows": past_shows_list,
        "upcoming_shows": upcoming_shows_list,
        "past_shows_count": len(past_shows_list),
        "upcoming_shows_count": len(upcoming_shows_list),
    })
    return render_template('pages/show_venue.html', venue=venue_detail)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        venue = Venue(name=request.form.get('name'),
                      city=request.form.get('city'),
                      state=request.form.get('state'),
                      address=request.form.get('address'),
                      phone=request.form.get('phone'),
                      facebook_link=request.form.get('facebook_link'),
                      image_link=request.form.get('image_link'),
                      website_link=request.form.get('website_link'),
                      seeking_talent=True if request.form.get('seeking_talent') else False,
                      seeking_description=request.form.get('seeking_description'))
        venue.genres = [Genres.query.filter_by(name=g).first() for g in request.form.getlist('genres')]
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    error = False
    # TODO: Complete this endpoint for taking a venue_id, and using
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artist_list = Artist.query.all()
    data = []
    for artist in artist_list:
        data.append({
            "id": artist.id,
            "name": artist.name,
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    data = search_term.split(",")
    search_artist_list = []
    if len(data) > 1:
        artist_search = Artist.query.filter(Artist.state.ilike("%" + data[1].strip() + "%"),
                                            Artist.city.ilike("%" + data[0].strip() + "%")).values(Artist.id,
                                                                                                   Artist.name,
                                                                                                   Artist.city,
                                                                                                   Artist.state)
    else:
        artist_search = Artist.query.filter(
            Artist.name.ilike("%" + search_term + "%") | Artist.state.ilike("%" + search_term + "%") |
            Artist.city.ilike("%" + search_term + "%")).values(Artist.id, Artist.name, Artist.city, Artist.state)
    for artist in artist_search:
        num_upcoming_shows = Show.query.filter(Show.artist_id == artist.id, Show.start_time >= datetime.now()).count()
        search_artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows,
            "city": artist.city,
            "state": artist.state,
        })
    response = {
        "count": len(search_artist_list),
        "data": search_artist_list
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist_detail = {}
    artist = Artist.query.get(artist_id)
    genres_list = [genres.name for genres in artist.genres]
    past_shows_query = Show.query.filter(Show.artist_id == artist.id, Show.start_time < datetime.now())
    upcoming_shows_query = Show.query.filter(Show.artist_id == artist.id, Show.start_time >= datetime.now())
    availability_query = Availability.query.filter(Availability.artist_id == artist.id)
    past_shows_list = []
    upcoming_shows_list = []
    availability_list = []
    for availability in availability_query:
        availability_list.append({
            "start_at": str(availability.start_at),
            "end_at": str(availability.end_at)
        })
    for past_show in past_shows_query:
        venue_data = Venue.query.get(past_show.venue_id)
        past_shows_list.append({
            "venue_id": past_show.venue_id,
            "venue_name": venue_data.name,
            "venue_image_link": venue_data.image_link,
            "start_time": str(past_show.start_time)
        })
    for upcoming_show in upcoming_shows_query:
        venue_data = Venue.query.get(upcoming_show.venue_id)
        upcoming_shows_list.append({
            "venue_id": upcoming_show.venue_id,
            "venue_name": venue_data.name,
            "venue_image_link": venue_data.image_link,
            "start_time": str(upcoming_show.start_time)
        })
    artist_detail.update({
        "id": artist.id,
        "name": artist.name,
        "genres": genres_list,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "past_shows": past_shows_list,
        "availability_list": availability_list,
        "upcoming_shows": upcoming_shows_list,
        "past_shows_count": len(past_shows_list),
        "upcoming_shows_count": len(upcoming_shows_list),
    })
    return render_template('pages/show_artist.html', artist=artist_detail)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    artist_genres_query = list(artist.genres)
    artist_genres_list = []
    for genres in artist_genres_query:
        artist_genres_list.append(genres.name)
    artist_form_data = {
        "id": artist.name,
        "name": artist.name,
        "genres": artist_genres_list,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
    form = ArtistForm(data=artist_form_data)
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.facebook_link = request.form.get('facebook_link')
        artist.image_link = request.form.get('image_link')
        artist.website_link = request.form.get('website_link')
        artist.seeking_venue = True if request.form.get('seeking_venue') else False
        artist.seeking_description = request.form.get('seeking_description')
        artist.genres = [Genres.query.filter_by(name=g).first() for g in request.form.getlist('genres')]
        db.session.commit()
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        print(sys.exc_info())
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue_genres_query = list(venue.genres)
    venue_genres_list = []
    for genres in venue_genres_query:
        venue_genres_list.append(genres.name)
    venue_form_data = {
        "id": venue.name,
        "name": venue.name,
        "genres": venue_genres_list,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    form = VenueForm(data=venue_form_data)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form.get('name')
        venue.address = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.phone = request.form.get('phone')
        venue.facebook_link = request.form.get('facebook_link')
        venue.image_link = request.form.get('image_link')
        venue.website_link = request.form.get('website_link')
        venue.seeking_talent = True if request.form.get('seeking_talent') else False
        venue.seeking_description = request.form.get('seeking_description')
        venue.genres = [Genres.query.filter_by(name=g).first() for g in request.form.getlist('genres')]
        db.session.commit()
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        print(sys.exc_info())
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        artist = Artist(name=request.form.get('name'),
                        city=request.form.get('city'),
                        state=request.form.get('state'),
                        phone=request.form.get('phone'),
                        facebook_link=request.form.get('facebook_link'),
                        image_link=request.form.get('image_link'),
                        website_link=request.form.get('website_link'),
                        seeking_venue=True if request.form.get('seeking_venue') else False,
                        seeking_description=request.form.get('seeking_description'))
        artist.genres = [Genres.query.filter_by(name=g).first() for g in request.form.getlist('genres')]
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    show_list = []
    show_query = Show.query.all()
    for show in show_query:
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        show_list.append({
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
            "end_time": str(show.end_time)
        })
    return render_template('pages/shows.html', shows=show_list)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    artist = Artist.query.get(request.form.get('artist_id'))
    venue = Venue.query.get(request.form.get('venue_id'))
    start_time_form = request.form.get('start_time')
    end_time_form = request.form.get('end_time')
    try:
        start_time = datetime.strptime(start_time_form, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time_form, '%Y-%m-%d %H:%M:%S')
        if start_time <= end_time:
            availability = Availability.query.filter(Availability.artist_id == artist.id,
                                                     Availability.start_at <= start_time,
                                                     Availability.end_at >= end_time).first()
            if availability:
                show_collide = Show.query.filter(and_(Show.artist_id == artist.id,
                                                      or_(and_(Show.start_time <= start_time,
                                                               Show.end_time >= end_time),
                                                          and_(Show.start_time >= start_time,
                                                               Show.end_time <= end_time),
                                                          and_(Show.start_time <= start_time,
                                                               Show.end_time >= start_time),
                                                          and_(Show.start_time <= end_time,
                                                               Show.end_time >= end_time), ))
                                                 ).first()
                if not show_collide:
                    show = Show(artist_id=artist.id, venue_id=venue.id, start_time=start_time, end_time=end_time)
                    db.session.add(show)
                    db.session.commit()
                    db.session.close()
                    flash('Show was successfully listed!')
                    return redirect(url_for('index'))
                else:
                    # on successful db insert, flash success
                    flash('Artist Availability already occupied, Show was not listed!')
            else:
                flash('Outside Artist Availability, Show was not listed!')
        else:
            flash('Start Time is less than equal to End time')
    except:
        print(sys.exc_info())
        flash('Show was not listed!')
        pass
    finally:
        db.session.close()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    form = ShowForm(data={
        'artist_id': artist.id,
        'venue_id': venue.id,
        'start_time': start_time_form,
        'end_time': end_time_form,
    })
    return render_template('forms/new_show.html', form=form)


@app.route('/artists/<int:artist_id>/availability/create', methods=['GET'])
def create_availability(artist_id):
    # renders form. do not touch.
    form = AvailabilityForm()
    return render_template('forms/new_availability.html', form=form)


@app.route('/artists/<int:artist_id>/availability/create', methods=['POST'])
def availability_submission(artist_id):
    # renders form. do not touch.
    artist = Artist.query.get(artist_id)
    start_at_form = request.form.get('start_at')
    end_at_form = request.form.get('end_at')
    try:
        start_at = datetime.strptime(start_at_form, '%Y-%m-%d %H:%M:%S')
        end_at = datetime.strptime(end_at_form, '%Y-%m-%d %H:%M:%S')
        if start_at <= end_at:
            availability_collide = Availability.query.filter(and_(Availability.artist_id == artist.id,
                                                                  or_(and_(Availability.start_at <= start_at,
                                                                           Availability.end_at >= end_at),
                                                                      and_(Availability.start_at >= start_at,
                                                                           Availability.end_at <= end_at),
                                                                      and_(Availability.start_at <= start_at,
                                                                           Availability.end_at >= start_at),
                                                                      and_(Availability.start_at <= end_at,
                                                                           Availability.end_at >= end_at), ))
                                                             ).first()
            if not availability_collide:
                availability = Availability(artist_id=artist.id, start_at=start_at, end_at=end_at)
                db.session.add(availability)
                db.session.commit()
                db.session.close()
                # on successful db insert, flash success
                flash('Availability was successfully listed!')
                redirect(url_for('index'))
            else:
                flash('Availability Collide!')
        else:
            flash('Start Time is less than equal to End time')
    except:
        print(sys.exc_info())
        flash('Availability was not listed!')
        pass
    finally:
        db.session.close()
    form = AvailabilityForm(data={
        'start_at': start_at_form,
        'end_at': end_at_form,
    })
    return render_template('forms/new_availability.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

def initial_genres():
    genres_list = ['Alternative', 'Blues', 'Classical', 'Country',
                   'Electronic', 'Folk', 'Funk', 'Hip-Hop',
                   'Heavy Metal', 'Instrumental', 'Jazz', 'Musical Theatre',
                   'Pop', 'Punk', 'R&B', 'Reggae', 'Rock n Roll', 'Soul', 'Other']
    for genres in genres_list:
        genres_exist = Genres.query.filter_by(name=genres).first()
        print(genres_exist)
        if not genres_exist:
            g = Genres(name=genres)
            db.session.add(g)
        else:
            print(genres)
    db.session.commit()
    db.session.close()


# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
