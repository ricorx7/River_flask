from collections import deque
from rti_python.Writer.rti_sql import RtiSQL
from rti_python.Ensemble.NmeaData import NmeaData
import pandas as pd
import sqlite3
from pygeodesy import sphericalNvector


class ShiptrackPlot:
    """
    Ship Track line plot.  Send the data to the javascript Plotly plot using SocketIO (websockets).
    """

    def __init__(self, max_display_points, mag_scale_factor: float = 1.0):
        """
        Initialize the queues to hold the latest ensemble data.
        """
        # Store all the data to plot
        self.latitude_queue = deque(maxlen=max_display_points)              # Latitude Line Plot Volt Values
        self.longitude_queue = deque(maxlen=max_display_points)             # Longitude Line Plot Datetime
        self.water_vector_lat_queue = deque(maxlen=max_display_points * 3)  # Water Vector Lines, multiple by 2 to handle null
        self.water_vector_lon_queue = deque(maxlen=max_display_points * 3)  # Water Vector Lines, multiple by 2 to handle null
        self.water_vector_desc_queue = deque(maxlen=max_display_points * 3) # Hovertext for each water vector line
        self.min_lat = None
        self.max_lat = None
        self.min_lon = None
        self.max_lon = None
        self.mid_lat = None
        self.mid_lon = None
        self.mag_scale_factor = mag_scale_factor

        self.is_update = False                                              # Flag to tell whether to update the plot

    def add_ens(self, ens):
        """
        Add the latest ensemble data to the queues.
        This will pull out the latest data from the given ensemble.
        :param ens: Latest Ensemble.
        """
        # Update the voltage plot
        if ens.IsNmeaData:
            latitude = ens.NmeaData.latitude
            longitude = ens.NmeaData.longitude

            if latitude != 0.0 and longitude != 0.0:
                self.latitude_queue.append(latitude)
                self.longitude_queue.append(longitude)

                # If nothing is set yet, then use the initial values for min and max
                if not self.max_lat and latitude and longitude:
                    self.min_lat = latitude
                    self.max_lat = latitude
                    self.min_lon = longitude
                    self.max_lon = longitude
                elif latitude and longitude:
                    # Get Min and Max lat and lon for the scale of the plot
                    self.max_lat = max(self.max_lat, latitude)
                    self.max_lon = max(self.max_lon, longitude)
                    self.min_lat = min(self.min_lat, latitude)
                    self.min_lon = min(self.min_lon, longitude)

                # Update the plot
                self.is_update = True

        # Create the water current vector lines
        if ens.IsEarthVelocity and ens.IsNmeaData:
            # Get the average magnitude and direction
            avg_mag, avg_dir = ens.EarthVelocity.average_mag_dir()

            if avg_mag and avg_dir:
                # Get the water current vector lat and lon point to plot on the same plot
                wv_lat, wv_lon = ens.NmeaData.get_new_position(avg_mag * self.mag_scale_factor, avg_dir)

                # Add the original point and the new point to the queue
                self.water_vector_lat_queue.append(ens.NmeaData.latitude)
                self.water_vector_lon_queue.append(ens.NmeaData.longitude)
                self.water_vector_lat_queue.append(wv_lat)
                self.water_vector_lon_queue.append(wv_lon)

                # Text description of the point
                # Use None first to place the description on the end point of the line
                # Ignore the blank point
                wv_desc = ens.EnsembleData.datetime_str() + " Mag: " + str(round(avg_mag, 2)) + " Dir: " + str(round(avg_dir, 2))
                self.water_vector_desc_queue.append(None)
                self.water_vector_desc_queue.append(wv_desc)
                self.water_vector_desc_queue.append(None)

                # Add a NULL in the list of points to breakup lines
                self.water_vector_lat_queue.append(None)
                self.water_vector_lon_queue.append(None)

                # Update the plot
                self.is_update = True

    def update_plot(self, socketio):
        """
        Update the plot with the latest data.
        Send the latest data to the socketio.
        :param socketio: SocketIO connection.
        """

        # Choose a ellipsoid

        if self.min_lon and self.min_lat and self.max_lon and self.max_lat:
            LatLon = sphericalNvector.LatLon
            min_loc = LatLon(self.min_lat, self.min_lon)
            max_loc = LatLon(self.max_lat, self.max_lon)

            # Get the Midpoint of the min and max
            mid_loc = min_loc.midpointTo(max_loc)
            self.mid_lat = mid_loc.lat
            self.mid_lon = mid_loc.lon

        #if self.is_update:
        # Send the shiptrack plot update
        socketio.emit('update_shiptrack_plot',
                      {
                          'lat': list(self.latitude_queue),
                          'lon': list(self.longitude_queue),
                          'min_lat': self.min_lat,
                          'min_lon': self.min_lon,
                          'max_lat': self.max_lat,
                          'max_lon': self.max_lon,
                          'mid_lat': self.mid_lat,
                          'mid_lon': self.mid_lon,
                          'wv_lat': list(self.water_vector_lat_queue),
                          'wv_lon': list(self.water_vector_lon_queue),
                          "wv_desc": list(self.water_vector_desc_queue),
                      },
                      namespace='/rti')

            # Update the flag
            #self.is_update = False

    def plot_update_sqlite(self, sqlite_path):
        """
        Get the data from the sqlite DB file.  Then update the queues to update the plot.
        """
        # Create a connection to the sqlite file
        conn = sqlite3.connect(sqlite_path)

        # Get the voltage data from the sqlite file
        df_lat_lon = pd.read_sql_query("SELECT latitude, longitude, AvgMagnitude, AvgDirection, ensembles.dateTime "
                                       "FROM ensembles "
                                       "INNER JOIN nmea ON ensembles.id=nmea.ensIndex "
                                       "WHERE ensembles.project_id=1;", conn)

        conn.close()

        # Add the data to the queue so the next refresh will show all the data
        self.latitude_queue.extend(df_lat_lon["latitude"])
        self.longitude_queue.extend(df_lat_lon["longitude"])

        # Get Min and Max lat and lon for the scale of the plot
        self.min_lat = min(df_lat_lon["latitude"])
        self.min_lon = min(df_lat_lon["longitude"])
        self.max_lat = max(df_lat_lon["latitude"])
        self.max_lon = max(df_lat_lon["longitude"])

        # Go through each ensemble and add the water vector line to the lat/lon position
        for ens_row in range(len(df_lat_lon["latitude"])):
            avg_mag = df_lat_lon["AvgMagnitude"][ens_row]
            avg_dir = df_lat_lon["AvgDirection"][ens_row]
            curr_lat = df_lat_lon["latitude"][ens_row]
            curr_lon = df_lat_lon["longitude"][ens_row]
            ens_dt = df_lat_lon["dateTime"][ens_row]

            # Get the water current vector lat and lon point to plot on the same plot
            # Calculate the new position based on the mag and dir
            wv_lat, wv_lon = NmeaData.get_new_lat_lon_position(curr_lat, curr_lon, avg_mag * self.mag_scale_factor, avg_dir)

            # Add the original point and the new point to the queue
            self.water_vector_lat_queue.append(curr_lat)
            self.water_vector_lon_queue.append(curr_lon)
            self.water_vector_lat_queue.append(wv_lat)
            self.water_vector_lon_queue.append(wv_lon)

            # Text description of the point
            # Use None first to place the description on the end point of the line
            # Ignore the blank point
            wv_desc = str(ens_dt) + " Mag: " + str(round(avg_mag, 2)) + " Dir: " + str(
                round(avg_dir, 2))
            self.water_vector_desc_queue.append(None)
            self.water_vector_desc_queue.append(wv_desc)
            self.water_vector_desc_queue.append(None)

            # Add a NULL in the list of points to breakup lines
            self.water_vector_lat_queue.append(None)
            self.water_vector_lon_queue.append(None)

        # Update the flag to plot
        self.is_update = True

    def clear(self):
        """
        Clear the plots.
        """
        self.latitude_queue.clear()
        self.longitude_queue.clear()
        self.water_vector_lon_queue.clear()
        self.water_vector_lat_queue.clear()
        self.water_vector_desc_queue.clear()

        self.min_lat = None
        self.max_lat = None
        self.min_lon = None
        self.max_lon = None

        # Update flag to update the plot
        self.is_update = True
