# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import abort

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"--------------------------------<br/>"
        f"Welcome to the API!<br/>"
        f"--------------------------------<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months"""
    # Calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    # abort code 404 if no data is found was suggested by Xpert Learning
    if not most_recent_date:
        abort(404, description="Data not found")

    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the last 12 months of precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    if not results:
        abort(404, description="Data not found")

    # Convert the query results to a dictionary
    precipitation = {date: prcp for date, prcp in results}

    # Returns JSON with the date as the key and the value as the precipitation
    # Only returns the JSONified precipitation data for the last year in the database
    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations"""
    # Query all stations
    results = session.query(Station.station).all()

    if not results:
        abort(404, description="Data not found")

    # Convert list of tuples into normal list
    stations_list = list(np.ravel(results))
    
    # Returns JSONified data of all of the stations in the database
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Temperature observations for the last year for the most active station"""
    # Identify the most active station, should be "USC00519281"
    most_active_station_id = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    
    if not most_active_station_id:
        abort(404, description="Data not found")

    most_active_station_id = most_active_station_id[0]

    # Calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    if not most_recent_date:
        abort(404, description="Data not found")

    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the temperature observations for the last year
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id).\
        filter(Measurement.date >= one_year_ago).all()

    if not temperature_data:
        abort(404, description="Data not found")

    # Convert the query results to a list of dictionaries
    tobs_list = [{date: tobs} for date, tobs in temperature_data]
    
    # Returns JSONified data for the most active station (USC00519281), and only returns the last year of data.
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
# this one seriously kicked my butt. I had to look up the solution to this one. I was not able to figure it out on my own.
def temperature_range(start, end=None):
    """Return TMIN, TAVG, and TMAX for a specified start or start-end range"""
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")
        #needed to convert the date to a string to avoid the error
    except ValueError:
        abort(400, description="Invalid date format. Use YYYY-MM-DD.")
# Exception handling was suggested by Xpert Learning. 
    if end:
        try:
            end_date = dt.datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            abort(400, description="Invalid date format. Use YYYY-MM-DD.")

        if end_date < start_date:
            abort(400, description="End date must be after start date.")
        
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date).\
        filter(Measurement.date <= end_date).all()
    else:
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date).all()

    if not results:
        abort(404, description="Data not found")

    # Return the query results directly as JSON
    tmin, tavg, tmax = results[0]
    return jsonify({"TMIN": tmin, "TAVG": tavg, "TMAX": tmax})

if __name__ == '__main__':
    app.run(debug=True)