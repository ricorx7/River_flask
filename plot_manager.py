from collections import deque
from threading import Thread, Event
import time
from rti_python.Ensemble.Ensemble import Ensemble
from plots.heatmap import HeatmapPlot
import pandas as pd


class PlotManager:

    def __init__(self, app_mgr, socketio):
        self.app_mgr = app_mgr              # App Manager to get the current state
        self.socketio = socketio            # SocketIO connection

        # Heatmap plot
        self.heatmap = HeatmapPlot()

        self.plot_state = {
            "thread_interval": 1,                           # Refresh rate for the plot
            "thread_alive": True,                           # Flag if plotting thread is alive
            "is_volt_plot_init": False,                     # Flag if the volt plot has been created
            "max_display_points": 100,                      # Max points to display in plot
            "blank": 0.0,                                   # Blank
            "bin_size": 0.0,                                # Bin Size
            "num_bins": 0,                                  # Number of bins
            "is_upward_facing": False,                      # Flag if the ADCP is upward or downward facing
        }

        # Init previous good Bottom Track Velocities
        self.prev_bt_east = Ensemble.BadVelocity
        self.prev_bt_north = Ensemble.BadVelocity
        self.prev_bt_vert = Ensemble.BadVelocity

        # Store all the data to plot
        self.voltage_queue = deque(maxlen=self.plot_state["max_display_points"])                    # Voltage Line Plot Volt Values
        self.voltage_dt_queue = deque(maxlen=self.plot_state["max_display_points"])                 # Voltage Line Plot Datetime

        # Thread to plot the data
        self.plot_thread = None
        self.plot_thread_event = Event()
        self.start_thread(self.plot_state["thread_interval"])

    def start_thread(self, interval: int = 1):
        """
        Start the thread.  This will take a new interval
        and then start the thread.  If the thread is already
        alive, it will shut it down.
        :param interval: Time to sleep before plot updates in seconds.
        """
        # Check if the thread is already running
        if self.plot_state["thread_alive"]:
            self.stop_thread()

        # Store the new interval
        self.plot_state["thread_interval"] = interval

        # Create the timer thread
        self.plot_thread = Thread(name="plot_thread", target=self.update_plots_thread)
        self.plot_state["thread_alive"] = True
        self.plot_thread.start()

    def stop_thread(self):
        """
        Stop the thread.  Set the flag to stop the flag.
        Wakeup the thread to see the flag.
        """
        if self.plot_state["thread_alive"]:
            self.plot_state["thread_alive"] = False
            self.plot_thread_event.set()
            self.plot_thread = None

    def update_plots_thread(self):
        """
        Thread function to update the plot.
        This will be woken up when new data arrives.  It will then
        send the updated data to the websocket.  It will then sleep
        for a period of time before checking if it should wakeup again.  It
        sleeps to slow down the update rate to not refresh the plots to quickly.
        """
        # Wait for the thread to be awoken by new data
        while self.plot_state["thread_alive"]:
            if self.plot_thread_event.wait():
                # Send the volt plot update
                self.socketio.emit('update_volt_plot',
                                   {'x': list(self.voltage_dt_queue), 'y': list(self.voltage_queue)},
                                   namespace='/rti')

                # Update the heatmap plot
                self.heatmap.plot_update(self.socketio)

                # Sleep a minimum about of time to ensure we are not updating too fast
                time.sleep(self.plot_state["thread_interval"])

    def add_ens(self, ens):
        """
        Add the new data to the queues to update the plots.
        Then wakeup the thread to pass to the data to the UI.
        :param ens: Ensemble data.
        """
        # Set Voltage line Plot data
        self.set_voltage_line_plot(ens)

        # Get the latest state of the ensembles
        self.get_ens_state(ens)

        # Remove the ship speed from the Earth Velocity
        self.remove_ship_speed(ens)

        # Set the Velocity Vector data for heatmap
        self.heatmap.add_ens(ens)

        # Wake up the thread
        self.plot_thread_event.set()

    def get_ens_state(self, ens):
        if ens.IsAncillaryData:
            self.plot_state["blank"] = ens.AncillaryData.FirstBinRange
            self.plot_state["bin_size"] = ens.AncillaryData.BinSize
            self.plot_state["is_upward_looking"] = ens.AncillaryData.is_upward_facing()

    def set_voltage_line_plot(self, ens):
        if ens.IsEnsembleData:
            # Display the voltage live
            if not self.plot_state["is_volt_plot_init"]:
                self.socketio.emit('init_plots',
                                   {'x': [ens.EnsembleData.datetime_str()], 'y': [0]}, namespace='/rti')
                self.plot_state["is_volt_plot_init"] = True

        # Update the voltage plot
        if ens.IsEnsembleData and ens.IsSystemSetup:
            datetime_now = ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f")
            voltage = ens.SystemSetup.Voltage
            self.voltage_queue.append(voltage)
            self.voltage_dt_queue.append(datetime_now)

    def remove_ship_speed(self, ens):
        """
        Store the last good bottom track velocity data.  Then use it to remove the ship
        speed from the Earth velocities and velocity vectors.
        :param ens: Ensemble data
        """
        if ens.IsBottomTrack and ens.IsEarthVelocity and ens.BottomTrack.NumBeams >= 3:
            # Check bottom track velocity for good data
            # If the bt velocity is not bad, then store it for next time
            # if it is bad, then use the previous good value
            # East
            if not Ensemble.is_bad_velocity(ens.BottomTrack.EarthVelocity[0]):
                self.prev_bt_east = ens.BottomTrack.EarthVelocity[0]

            # North
            if not Ensemble.is_bad_velocity(ens.BottomTrack.EarthVelocity[1]):
                self.prev_bt_north = ens.BottomTrack.EarthVelocity[1]

            # Vertical
            if not Ensemble.is_bad_velocity(ens.BottomTrack.EarthVelocity[2]):
                self.prev_bt_vert = ens.BottomTrack.EarthVelocity[2]

            # Remove the ship speed
            ens.EarthVelocity.remove_vessel_speed(bt_east=self.prev_bt_east, bt_north=self.prev_bt_north, bt_vert=self.prev_bt_vert)

