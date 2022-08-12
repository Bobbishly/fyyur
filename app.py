#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql.functions import concat
from models import showTable, Venue, Artist
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

def str_to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    upcoming_shows = 0
    # Get unique cities first to fill the data array in the correct way
    city_records = Venue.query.distinct(concat(Venue.city, Venue.state)).all()
    for c_record in city_records:
        venues_data = []
        # Get all the venues in each city
        venue_records = Venue.query.filter(Venue.city.like(c_record.city)) \
            .filter(Venue.state.like(c_record.state)).all()
        for v_record in venue_records:
            # Get upcoming show
            upcoming_shows = 0
            shows = db.session.query(showTable)\
            .join(Venue, Venue.id == showTable.c.venue_id)\
            .join(Artist, Artist.id == showTable.columns.artist_id)\
            .filter(Venue.id == v_record.id).all()
            for show in shows:
                if str_to_datetime(show.start_time) > datetime.utcnow():
                    upcoming_shows += 1
            # Append each venue data to the venues list
            venues_data.append({'id': v_record.id, 'name': v_record.name, 'num_upcomig_shows': upcoming_shows})
        # Append each city to the data list
        data.append({'city': c_record.city, 'state': c_record.state, 'venues': venues_data})
    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_word = request.form['search_term']
    results = Venue.query.filter(Venue.name.ilike(f'%{search_word}%')).all()
    data = []
    for result in results:
        upcoming_shows = 0
        # Get upcoming show counts
        shows = db.session.query(showTable)\
            .join(Venue, Venue.id == showTable.c.venue_id)\
            .join(Artist, Artist.id == showTable.columns.artist_id)\
            .filter(Venue.id == result.id).all()
        for show in shows:
            if str_to_datetime(show.start_time) > datetime.utcnow():
                upcoming_shows += 1
        # Add the result needed data to the data object
        data.append({'id': result.id, 'name': result.name, 'num_upcoming_shows': upcoming_shows})
    # Create the response with the right way to be rendered
    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    form = ArtistForm()
    data = {}
    # Get the required venue to show its details with its id
    required_venue = Venue.query.get(venue_id)
    # Convert genres to list to be rendered in the correct way
    required_venue.genres = (required_venue.genres.replace('{', '')).replace('}', '').split(',')
    # Update the data dictionary with the venue details 
    data.update({
        'id': required_venue.id,
        'name': required_venue.name,
        "genres": required_venue.genres,
        "address": required_venue.address,
        "city": required_venue.city,
        "state": required_venue.state,
        "phone": required_venue.phone,
        "website": required_venue.website,
        "facebook_link": required_venue.facebook_link,
        "seeking_talent": required_venue.seeking_talent,
        "seeking_description": required_venue.seeking_description,
        "image_link": required_venue.image_link
    })
    # Get the shows details for this venue by using the relationships between the tables "Models"
    past_shows = []
    upcoming_shows = []
    past_count = 0
    upcoming_count = 0
    artists_shows_infos = db.session.query(showTable,Artist.name.label('artist_name'), Artist.image_link.label('artist_image'))\
            .join(Venue, Venue.id == showTable.columns.venue_id)\
            .join(Artist, Artist.id == showTable.columns.artist_id)\
            .filter(Venue.id == required_venue.id).all()
    for info in artists_shows_infos:
        # Check if the show was played or will be played in upcoming days
        if str_to_datetime(info.start_time) > datetime.utcnow():
            upcoming_count += 1
            upcoming_shows.append({
                "artist_id": info.artist_id,
                "artist_name": info.artist_name,
                "artist_image_link": info.artist_image,
                "start_time": info.start_time
            })
        else:
            past_count += 1
            past_shows.append({
                "artist_id": info.artist_id,
                "artist_name": info.artist_name,
                "artist_image_link": info.artist_image,
                "start_time": info.start_time
            })
    # Update the data dictionary with the shows information
    data.update({"past_shows": past_shows})
    data.update({"upcoming_shows": upcoming_shows})
    data.update({"past_shows_count": past_count})
    data.update({"upcoming_shows_count": upcoming_count})
    return render_template('pages/show_venue.html', venue=data)

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
    error = False
    try:
        # Get the data from the form to save it in the database
        venue = Venue(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            address=request.form['address'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link']
        )
        # Add the Venue Object to the db session
        db.session.add(venue)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Venue {request.form['name']} could not be listed.", 'warning')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
  # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        # Delete venue by id
        delete_venue = Venue.query.get(venue_id)
        db.session.delete(delete_venue)
        db.session.commit()
    except:
        # Error handling 
        error = True
        db.session.rollback()
    finally:
        # Close the session to be used with other processs
        db.session.close()

    return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
    # return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
    data = []
    # Get all the artist from db
    all_artists = Artist.query.all()
    for artist in all_artists:
        data.append({'id': artist.id, 'name': artist.name})
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
    search_word = request.form['search_term']
    # Get all the results that match the search word from db
    results = Artist.query.filter(Artist.name.ilike(f'%{search_word}%')).all()
    data = []
    for result in results:
        # Update data list with the matched artists
        data.append({'id': result.id, 'name': result.name, 'num_upcoming_shows': 0})
    response = {
        "count": len(results),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
    data = {}
    # Get the required artist to show its details with its id
    required_artist = Artist.query.get(artist_id)
    # Convert genres to list to be rendered in the correct way
    required_artist.genres = (required_artist.genres.replace('{', '')).replace('}', '').split(',')
    # Update the data dictionary with the artist details 
    data.update({
        'id': required_artist.id,
        'name': required_artist.name,
        "genres": required_artist.genres,
        "city": required_artist.city,
        "state": required_artist.state,
        "phone": required_artist.phone,
        "website": required_artist.website,
        "facebook_link": required_artist.facebook_link,
        "seeking_venue": required_artist.seeking_venue,
        "seeking_description": required_artist.seeking_description,
        "image_link": required_artist.image_link
    })
    # Get the shows details for this artist by using the relationships between the tables "Models"
    past_shows = []
    upcoming_shows = []
    past_count = 0
    upcoming_count = 0
    venues_shows_infos = db.session.query(showTable,Venue.name.label('venue_name'), Venue.image_link.label('venue_image'))\
            .join(Venue, Venue.id == showTable.columns.venue_id)\
            .join(Artist, Artist.id == showTable.columns.artist_id)\
            .filter(Artist.id == required_artist.id).all()
    for info in venues_shows_infos:
        # Check if the show was played or will be played in upcoming days
        if (str_to_datetime(info.start_time) > datetime.utcnow()):
            upcoming_count += 1
            upcoming_shows.append({
                "venue_id": info.venue_id,
                "venue_name": info.venue_name,
                "venue_image_link": info.venue_image,
                "start_time": info.start_time
            })
        else:
            past_count += 1
            past_shows.append({
                "venue_id": info.venue_id,
                "venue_name": info.venue_name,
                "venue_image_link": info.venue_image,
                "start_time": info.start_time
            })
    # Update the data dictionary with the shows information
    data.update({"past_shows": past_shows})
    data.update({"upcoming_shows": upcoming_shows})
    data.update({"past_shows_count": past_count})
    data.update({"upcoming_shows_count": upcoming_count})

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # Get the required artist to show its details with its id
  required_artist = Artist.query.get(artist_id)
    # Convert genres to list to be rendered in the correct way
  required_artist.genres = (required_artist.genres.replace('{', '')).replace('}', '').split(',')
  artist = {
      "id": required_artist.id,
      "name": required_artist.name,
      "genres": required_artist.genres,
      "city": required_artist.city,
      "state": required_artist.state,
      "phone": required_artist.phone,
      "website": required_artist.website,
      "facebook_link": required_artist.facebook_link,
      "seeking_venue": required_artist.seeking_venue,
      "seeking_description":required_artist.seeking_description,
      "image_link": required_artist.image_link
  }

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
    error = False
    update_artist = Artist.query.get(artist_id)
    try:
        # Update artist information from the from entry
        update_artist.name = request.form['name']
        update_artist.genres = request.form.getlist('genres')
        update_artist.city = request.form['city']
        update_artist.state = request.form['state']
        update_artist.phone = request.form['phone']
        update_artist.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Artist {request.form['name']} could not be updated.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Artist {request.form['name']} was successfully updated!", 'info')

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
  # Get the required artist to show its details with its id
    required_venue = Venue.query.get(venue_id)
    # Convert genres to list to be rendered in the correct way
    required_venue.genres = (required_venue.genres.replace('{', '')).replace('}', '').split(',')
    venue = {
        "id": required_venue.id,
        "name": required_venue.name,
        "genres": required_venue.genres,
        "address": required_venue.address,
        "city": required_venue.city,
        "state": required_venue.state,
        "phone": required_venue.phone,
        "website": required_venue.website,
        "facebook_link": required_venue.facebook_link,
        "seeking_talent": required_venue.seeking_talent,
        "seeking_description":required_venue.seeking_description,
        "image_link": required_venue.image_link
    }

  # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    update_venue = Venue.query.get(venue_id)
    try:
        # Update venue information from the from entry
        update_venue.name = request.form['name']
        update_venue.genres = request.form.getlist('genres')
        update_venue.city = request.form['city']
        update_venue.state = request.form['state']
        update_venue.address = request.form['address']
        update_venue.phone = request.form['phone']
        update_venue.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Venue {request.form['name']} could not be updated.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Venue {request.form['name']} was successfully updated!", 'info')

  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
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
    error = False
    try:
        # Get the data from the form to save it in the database
        artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link']
        )
        # Add the Artist Object to the db session
        db.session.add(artist)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Artist {request.form['name']} could not be listed.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
  # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
    data = []
    # Get all the artist from db
    all_shows = db.session.query(showTable,Venue.name.label('venue_name'),
    Artist.name.label('artist_name'),Artist.image_link.label('artist_image'))\
            .join(Venue, Venue.id == showTable.columns.venue_id)\
            .join(Artist, Artist.id == showTable.columns.artist_id)\
            .all()
    for show_info in all_shows:
        data.append({"venue_id": show_info.venue_id,
                     "venue_name": show_info.venue_name,
                     "artist_id": show_info.artist_id,
                     "artist_name": show_info.artist_name,
                     "artist_image_link": show_info.artist_image,
                     "start_time": show_info.start_time
                     })
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
    error = False
    try:
         # Get the data from the form to save it in the database
        insertShow = showTable.insert().values(
            {"venue_id":request.form['venue_id'], 
            "artist_id":request.form['artist_id'], 
            "start_time" : request.form['start_time']}
            )
        # Add the Show Object to the db session
        db.session.execute(insertShow)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Show on {request.form['start_time']} could not be listed.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()
    
    # Flash success message after correct database insertion
    if not error:
  # on successful db insert, flash success
        flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

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
