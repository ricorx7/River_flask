
from threading import Thread, Event
import time
from rti_python.Ensemble.Ensemble import Ensemble
from plots.heatmap import HeatmapPlot
from plots.voltage import VoltageLinePlot
from plots.shiptrack import ShiptrackPlot
import pandas as pd


class PlotManager:

    def __init__(self, app_mgr, socketio):
        self.app_mgr = app_mgr              # App Manager to get the current state
        self.socketio = socketio            # SocketIO connection

        self.plot_state = {
            "thread_interval": 1,                           # Refresh rate for the plot
            "realtime_thread_alive": True,                  # Flag if realtime plotting thread is alive
            "is_volt_plot_init": False,                     # Flag if the volt plot has been created
            "max_display_points": 100,                      # Max points to display in plot
            "blank": 0.0,                                   # Blank
            "bin_size": 0.0,                                # Bin Size
            "num_bins": 0,                                  # Number of bins
            "is_upward_facing": False,                      # Flag if the ADCP is upward or downward facing
        }

        # Heatmap plot
        self.heatmap = HeatmapPlot(self.plot_state["max_display_points"])
        self.volt_line = VoltageLinePlot(self.plot_state["max_display_points"])
        self.shiptrack = ShiptrackPlot(self.plot_state["max_display_points"])

        # Init previous good Bottom Track Velocities
        self.prev_bt_east = Ensemble.BadVelocity
        self.prev_bt_north = Ensemble.BadVelocity
        self.prev_bt_vert = Ensemble.BadVelocity

        # Thread to plot the data
        self.plot_realtime_thread = None
        self.plot_realtime_thread_event = Event()
        self.start_realtime_thread(self.plot_state["thread_interval"])

    def start_realtime_thread(self, interval: int = 1):
        """
        Start the thread.  This will take a new interval
        and then start the thread.  If the thread is already
        alive, it will shut it down.
        :param interval: Time to sleep before plot updates in seconds.
        """
        # Check if the thread is already running
        if self.plot_state["realtime_thread_alive"]:
            self.stop_realtime_thread()

        # Store the new interval
        self.plot_state["thread_interval"] = interval

        # Create the timer thread
        self.plot_realtime_thread = Thread(name="plot_realtime_thread", target=self.update_plots_realtime_thread)
        self.plot_state["realtime_thread_alive"] = True
        self.plot_realtime_thread.start()

    def stop_realtime_thread(self):
        """
        Stop the thread.  Set the flag to stop the flag.
        Wakeup the thread to see the flag.
        """
        if self.plot_state["realtime_thread_alive"]:
            self.plot_state["realtime_thread_alive"] = False
            self.plot_realtime_thread_event.set()
            self.plot_realtime_thread = None

    def update_plots_realtime_thread(self):
        """
        Thread function to update the plot.
        This will be woken up when new data arrives.  It will then
        send the updated data to the websocket.  It will then sleep
        for a period of time before checking if it should wakeup again.  It
        sleeps to slow down the update rate to not refresh the plots to quickly.
        """
        # Wait for the thread to be awoken by new data
        while self.plot_state["realtime_thread_alive"]:
            if self.plot_realtime_thread_event.wait():
                # Update the voltage plot
                self.volt_line.update_plot(self.socketio)

                # Update the heatmap plot
                self.heatmap.update_plot(self.socketio)

                # Update the shiptrack plot
                self.shiptrack.update_plot(self.socketio)

                # Sleep a minimum about of time to ensure we are not updating too fast
                time.sleep(self.plot_state["thread_interval"])

    def add_ens(self, ens):
        """
        Add the new data to the queues to update the plots.
        Then wakeup the thread to pass to the data to the UI.
        :param ens: Ensemble data.
        """
        # Get the latest state of the ensembles
        self.get_ens_state(ens)

        # Remove the ship speed from the Earth Velocity
        self.remove_ship_speed(ens)

        # Set Voltage line plot data
        self.volt_line.add_ens(ens)

        # Set the Velocity Vector data for heatmap
        self.heatmap.add_ens(ens)

        # Add the Ship track data
        self.shiptrack.add_ens(ens)

        # Wake up the thread
        self.plot_realtime_thread_event.set()

    def get_ens_state(self, ens):
        if ens.IsAncillaryData:
            self.plot_state["blank"] = ens.AncillaryData.FirstBinRange
            self.plot_state["bin_size"] = ens.AncillaryData.BinSize
            self.plot_state["is_upward_looking"] = ens.AncillaryData.is_upward_facing()

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

    def playback_sqlite(self, sqlite_filepath):
        """
        Playback all the data from the sqlite file.
        This will query all the data, then update all the plots.
        :param sqlite_filepath: File path to sqlite DB RTI file.
        """
        # Clear the current plots
        self.clear_plots()

        # Pass the db to the plots
        self.volt_line.plot_update_sqlite(sqlite_path=sqlite_filepath)
        self.heatmap.plot_update_sqlite(sqlite_path=sqlite_filepath)
        self.shiptrack.plot_update_sqlite(sqlite_path=sqlite_filepath)

    def clear_plots(self):
        """
        Clear the plots.
        """
        self.volt_line.clear()
        self.heatmap.clear()
        self.shiptrack.clear()
