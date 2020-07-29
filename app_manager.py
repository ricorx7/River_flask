import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
from rti_python.Comm.adcp_serial_port import AdcpSerialPort
import rti_python.Datalogger.DataloggerHardware as data_logger
from vm import DataloggrGui
import threading
import logging
import serial
import time


class AppManager:

    def __init__(self, socketio):
        self.plot = self.create_plot()
        self.socketio = socketio

        self.serial_port = None
        self.serial_thread = None
        self.serial_thread_alive = False

        # GUI object to keep track of state
        self.gui = DataloggrGui.DataloggrGui()

    def get_plot(self):
        return self.plot

    def create_plot(self):
        N = 40
        x = np.linspace(0, 1, N)
        y = np.random.randn(N)
        df = pd.DataFrame({'x': x, 'y': y})  # creating a sample dataframe

        data = [
            go.Bar(
                x=df['x'],  # assign x as the dataframe column 'x'
                y=df['y']
            )
        ]

        graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    def socketio_background_thread(self):
        """
        Background worker.  This will maintain the status of the
        backend and the GUI.
        Send the status of the Datalogger download process.
        This will continously check the status of the process.
        """
        count = 0
        while True:
            # Wait time
            self.socketio.sleep(5)
            count += 1

            # Send a debug status to websocket
            self.socketio.emit('status_report',
                               {'data': 'Server generated event', 'count': count},
                               namespace='/rti')

            # Get the Datalogger status
            #dl_status = logger_hardware.get_status()

            # Set the Datalogger status to the gui
            #gui.set_dl_status(dl_status)

            # Get the gui status as json
            #json_gui = gui.get_json()

            # Pass the status to the websocket
            #self.socketio.emit('gui_status', json_gui, namespace='/test')

    def connect_serial(self, comm_port: str, baud: int):
        """
        Connect the serial port.
        Start the serial port read thread.
        """
        if not self.serial_port:
            try:
                self.serial_port = AdcpSerialPort(comm_port, baud)
            except ValueError as ve:
                logging.error("Error opening serial port. " + str(ve))
                return "Error opening serial port. " + str(ve)
            except serial.SerialException as se:
                logging.error("Error opening serial port. " + str(se))
                return "Error opening serial port. " + str(se)
            except Exception as e:
                logging.error("Error opening serial port. " + str(e))
                return "Error opening serial port. " + str(e)

            # Start the read thread
            self.serial_thread_alive = True
            self.serial_thread = threading.Thread(name="Serial Terminal Thread", target=self.serial_thread_worker)
            self.serial_thread.start()

            return "Connected"

    def disconnect_serial(self):
        """
        Disconnect the serial port.
        """
        self.serial_thread_alive = False

        if self.serial_port:
            self.serial_port.disconnect()
            self.serial_port = None

    def send_serial_break(self):
        if self.serial_port:
            self.serial_port.send_break()

    def send_serial_cmd(self, cmd):
        if self.serial_port:
            self.serial_port.send_cmd(cmd=cmd)

    def serial_thread_worker(self):
        """
        Thread worker to handle reading the serial port.
        :param mgr: This Object to get access to the variables.
        :return:
        """
        while self.serial_thread_alive:
            try:
                if self.serial_port.raw_serial.in_waiting:
                    # Read the data from the serial port
                    data = self.serial_port.read(self.serial_port.raw_serial.in_waiting)

                    try:
                        ascii_data = data.decode('ascii')
                        logging.debug(ascii_data)

                        self.socketio.emit('serial_comm',
                                           {'data': ascii_data},
                                           namespace='/rti')
                        print(ascii_data)

                    except Exception as ex:
                        # Do nothing
                        logging.error("Error Reading serial data" + str(ex))

                    # Record data if turned on
                    #vm.record_data(data)

                    # Publish the data
                    #vm.on_serial_data(data)

                time.sleep(0.01)
            except serial.SerialException as se:
                logging.error("Error using the serial port.\n" + str(se))
                self.disconnect_serial()
            except Exception as ex:
                logging.error("Error processing the data.\n" + str(ex))
