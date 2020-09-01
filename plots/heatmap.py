from collections import deque
import pandas as pd
import numpy as np
from rti_python.Writer.rti_sql import RtiSQL
from rti_python.Ensemble.Ensemble import Ensemble


class HeatmapPlot:
    """
    Plot the water vector data to the heatmap.  The x-axis will the datetime.  The y-axis will the bin depths.  The
    values will be the magnitude or direction.  There is also a bottom track line added to the plot.
    The plot is a Plotly javascript file.  The data is received through a websocket.  Then the plot is updated
    in javascript.

    Colorscale options:
    Viridis, Inferno, Cividis, RdBu, Bluered_r, ["red", "green", "blue"]), [(0, "red"), (0.5, "green"), (1, "blue")]
    """

    def __init__(self, max_display_points, bad_velocity=Ensemble.BadVelocity, min_z=0.0, max_z=0.0, mark_bad_below_bottom=True):
        """
        Initialize the queues to hold all the ensemble data.
        The queues will contain all the accumulated information.
        :param max_display_points: Maximum points to display in the plot
        :param bad_velocity: Bad Velocity to look for in the data.  If data exceeds this value, it is marked bad
        :param min_z: Minimum z value to display in color.  By default it looks for the minimum value
        :param max_z: Maximum z value to display in color.  By default it looks for the maximum value
        :param mark_bad_below_bottom: Mark the data below the bottom bad.
        """
        self.max_display_points = max_display_points
        self.bad_velocity = bad_velocity
        self.mark_bad_below_bottom = mark_bad_below_bottom

        #self.queue_mag = deque(maxlen=max_display_points)
        self.list_mag = []
        self.queue_dt = deque(maxlen=max_display_points)
        self.queue_bin_depth = deque(maxlen=max_display_points)
        self.queue_bt_dt = deque(maxlen=max_display_points)
        self.queue_bt_range = deque(maxlen=max_display_points)
        self.queue_bottom = deque(maxlen=max_display_points)

        self.bin_depth_list = []

        self.min_z = min_z            # Min magnitude value
        self.max_z = max_z            # Max magnitude value for color scale

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

        # Get the Ensemble data
        if ens.IsAncillaryData and ens.IsEnsembleData and ens.IsEarthVelocity:
            self.blank = ens.AncillaryData.FirstBinRange
            self.bin_size = ens.AncillaryData.BinSize
            self.is_upward_looking = ens.AncillaryData.is_upward_facing()

            # Add the datetime data
            self.queue_dt.append(ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f"))

            # Clear the current depth list
            self.bin_depth_list.clear()

            # Go through each bin to add the data
            for bin_num in range(ens.EnsembleData.NumBins):
                # Add a magnitude entry in the list for each bin
                if bin_num >= len(self.list_mag):
                    # Add a deque to the list for each bin
                    self.list_mag.append(deque(maxlen=self.max_display_points))

                # Check for the depth of the water
                depth = None
                bin_depth = None
                if ens.IsBottomTrack:
                    depth = ens.BottomTrack.avg_range()
                if ens.IsAncillaryData:
                    bin_depth = ens.AncillaryData.FirstBinRange + (ens.AncillaryData.BinSize * bin_num)

                # Check if we need to mark bad below bottom
                if self.mark_bad_below_bottom and depth and bin_depth and bin_depth >= depth:
                    self.list_mag[bin_num].append(None)
                # Add  the magnitude data if good data
                elif not Ensemble.is_bad_velocity(ens.EarthVelocity.Magnitude[bin_num]):
                    self.list_mag[bin_num].append(ens.EarthVelocity.Magnitude[bin_num])
                # If BAD_VELOCITY, then set the value to NONE
                else:
                    self.list_mag[bin_num].append(None)

                # Check for the min and max magnitude value
                self.check_min_max_z(self.list_mag[bin_num])

                # Set the bin depth
                if bin_depth:
                    self.bin_depth_list.append(bin_depth)
                else:
                    self.bin_depth_list.append(bin_num)

        # Keep track of BT Range
        if ens.IsEnsembleData and ens.IsBottomTrack and ens.BottomTrack.NumBeams >= 3:
            avg_range = ens.BottomTrack.avg_range()
            self.queue_bt_range.append(avg_range)
            self.queue_bt_dt.append(ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f"))

            # Create a line at the bottom of the plot to connect to the bottom track line
            # Make the length of the list the same as the number of range values
            self.queue_bottom.append(max(self.bin_depth_list))

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

        #if self.is_update:
        # Send the magnitude heatmap plot update
        socketio.emit('update_heatmap_plot',
                      {
                          'hm_x': list(self.queue_dt),
                          'hm_y': self.bin_depth_list,
                          'hm_z': mag_list,
                          'min_z': self.min_z,
                          'max_z': self.max_z,
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

        sql.close()

        # Get the list of all the average ranges
        avg_range_list = df_bt_range['avgRange'].tolist()
        bt_dt_list = df_bt_range['datetime'].tolist()

        # Find all the unique datetime to separate the ensembles
        # Then add them to the queue
        unique_dt = df_mag.datetime.unique()
        self.queue_dt.extend(unique_dt)

        # Set the depth list
        # Get the first dt to get all the bins associated with a specific datetime (ensemble)
        first_dt = unique_dt.flat[0]
        first_ens = df_mag.loc[df_mag['datetime'] == first_dt]
        self.is_upward_looking = bool(first_ens['isUpwardLooking'].iloc[0])
        self.bin_size = first_ens['bin_size'].iloc[0]
        self.blank = first_ens['blank'].iloc[0]

        # Get all the unique bin numbers
        # Sort them to be in order
        unique_bin_num = df_mag.bin_num.unique()
        unique_bin_num.sort()

        for bin_num in unique_bin_num:
            bin_depth = self.blank + (self.bin_size * bin_num)

            # Add the bins depths to the list
            self.bin_depth_list.append(bin_depth)

            # Get all the values for each bin
            bin_mags = df_mag.loc[df_mag['bin_num'] == bin_num]

            #if self.mark_bad_below_bottom and df_bt_range:


            # Remove any bad velocity data
            # Bad velocity is greater than 88.88
            # Convert to numpy array first then replace bad velocity values with None
            bin_mags_np = np.array(bin_mags['mag'].tolist())
            bin_mags_list = np.where(bin_mags_np >= self.bad_velocity, None, bin_mags_np).tolist()

            # Add a deque to the list for each bin
            self.list_mag.append(deque(maxlen=self.max_display_points))

            # Set all the magnitude values to the list
            self.list_mag[bin_num].extend(bin_mags_list)

            # Check for the min and max magnitude value
            self.check_min_max_z(bin_mags_list)

        # Get all the range values for the bottom track line
        self.queue_bt_range.extend(avg_range_list)

        # Get the datetime for the bottom track values
        self.queue_bt_dt.extend(bt_dt_list)

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
        self.list_mag.clear()
        self.queue_bin_depth.clear()
        self.queue_bt_range.clear()
        self.bin_depth_list.clear()

        # Set flag to update the plot
        self.is_update = True

    def check_min_max_z(self, mag_list):
        """
        Check if the minimum and maximum z need to be replaced.
        When checking, ignore None values.

        :param mag_list: List to check for min and max.
        """
        # Ensure a list is given and that it does not contain all None

        if mag_list and len(mag_list) > 0 and not all(v is None for v in mag_list):
            # Set the min and max value
            curr_min_z = min(x for x in mag_list if x is not None)
            if curr_min_z and curr_min_z < self.min_z:
                self.min_z = curr_min_z

            curr_max_z = max(x for x in mag_list if x is not None)
            if curr_max_z and curr_max_z > self.max_z:
                self.max_z = curr_max_z