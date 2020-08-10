from collections import deque
from rti_python.Writer.rti_sql import RtiSQL


class VoltageLinePlot:
    """
    Voltage line plot.  Send the data to the javascript Plotly plot using SocketIO (websockets).
    """

    def __init__(self, max_display_points):
        """
        Initialize the queues to hold the latest ensemble data.
        """
        # Store all the data to plot
        self.voltage_queue = deque(maxlen=max_display_points)                    # Voltage Line Plot Volt Values
        self.voltage_dt_queue = deque(maxlen=max_display_points)                 # Voltage Line Plot Datetime

    def add_ens(self, ens):
        """
        Add the latest ensemble data to the queues.
        This will pull out the latest data from the given ensemble.
        :param ens: Latest Ensemble.
        """
        #if ens.IsEnsembleData:
            # Display the voltage live
            #if not self.plot_state["is_volt_plot_init"]:
            #    self.socketio.emit('init_plots',
            #                       {
            #                           'x': [ens.EnsembleData.datetime_str()],
            #                           'y': [0]
            #                       },
            #                       namespace='/rti')
            #    self.plot_state["is_volt_plot_init"] = True

        # Update the voltage plot
        if ens.IsEnsembleData and ens.IsSystemSetup:
            datetime_now = ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f")
            voltage = ens.SystemSetup.Voltage
            self.voltage_queue.append(voltage)
            self.voltage_dt_queue.append(datetime_now)

    def update_plot(self, socketio):
        """
        Update the plot with the latest data.
        Send the latest data to the socketio.
        :param socketio: SocketIO connection.
        """
        # Send the volt plot update
        socketio.emit('update_volt_plot',
                      {
                          'x': list(self.voltage_dt_queue),
                          'y': list(self.voltage_queue)
                      },
                      namespace='/rti')

    def plot_update_sqlite(self, sqlite_path):
        # Create a connection to the sqlite file
        sql = RtiSQL(conn=sqlite_path, is_sqlite=True)

        # Get the voltage data from the sqlite file
        df_volt = sql.get_voltage_data(1)

        # Add the data to the queue so the next refresh will show all the data
        self.voltage_dt_queue.extend(df_volt["datetime"])
        self.voltage_queue.extend(df_volt["voltage"])

