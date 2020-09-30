#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import desc, distinct
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import re
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'venue'

    v_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))

    def get_shows(self):
        # A method to return upcoming and past shows for current artist. Its better than looping a join method. 
        # This method inspired by a comment from the Mentor Help section in Udacity.
        shows = self.artist
        upcoming_shows = []
        past_shows = []
        for show in shows:
            current_date = datetime.now()
            show_date = dateutil.parser.parse(show.start_time)
            if show_date > current_date:
                upcoming_shows.append(show)
            else:
                past_shows.append(show)

        return [upcoming_shows, past_shows]


class Artist(db.Model):
    __tablename__ = 'artist'
    a_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))

    def get_shows(self):
        # A method to return upcoming and past shows for current artist. Its better than looping a join method. 
        # This method inspired by a comment from the Mentor Help section in Udacity.
        shows = self.venue
        upcoming_shows = []
        past_shows = []
        for show in shows:
            current_date = datetime.now()
            show_date = dateutil.parser.parse(show.start_time)
            if show_date > current_date:
                upcoming_shows.append(show)
            else:
                past_shows.append(show)

        return [upcoming_shows, past_shows]


class Show(db.Model):
    __tablename__ = 'show'
    s_id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.a_id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.v_id'))
    start_time = db.Column(db.String)

    venue = relationship('Venue', backref=backref("artist", lazy=True))
    artist = relationship('Artist', backref=backref("venue", lazy=True))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    artists = Artist.query.order_by(db.desc(Artist.a_id)).limit(10)
    venues = Venue.query.order_by(db.desc(Venue.v_id)).limit(10)
    return render_template('pages/home.html', artists=artists, venues=venues)


#  VENUES
#  ----------------------------------------------------------------
# -- PRINT LIST -- 
@app.route('/venues')
def venues():
    venues = Venue.query.all()
    distinct_venues = Venue.query.distinct(Venue.state).all()
    data = []
    entry = {}
    ven = []
    ven_entry = {}
    for d_v in distinct_venues:
        entry["city"] = d_v.city
        entry["state"] = d_v.state
        for v in venues:
            if v.state == d_v.state:
                ven_entry["id"]=v.v_id
                ven_entry["name"]=v.name
                ven_entry["num_upcoming_shows"] = len(v.get_shows()[0])
                ven.append(ven_entry)
                ven_entry = {}
        entry["venues"] = ven
        ven = []
        data.append(entry)
        entry = {}            

    return render_template('pages/venues.html', areas=data)

# -- SEARCH -- 
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_value = request.form.get('search_term', '')
    data = Venue.query.filter(Venue.name.ilike('%'+search_value+'%')).all()
    response = {
        "count":0,
        "data":[]
    }
    response["count"] = len(data)
    for d in data: 
        response["data"].append(d.__dict__) 

    return render_template('pages/search_venues.html', results=response, search_term=search_value)

# -- SHOW PAGE -- 
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    shows = venue.get_shows()
    data = venue.__dict__
    data['upcoming_shows'] = shows[0]
    data['past_shows'] = shows[1]
    data['upcoming_shows_count'] = len(shows[0])
    data['past_shows_count'] = len(shows[1])
    
    return render_template('pages/show_venue.html', venue=data)
                           

# -- CREATE -- 
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        name = request.form['name']
        city = request.form['city']    
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        print(genres)
        facebook_link = request.form['facebook_link']

        venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return index()
    except: 
        flash('An error occurred. Venue ' +  request.form['name'] + ' could not be listed.')
        db.session.rollback()
    finally: 
        db.session.close()


# -- DELETE -- 
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
        return index()
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +  venue.name + ' could not be deleted.')
    finally:
        db.session.close()


# -- EDIT -- 
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.name.process_data(venue.name)
    form.city.process_data(venue.city)
    form.state.process_data(venue.state) 
    form.address.process_data(venue.address)
    form.phone.process_data(venue.phone)
    form.genres.process_data([g for g in venue.genres])
    form.facebook_link.process_data(venue.facebook_link)
    data = venue.__dict__
    return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']

        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except: 
        flash('An error occurred. Venue ' +  request.form['name'] + ' could not be edited.')
        db.session.rollback()
    finally: 
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  ARTIST
#  ----------------------------------------------------------------
# -- PRINT LIST -- 
@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()
    for a in artists:
        data.append(a.__dict__)
    return render_template('pages/artists.html', artists=data)

# -- SEARCH -- 
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_value = request.form.get('search_term', '')
    data = Artist.query.filter(Artist.name.ilike('%'+search_value+'%')).all()
    response = {
        "count":0,
        "data":[]
    }
    response["count"] = len(data)
    for d in data: 
        response["data"].append(d.__dict__) 
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# -- SHOW PAGE -- 
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    shows = artist.get_shows()
    data = artist.__dict__
    data['upcoming_shows'] = shows[0]
    data['past_shows'] = shows[1]
    data['upcoming_shows_count'] = len(shows[0])
    data['past_shows_count'] = len(shows[1])

    return render_template('pages/show_artist.html', artist=data)

# -- EDIT -- 
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.name.process_data(artist.name)
    form.city.process_data(artist.city)
    form.state.process_data(artist.state) 
    form.phone.process_data(artist.phone)
    form.genres.process_data([g for g in artist.genres])
    form.facebook_link.process_data(artist.facebook_link)
    data = artist.__dict__
    return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully edited!')
    except: 
        flash('An error occurred. Artist ' +  request.form['name'] + ' could not be edited.')
        db.session.rollback()
    finally: 
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

# -- CREATE --
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        name = request.form['name']
        city = request.form['city']    
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']

        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return index()
    except: 
        flash('An error occurred. Artist ' +  request.form['name'] + ' could not be listed.')
        db.session.rollback()
    finally: 
        db.session.close()

# -- DELETE -- 
@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully deleted!')
        return index()
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +  artist.name + ' could not be deleted.')
    finally:
        db.session.close()

#  SHOWS
#  ----------------------------------------------------------------
# -- PRINT LIST -- 
@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    entery = {}
    for show in shows: 
        entery["venue_id"] = show.venue_id
        entery["venue_name"] = Venue.query.get(show.venue_id).name
        entery["artist_id"] = show.artist_id
        entery["artist_name"] = Artist.query.get(show.artist_id).name
        entery["artist_image_link"] = Artist.query.get(show.artist_id).image_link
        entery["start_time"] = show.start_time
        data.append(entery)
        entery = {}

    return render_template('pages/shows.html', shows=data)

# -- CREATE -- 
@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']    
        start_time = request.form['start_time']

        show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except: 
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
    finally: 
        db.session.close()

    return index()


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
