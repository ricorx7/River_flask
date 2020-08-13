from collections import deque
import pandas as pd
import numpy as np
from rti_python.Writer.rti_sql import RtiSQL


class HeatmapPlot:
    """
    Plot the water vector data to the heatmap.  The x-axis will the datetime.  The y-axis will the bin depths.  The
    values will be the magnitude or direction.  There is also a bottom track line added to the plot.
    The plot is a Plotly javascript file.  The data is received through a websocket.  Then the plot is updated
    in javascript.

    Colorscale options:
    Viridis, Inferno, Cividis, RdBu, Bluered_r, ["red", "green", "blue"]), [(0, "red"), (0.5, "green"), (1, "blue")]
    """

    def __init__(self, max_display_points):
        """
        Initialize the queues to hold all the ensemble data.
        The queues will contain all the accumulated information.
        """
        self.max_display_points = max_display_points

        #self.queue_mag = deque(maxlen=max_display_points)
        self.list_mag = []
        self.queue_dt = deque(maxlen=max_display_points)
        self.queue_bin_depth = deque(maxlen=max_display_points)
        self.queue_bt_dt = deque(maxlen=max_display_points)
        self.queue_bt_range = deque(maxlen=max_display_points)
        self.queue_bottom = deque(maxlen=max_display_points)

        self.bin_depth_list = []

        self.is_update = False      # Flag whether there is new data

        self.blank = 0.0
        self.bin_size = 0.0
        self.is_upward_looking = False

    def add_ens(self, ens):
        """
        Receive the data from the file.  It will process the file.
        When an ensemble is found, it will call this function with the
        complete ensemble.

        It is assumed the ship speed has already been removed.
        :param self:
        :param ens: Ensemble to process.
        :return:
        """
        #############################################
        # Assumed Ship Speed has already been removed
        #############################################

        # Keep track of previous BT speed
        if ens.IsEnsembleData and ens.IsBottomTrack and ens.BottomTrack.NumBeams >= 3:
            self.queue_bt_range.append(ens.BottomTrack.avg_range())
            self.queue_bt_dt.append(ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f"))

        # Get the Ensemble data
        if ens.IsAncillaryData and ens.IsEnsembleData and ens.IsEarthVelocity:
            self.blank = ens.AncillaryData.FirstBinRange
            self.bin_size = ens.AncillaryData.BinSize
            self.is_upward_looking = ens.AncillaryData.is_upward_facing()

            # Add the datetime data
            self.queue_dt.append(ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f"))

            # Add the magnitude data
            self.queue_mag.append(list(ens.EarthVelocity.Magnitude))

            # Create the bin depth list and add it to the queue
            temp_bin_depth_list = []
            for bin_num in range(ens.EnsembleData.NumBins):
                temp_bin_depth_list.append((bin_num * ens.AncillaryData.BinSize) + ens.AncillaryData.FirstBinRange)
            self.bin_depth_list = temp_bin_depth_list
            #self.queue_bin_depth.append(bin_depth_list)

        # Set flag to update the plot
        self.is_update = True

    def update_plot(self, socketio):
        """
        Update the plot using the SocketIO.  The latest
        information will be sent to the websocket and update
        the plotly plot.  The data is passed using a JSON object.
        :param socketio: SocketIO (websocket) connection.
        """
        # Convert the list of deque magnitudes to a list of magnitudes
        mag_list = []
        for mag_deque in self.list_mag:
            mag_list.append(list(mag_deque))

        # If downward looking, reverse the plot
        #temp_bin_depth_list = self.bin_depth_list
        #if not self.is_upward_looking:
        #    mag_list.reverse()
        #    temp_bin_depth_list.reverse()

        #if self.is_update:
        # Send the magnitude heatmap plot update
        socketio.emit('update_heatmap_plot',
                      {
                          'hm_x': list(self.queue_dt),
                          'hm_y': self.bin_depth_list,
                          'hm_z': mag_list,
                          "bt_x": list(self.queue_bt_dt),
                          "bt_y": list(self.queue_bt_range),
                          "bottom_x": list(self.queue_bt_dt),
                          "bottom_y": list(self.queue_bottom),
                          "is_upward": self.is_upward_looking,
                          "colorscale": 'Cividis'
                      },
                      namespace='/rti')

            # Reset flag
            #self.is_update = False

    def plot_update_sqlite(self, sqlite_path):
        """
        Get the data from the sqlite file.
        Then add it to the queue so it will be plotted on the next update.
        """
        # Create a connection to the sqlite file
        sql = RtiSQL(conn=sqlite_path, is_sqlite=True)

        df_bt_range = sql.get_bottom_track_range(1)
        df_mag = sql.get_mag(1)

        # Find all the unique datetime to separate the ensembles
        # Then add them to the queue
        unique_dt = df_mag.datetime.unique()
        self.queue_dt.extend(unique_dt)

        # Set the depth list
        # Get the first dt to get all the bins associated with a specific datetime (ensemble)
        first_dt = unique_dt.flat[0]
        first_ens = df_mag.loc[df_mag['datetime'] == first_dt]
        #self.bin_depth_list = (first_ens['bin_num'] * first_ens['bin_size'] + first_ens['blank']).tolist()
        self.is_upward_looking = bool(first_ens['isUpwardLooking'].iloc[0])
        self.bin_size = first_ens['bin_size'].iloc[0]
        self.blank = first_ens['bin_size'].iloc[0]

        # Get all the unique bin numbers
        # Sort them based on is_upward_looking
        unique_bin_num = df_mag.bin_num.unique()

        if self.is_upward_looking:
            unique_bin_num.sort()
        else:
            # Reorder the array for downward looking
            # Smallest depth is last entry
            -np.sort(-unique_bin_num)

        for bin_num in unique_bin_num:
            # Add the bins depths to the list
            self.bin_depth_list.append(self.blank + (self.bin_size * bin_num))

            # Get all the values for each bin
            bin_mags = df_mag.loc[df_mag['bin_num'] == bin_num]

            # Create a deque for each bin
            self.list_mag.append(deque(maxlen=self.max_display_points))

            # Remove any bad velocity data
            # Bad velocity is greater than 88.88
            # Convert to numpy array first then remove value
            bin_mags_np = np.array(bin_mags['mag'].tolist())
            bin_mags_list = np.where(bin_mags_np > 88.8, None, bin_mags_np).tolist()

            # Set all the magnitude values to the list
            #self.queue_mag.append(bin_mags["mag"].tolist())
            #self.list_mag[bin_num].extend(bin_mags["mag"].tolist())
            self.list_mag[bin_num].extend(bin_mags_list)

        #for dt in unique_dt:
        # Accumulate all the datetime
        #self.queue_dt.append(dt)

        # Get the list of all the magnitude values for this dt
        # Then accumulate all the magnitude values
        #mag_dt_list = df_mag.loc[df_mag['datetime'] == dt]
        #self.queue_mag.append(mag_dt_list['val'].tolist())

        # Accumulate the depths of each bin
        #depth_list = (mag_dt_list['bin_num'] * mag_dt_list['bin_size'] + mag_dt_list['blank']).tolist()
        #self.queue_mag.append(depth_list)
        #self.bin_depth_list = depth_list

        # Get all the range values for the bottom track line
        self.queue_bt_range.extend(df_bt_range['avgRange'].tolist())

        # Get the datetime for the bottom track values
        self.queue_bt_dt.extend(df_bt_range['datetime'].tolist())

        # Create a line at the bottom of the plot to connect to the bottom track line
        # Make the length of the list the same as the number of range values
        self.queue_bottom.extend([max(self.bin_depth_list)]*len(df_bt_range['avgRange'].tolist()))

        # Set flag to update the plot
        self.is_update = True

    def clear(self):
        """
        Clear the plot.
        """
        self.queue_dt.clear()
        self.queue_bt_dt.clear()
        #self.queue_mag.clear()
        self.list_mag.clear()
        self.queue_bin_depth.clear()
        self.queue_bt_range.clear()

        # Set flag to update the plot
        self.is_update = True
