from collections import deque
import pandas as pd


class HeatmapPlot:
    """
    Colorscale options:
    Viridis, Inferno, Cividis, RdBu, Bluered_r, ["red", "green", "blue"]), [(0, "red"), (0.5, "green"), (1, "blue")]
    """

    def __init__(self):
        self.df_earth_columns = ["dt", "type", "ss_code", "ss_config", "bin_num", "beam", "blank", "bin_size", "val"]
        # Use the load_data. notation to use variable within inner function
        self.ens_count = 0
        self.df_all_earth = pd.DataFrame({}, columns=self.df_earth_columns)

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
        if ens.IsBottomTrack and ens.BottomTrack.NumBeams >= 3:
            df_bt = ens.BottomTrack.encode_df(ens.EnsembleData.datetime(),
                                              ens.EnsembleData.SysFirmwareSubsystemCode,
                                              ens.EnsembleData.SubsystemConfig)

        # Create Dataframe
        if ens.IsAncillaryData and ens.IsEnsembleData:
            self.blank = ens.AncillaryData.FirstBinRange
            self.bin_size = ens.AncillaryData.BinSize
            self.is_upward_looking = ens.AncillaryData.is_upward_facing()

            df_earth = ens.EarthVelocity.encode_df(ens.EnsembleData.datetime(),
                                                   ens.EnsembleData.SysFirmwareSubsystemCode,
                                                   ens.EnsembleData.SubsystemConfig,
                                                   0.0,  # Replace BadVelocity
                                                   0.0,  # Replace BadVelocity
                                                   False,  # Do not include bad velocity
                                                   False)  # Do not include bad velocity

            # Merge the data to the global buffer
            if self.df_all_earth.empty:
                self.df_all_earth = df_earth
            else:
                # df_all_earth.append(df_earth, ignore_index=True, sort=False)
                self.df_all_earth = pd.concat([self.df_all_earth, df_earth])

    def plot_update(self, socketio):

        # Get the magnitude data from dataframe
        mag_data = self.df_all_earth.loc[self.df_all_earth['type'] == "Magnitude"]
        bt_range = self.df_all_earth.loc[self.df_all_earth['type'] == "BT_Avg_Range"]

        # Pull out the data from the dataframe
        bin_depth = (mag_data['bin_num'] * self.bin_size) + self.blank
        dates = mag_data['dt']
        mag_val = mag_data['val']
        bt_x = bt_range['dt']
        bt_y = bt_range['val']

        # Send the magnitude heatmap plot update
        socketio.emit('update_heatmap_plot',
                           {
                               'hm_x': dates.tolist(),
                               'hm_y': bin_depth.tolist(),
                               'hm_z': mag_val.tolist(),
                               "bt_x": bt_x.tolist(),
                               "bt_y": bt_y.tolist(),
                               "is_upward": False,
                               "colorscale": 'Cividis'
                           },
                           namespace='/rti')
