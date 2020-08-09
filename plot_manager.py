from collections import deque
from threading import Thread, Event
import time

class PlotManager:

    def __init__(self, app_mgr, socketio):
        self.app_mgr = app_mgr              # App Manager to get the current state
        self.socketio = socketio            # SocketIO connection

        self.plot_state = {
            "thread_interval": 1,
            "thread_alive": True,
            "is_volt_plot_init": False,
            "max_display_points": 100,
        }

        self.voltage_queue = deque(maxlen=self.plot_state["max_display_points"])
        self.ens_dt_queue = deque(maxlen=self.plot_state["max_display_points"])

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
                self.socketio.emit('update_volt_plot', {'x': list(self.ens_dt_queue), 'y': list(self.voltage_queue)},
                                   namespace='/rti')

                # Sleep a minimum about of time to ensure we are not updating too fast
                time.sleep(self.plot_state["thread_interval"])

    def add_ens(self, ens):
        """
        Add the new data to the queues to update the plots.
        Then wakeup the thread to pass to the data to the UI.
        :param ens: Ensemble data.
        """

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
            self.ens_dt_queue.append(datetime_now)

        # Wake up the thread
        self.plot_thread_event.set()



