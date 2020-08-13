from collections import deque
import pandas as pd
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
        self.queue_mag = deque(maxlen=max_display_points)
        self.queue_dt = deque(maxlen=max_display_points)
        self.queue_bin_depth = deque(maxlen=max_display_points)
        self.queue_bt_dt = deque(maxlen=max_display_points)
        self.queue_bt_range = deque(maxlen=max_display_points)

        self.bin_depth_list = []

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

    def update_plot(self, socketio):
        """
        Update the plot using the SocketIO.  The latest
        information will be sent to the websocket and update
        the plotly plot.  The data is passed using a JSON object.
        :param socketio: SocketIO (websocket) connection.
        """
        # Send the magnitude heatmap plot update
        socketio.emit('update_heatmap_plot',
                      {
                          'hm_x': list(self.queue_dt),
                          'hm_y': self.bin_depth_list,
                          'hm_z': list(self.queue_mag),
                          "bt_x": list(self.queue_bt_dt),
                          "bt_y": list(self.queue_bt_range),
                          "is_upward": False,
                          "colorscale": 'Cividis'
                      },
                      namespace='/rti')

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
        unique_dt = df_mag.datetime.unique()
        for dt in unique_dt:
            # Accumulate all the datetime
            self.queue_dt.append(dt)

            # Get the list of all the magnitude values for this dt
            # Then accumulate all the magnitude values
            mag_dt_list = df_mag.loc[df_mag['datetime'] == dt]
            self.queue_mag.append(mag_dt_list['val'].tolist())

            # Accumulate the depths of each bin
            depth_list = (mag_dt_list['bin_num'] * mag_dt_list['bin_size'] + mag_dt_list['blank']).tolist()
            #self.queue_mag.append(depth_list)
            self.bin_depth_list = depth_list

        # Get all the range values for the bottom track line
        self.queue_bt_range.append(df_bt_range['avgRange'].tolist())

        # Get the datetime for the bottom track values
        self.queue_bt_dt.append(df_bt_range['datetime'].tolist())
