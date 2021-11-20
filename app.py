import numpy as np
import os
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)
print(Base.classes.keys())

#Measurement Table
Measurement=Base.classes.measurement

#Station Table
Station=Base.classes.station

# Flask Setup
app = Flask(__name__)

#Define root or home route,which lists all routes
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/2016-01-01<br>"
        f"/api/v1.0/2012-01-01/2013-01-01"
    )

@app.route("/api/v1.0/precipitation")
def prcp():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Returns all dates and Percipitaion readings"""

    #Query all Percipitation date in measurement table
    results=session.query(Measurement.date,Measurement.prcp).all()

    #Close Session
    session.close()

     #Create Dictionary for Percipitation
    all_prcp={}
    for row in results:
        all_prcp[row.date]=row.prcp # Stores Percipitation value with the recorded date key
    return(jsonify(all_prcp))

@app.route("/api/v1.0/stations")
def sta():

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Returns all stations"""

    #Query all stations data
    results=session.query(Station).all()
 
    #Close Session
    session.close()

    all_stations=[] # List of Stattions
    for row in results:
        station_dict={} #Create a dictionary of the current row.
        station_dict['name']=row.name
        station_dict['station']=row.station
        station_dict['latitude']=row.latitude
        station_dict['longitude']=row.longitude
                
        all_stations.append(station_dict) #Append Current Row dict to List
    
    return(jsonify(all_stations))

@app.route("/api/v1.0/tobs")
def tobs():

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Returns last 12 months Temperature obervations for the most active station"""

    #This gets the station with most observations i.e. active station
    ActiveStation=session.query(Station.station).filter(Station.station==Measurement.station).group_by(Station.station).order_by(func.count(Measurement.station).desc()).first()[0]
    #Get Latest Date for Active Station
    LatestDate=session.query(func.max(Measurement.date)).filter(Measurement.station==ActiveStation).all()[0][0]
    #Convert to Date
    LatestDate=datetime.strptime(LatestDate,'%Y-%m-%d')
    #Get date 12 months back from the latest date
    OneYearFromLatestDt=LatestDate + relativedelta(months=-12)
    # Query the dates and temperature observations of the most active station for the last year of data
    results=session.query(Measurement.date,Measurement.tobs).filter(Measurement.station==ActiveStation,Measurement.date>=func.date(OneYearFromLatestDt)).all()
 
    #Close Session
    session.close()

    #Create Dictionary for Temperatures
    all_tobs={}
    for row in results:
        all_tobs[row.date]=row.tobs #Stores Temeprature value with the recorded date key
    
    return(jsonify(all_tobs))

@app.route("/api/v1.0/<start>")
def temp_start_date(start):

    """calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date"""

    #Checks if the given Start Date is valid
    isValidDate=True
    year,month,day=start.split('-')
    try:
       dt.datetime(int(year), int(month), int(day))
    except ValueError:
        isValidDate = False
    
    if (isValidDate==False): #Returns below message for Invalid Date
        return("Invalid Date, Enter date as YYYY-MM-DD")
    
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Return min,max & Avg Temperatures for all dates greater than given date"""
    results=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start).all()
    # Get the First Value in First row of result
    first_value=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start).first()[0]

    #Close Session
    session.close()

    if (first_value is None): # If there is no data in the query results,returns below message.
        return("No Temperature recording for dates greater that this date")

    return(jsonify(results))

@app.route("/api/v1.0/<start>/<end>")
def temp_start_end_date(start,end):

    """calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive"""

    #Checks if the given Start Date is valid
    isValidDate=True
    start_year,start_month,start_day=start.split('-')
    try:
       dt.datetime(int(start_year), int(start_month), int(start_day))
    except ValueError:
        isValidDate = False
    
    if (isValidDate==False):
        return(jsonify("Invalid Start Date, Enter date as YYYY-MM-DD"))
    
    #Checks if the given End Date is valid
    end_year,end_month,end_day=end.split('-')
    try:
       dt.datetime(int(end_year), int(end_month), int(end_day))
    except ValueError:
        isValidDate = False
    
    if (isValidDate==False):
        return(jsonify("Invalid End Date, Enter date as YYYY-MM-DD"))
    
    
    #Checks if the given End Date is geater than start date
    if ((dt.datetime(int(start_year), int(start_month), int(start_day)))> (dt.datetime(int(end_year), int(end_month), int(end_day)))):
        return(jsonify("End Date has to be greater than start date"))
    
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Return min,max & Avg Temperatures for all dates greater than start date and less than end date"""
    results=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start,Measurement.date<=end).all()
    # Get the First Value in First row of result
    first_value=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start,Measurement.date<=end).first()[0]
    
    #Close Session
    session.close()

    
    if (first_value is None): # If there is no data in the query results,returns below message.
        return(jsonify("No Data for these dates"))
        
    return(jsonify(results))

if __name__ == '__main__':
    app.run(debug=False)