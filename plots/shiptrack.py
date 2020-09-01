from collections import deque
from rti_python.Writer.rti_sql import RtiSQL
import pandas as pd
import sqlite3


class ShiptrackPlot:
    """
    Ship Track line plot.  Send the data to the javascript Plotly plot using SocketIO (websockets).
    """

    def __init__(self, max_display_points):
        """
        Initialize the queues to hold the latest ensemble data.
        """
        # Store all the data to plot
        self.latitude_queue = deque(maxlen=max_display_points)             # Latitude Line Plot Volt Values
        self.longitude_queue = deque(maxlen=max_display_points)            # Longitude Line Plot Datetime
        self.min_lat = None
        self.max_lat = None
        self.min_lon = None
        self.max_lon = None

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

    def update_plot(self, socketio):
        """
        Update the plot with the latest data.
        Send the latest data to the socketio.
        :param socketio: SocketIO connection.
        """
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
        df_lat_lon = pd.read_sql_query("SELECT latitude, longitude "
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


        # Update the flag to plot
        self.is_update = True

    def clear(self):
        """
        Clear the plots.
        """
        self.latitude_queue.clear()
        self.longitude_queue.clear()

        self.min_lat = None
        self.max_lat = None
        self.min_lon = None
        self.max_lon = None

        # Update flag to update the plot
        self.is_update = True