from collections import deque
from rti_python.Writer.rti_sql import RtiSQL
from rti_python.Ensemble.Ensemble import Ensemble


class AmplitudeLinePlot:
    """
    Amplitude line plot.  Send the data to the javascript Plotly plot using SocketIO (websockets).
    """

    def __init__(self, max_display_points):
        """
        Initialize the queues to hold the latest ensemble data.
        """
        self.beam_0 = []
        self.beam_1 = []
        self.beam_2 = []
        self.beam_3 = []
        self.beam_vert = []
        self.bin_depth_list = []
        self.is_upward = False

        self.is_update = False                                              # Flag to tell whether to update the plot

    def add_ens(self, ens):
        """
        Add the latest ensemble data to the list.
        This will pull out the latest data from the given ensemble.
        :param ens: Latest Ensemble.
        """
        beam_0_list = []
        beam_1_list = []
        beam_2_list = []
        beam_3_list = []
        beam_vert_list = []

        # Update the voltage plot
        if ens.IsAncillaryData and ens.IsAmplitude:
            # Set if upward or downward
            self.is_upward = ens.AncillaryData.is_upward_facing()

            # Set the y axis as bin depth
            self.bin_depth_list = Ensemble.get_bin_depth_list(ens.AncillaryData.FirstBinRange,
                                                              ens.AncillaryData.BinSize,
                                                              ens.EnsembleData.NumBins)
            # Check if it is a vertical beam
            if ens.EnsembleData.NumBeams > 1:
                for bin_num in range(ens.EnsembleData.NumBins):
                    if ens.EnsembleData.NumBeams >= 0:
                        beam_0_list.append(ens.Amplitude.Amplitude[bin_num][0])
                    if ens.EnsembleData.NumBeams >= 1:
                        beam_1_list.append(ens.Amplitude.Amplitude[bin_num][1])
                    if ens.EnsembleData.NumBeams >= 2:
                        beam_2_list.append(ens.Amplitude.Amplitude[bin_num][2])
                    if ens.EnsembleData.NumBeams >= 3:
                        beam_3_list.append(ens.Amplitude.Amplitude[bin_num][3])
            if ens.EnsembleData.NumBeams == 1:
                beam_vert_list.append(ens.Amplitude.Amplitude[bin_num][0])

        # Set the lists
        self.beam_0 = beam_0_list
        self.beam_1 = beam_1_list
        self.beam_2 = beam_2_list
        self.beam_3 = beam_3_list
        self.beam_vert = beam_vert_list

        # Update the plot
        self.is_update = True

    def update_plot(self, socketio):
        """
        Update the plot with the latest data.
        Send the latest data to the socketio.
        :param socketio: SocketIO connection.
        """
        #if self.is_update:
        # Send the volt plot update
        socketio.emit('update_amp_plot',
                      {
                          'beam0': self.beam_0,
                          'beam1': self.beam_1,
                          'beam2': self.beam_2,
                          'beam3': self.beam_3,
                          'beamVert': self.beam_vert,
                          'binDepth': self.bin_depth_list
                      },
                      namespace='/rti')

            # Update the flag
            #self.is_update = False

    def plot_update_sqlite(self, sqlite_path):
        """
        Get the data from the sqlite DB file.  Then update the queues to update the plot.
        """
        # Create a connection to the sqlite file
        sql = RtiSQL(conn=sqlite_path, is_sqlite=True)

        # Get the voltage data from the sqlite file
        df_volt = sql.get_voltage_data(1)

        sql.close()

        # Add the data to the queue so the next refresh will show all the data
        self.voltage_dt_queue.extend(df_volt["datetime"])
        self.voltage_queue.extend(df_volt["voltage"])

        # Update the flag to plot
        self.is_update = True

    def clear(self):
        """
        Clear the plots.
        """
        self.beam_0.clear()
        self.beam_1.clear()
        self.beam_2.clear()
        self.beam_3.clear()
        self.beam_vert.clear()
        self.bin_depth_list.clear()

        # Update flag to update the plot
        self.is_update = True
