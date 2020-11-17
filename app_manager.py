import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from mttkinter import mtTkinter
from tkinter import filedialog
import json
from rti_python.Comm.adcp_serial_port import AdcpSerialPort
import rti_python.Comm.adcp_serial_port as serial_port
from rti_python.Codecs.AdcpCodec import AdcpCodec
from rti_python.Writer.rti_sqlite_projects import RtiSqliteProjects
import threading
import logging
import serial
import time
import datetime
import os
import pathlib
from datetime import timedelta
from collections import deque
import re
from plot_manager import PlotManager
from rti_python.River.RiverProjectManager import RiverProjectManager, RiverProjectMeta
from rti_python.Writer.rti_sqlite_projects import RtiSqliteProjects
from rti_python.River.Transect import Transect
from rti_python.Utilities.config import RtiConfig
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Writer.rti_binary import RtiBinaryWriter


class AppManager:

    def __init__(self, socketio):
        self.plot = self.create_plot()
        self.socketio = socketio

        # RTI Configuration
        self.rti_config = RtiConfig(file_path="config.ini")
        self.rti_config.init_river_project_config()

        # Plot manager to keep track of plots
        self.plot_mgr = PlotManager(app_mgr=self, socketio=socketio)

        # River Project Manager to keep track of River projects
        self.river_prj_mrg = RiverProjectManager(self.rti_config)

        # ADCP Codec to decode the ADCP data
        self.adcp_codec = AdcpCodec()
        self.adcp_codec.ensemble_event += self.process_ensemble

        # Serial Port
        self.serial_port = None
        self.serial_thread = None
        self.serial_thread_alive = False

        self.app_state = {
            "is_serial_connected": False,                       # Is the serial port connected
            "serial_status": [],                                # Status of the serial connection
            "selected_serial_port": "",                         # Comm port selected
            "selected_baud": "115200",                          # Baud rate selected
            "is_serial_error":  False,                          # Any serial errors.
            "serial_error_status": [],                          # List of error messages
            "baud_list": self.get_baud_rates(),                 # List of all available Baud rates
            "serial_port_list": self.get_serial_ports(),        # List of all available Serial Ports
            "serial_raw_ascii": "",                             # Raw ascii from the serial port
            "max_ascii_buff": 10000,                            # Maximum number of characters to keep in serial ASCII buffer
            "adcp_break": {},                                   # Results of a BREAK statement
            "adcp_ens_num": 0,                                  # Latest Ensemble number
            "selected_files": [],                               # Selected files to playback,
            "selected_project_db": None,                           # Selected Project,
            "prj_name": "",                                     # Current project name
            "prj_path": "",                                     # Current project folder path
        }

        self.transect_state = {
            "transect_index": 1,        # Current index for the transect
            "transect_dt_start": None,  # Start datetime of the transect
            "transect_duration": None,  # Time duration of the transect
            "voltage": 0.0,             # System Voltage
        }

        # Current Transect
        self.db_file = None                         # DB file to store the ensembles and transects
        self.raw_file = None                        # Raw binary file to the store the ensemble data
        self.is_record_raw_data = self.rti_config.config['RIVER']['auto_save_raw']     # Automatically save on startup
        self.curr_ens_index = 0                     # Index the project DB for the latest ensemble
        self.transect_index = 0                     # Transect Index
        self.transect = None                        # Current transect

        #self.is_volt_plot_init = False
        #self.voltage_queue = deque(maxlen=100)
        #self.ens_dt_queue = deque(maxlen=100)

        # Incoming serial data
        self.serial_raw_bytes = None

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

    def clear_plots(self):
        """
        Clear all the plots.
        """
        self.plot_mgr.clear_plots()

    def create_river_project(self):
        """
        Create a river project file if it does not exist.
        This will keep all the ensemble and transect information.
        Also create a raw data file to store all the incoming serial data.
        """
        if not self.db_file:
            curr_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            #prj_file = self.river_prj_mrg.create_project(curr_datetime)
            #self.app_state["prj_name"] = curr_datetime
            #self.app_state["prj_path"] = prj_file.file_path

            db_file_path = os.path.join(self.rti_config.config['RIVER']['output_dir'], curr_datetime + ".db")
            self.db_file = RtiSqliteProjects(db_file_path)
            self.db_file.create_tables()

            self.raw_file = RtiBinaryWriter(folder_path=self.rti_config.config['RIVER']['output_dir'])

    def create_transect(self):
        # Create a transect
        if not self.transect:
            self.transect = Transect(self.transect_next_index)

        # Ensure the project is created
        self.create_river_project(self)

        # Start recording a transect file
        if self.raw_file:
            self.raw_file.close()

        file_transect_header = "Transect_" + str(self.transect_index)
        self.raw_file = RtiBinaryWriter(folder_path=self.rti_config.config['RIVER']['output_dir'], header=file_transect_header)

    def update_site_info(self, site_info):
        """
        Update the site information for the transect.
        """
        # Create the transect if it is not created
        self.create_transect()

        # Set the values
        self.transect.site_name = site_info["site_name"]
        self.transect.station_number = site_info["station_number"]
        self.transect.location = site_info["location"]
        self.transect.party = site_info["party"]
        self.transect.boat = site_info["boat"]
        self.transect.measurement_num = site_info["measurement_num"]
        self.transect.comments = site_info["comments"]

        # Write the data to the transect
        self.db_file.update_transect(self.transect)

    def start_transect(self):
        """
        Start the transect.  Take all the information from the transect settings
        and write it to the db file.
        """
        # Create the project db file if it does not exist
        self.create_river_project()

        # Create a transect
        if not self.transect:
            self.transect = Transect(self.transect_next_index)

        # Set the start datetime
        self.transect.start_datetime = datetime.datetime.now()

        # Set the first ensemble for the transect
        self.transect.start_ens_index = self.curr_ens_index

    def stop_transect(self):
        """
        Stop the transect.  Set the last ensemble in the transect.
        Make the discharge calculation.
        Record the transect information to the DB file.
        """
        # Create the project db file if it does not exist
        self.create_river_project()

        # Set the stop datetime
        self.transect.stop_datetime = datetime.datetime.now()

        # Set the last ensemble for the transect
        self.transect.last_ens_index = self.curr_ens_index

        # Add the transect to the db file
        self.db_file.add_transect(self.transect)

        # Increment the transect index for the next transect
        self.transect_index = self.transect_next_index + 1

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

    def get_serial_ports(self):
        return serial_port.get_serial_ports()

    def get_baud_rates(self):
        return serial_port.get_baud_rates()

    def connect_serial(self, comm_port: str, baud: int):
        """
        Connect the serial port.
        Start the serial port read thread.
        """
        # Set App State
        self.app_state["selected_serial_port"] = comm_port
        self.app_state["selected_baud"] = str(baud)

        if not self.serial_port:
            try:
                self.serial_port = AdcpSerialPort(comm_port, baud)
            except ValueError as ve:
                logging.error("Error opening serial port. " + str(ve))
                self.app_state["is_serial_connected"] = False
                self.app_state["is_serial_error"] = True
                self.app_state["serial_error_status"].append("Error opening serial port. " + str(ve))
                return self.app_state
            except serial.SerialException as se:
                logging.error("Error opening serial port. " + str(se))
                self.app_state["is_serial_connected"] = False
                self.app_state["is_serial_error"] = True
                self.app_state["serial_error_status"].append("Error opening serial port. " + str(se))
                return self.app_state
            except Exception as e:
                logging.error("Error opening serial port. " + str(e))
                self.app_state["is_serial_connected"] = False
                self.app_state["is_serial_error"] = True
                self.app_state["serial_error_status"].append("Error opening serial port. " + str(e))
                return self.app_state

            # Start the read thread
            self.serial_thread_alive = True
            self.serial_thread = threading.Thread(name="Serial Terminal Thread", target=self.serial_thread_worker)
            self.serial_thread.start()

            # Set the app state
            self.app_state["is_serial_connected"] = True
            self.app_state["is_serial_error"] = False
            self.app_state["serial_status"].clear()
            self.app_state["serial_status"].append("Connected")

            # Send a BREAK to get ADCP Information
            self.send_serial_break()

            # Clear the plots to get new data
            self.clear_plots()

            return self.app_state

    def disconnect_serial(self):
        """
        Disconnect the serial port.
        """
        self.serial_thread_alive = False

        if self.serial_port:
            self.serial_port.disconnect()
            self.serial_port = None

            # Set the app state
            self.app_state["is_serial_connected"] = False
            self.app_state["is_serial_error"] = False
            self.app_state["serial_status"].clear()
            self.app_state["serial_error_status"].clear()
            self.app_state["serial_status"].append("Disconnected")

        return self.app_state

    def send_serial_break(self):
        if self.serial_port:

            # Clear the buffer of the serial data
            # We can then check for the results
            self.app_state["serial_raw_ascii"] = ""

            self.serial_port.send_break()

            # Wait a second for result
            time.sleep(1.2)

            # Get the results of the BREAK
            break_results = self.app_state["serial_raw_ascii"]
            logging.debug(break_results)

            # Decode the BREAK result
            self.app_state["adcp_break"] = self.adcp_codec.decode_BREAK(break_results)
            logging.debug(self.app_state["adcp_break"])

            return self.app_state["adcp_break"]

    def send_serial_cmd(self, cmd):
        if self.serial_port:
            self.serial_port.send_cmd(cmd=cmd)

    def playback_files(self):
        """
        Display a dialog box to select the files.
        :return: List of all the files selected.
        """
        self.app_state["selected_files"] = self.select_files_playback()

        # Plot all the plots
        if len(self.app_state["selected_files"]) >= 1:

            # Get the directory of the first file selected
            file_dir = os.path.dirname(self.app_state["selected_files"][0])
            file_name_no_ext = pathlib.Path(self.app_state["selected_files"][0]).stem
            file_ext = pathlib.Path(self.app_state["selected_files"][0]).suffix

            # Check if it is a raw file or DB file
            if file_ext == '.bin' or file_ext == '.ens' or file_ext == '.rtb' or file_ext == '.BIN' or file_ext == '.ENS' or file_ext == '.RTB':
                # Create a project DB file
                project_path = os.path.join(file_dir, file_name_no_ext + RtiSqliteProjects.FILE_EXT)
                playback_project = RtiSqliteProjects(project_path)

                # Load the files to the project
                # Use a thread to load the data
                read_file_thread = threading.Thread(target=self.load_raw_files, args=[project_path], name="Read Raw File Thread")

                # Start the thread then wait for it to finish before moving on
                read_file_thread.start()
                read_file_thread.join()
                #playback_project.load_files(self.app_state['selected_files'])

                # Reset what the selected project is
                self.app_state['selected_project_db'] = project_path

            # Check if the file is a RDB file
            elif file_ext == '.rdb' or file_ext == '.RDB' or file_ext == RtiSqliteProjects.FILE_EXT:
                self.app_state["selected_project_db"] = self.app_state["selected_files"][0]

            # Load plot the DB data
            if self.app_state["selected_project_db"]:
                self.plot_mgr.playback_sqlite(self.app_state["selected_project_db"])

        return self.app_state["selected_project_db"]

    def load_raw_files(self, project_path):
        """
        Load the raw data to the project.
        :param project_path: Path to the RDB file.
        :return:
        """
        playback_project = RtiSqliteProjects(project_path)

        # Load the files to the project
        playback_project.load_files(self.app_state['selected_files'])

    def select_files_playback(self):
        """
        Display a dialog box to select the files.
        :return: List of all the files selected.
        """
        # Dialog to ask for a file to select
        root = mtTkinter.Tk()
        root.overrideredirect(True)         # Used to Bring window to front and focused
        root.geometry('0x0+0+0')            # Used to Bring window to front and focused
        root.focus_force()                  # Used to Bring window to front and focused
        filetypes = [("RDB files", "*.rdb"), ("ENS Files", "*.ens"), ("BIN Files", "*.bin"), ('All Files', '*.*')]
        file_paths = filedialog.askopenfilenames(parent=root, title="Select File to Playback", filetypes=filetypes)
        root.withdraw()

        print(str(file_paths))

        return file_paths

    def process_ensemble(self, sender, ens):
        """"
        Process the next incoming ensemble.
        """
        heading = 0.0
        pitch = 0.0
        roll = 0.0
        voltage = 0.0
        water_temp = 0.0
        transect_duration = ""
        ens_time = ""
        adcp_ens_num = 0
        if ens.IsEnsembleData:
            #print(str(ens.EnsembleData.EnsembleNumber))
            self.app_state["adcp_ens_num"] = ens.EnsembleData.EnsembleNumber
            adcp_ens_num = ens.EnsembleData.EnsembleNumber

            if not self.transect_state["transect_dt_start"]:
                self.transect_state["transect_dt_start"] = ens.EnsembleData.datetime()

            # Calculate the time between when transect started and now
            self.transect_state["transect_duration"] = (ens.EnsembleData.datetime() - self.transect_state["transect_dt_start"]).total_seconds()
            #duration = (ens.EnsembleData.datetime() - self.app_state["transect_dt_start"]).total_seconds()
            transect_duration = str(timedelta(seconds=self.transect_state["transect_duration"]))

            ens_time = str(ens.EnsembleData.datetime().strftime("%H:%M:%S"))

        if ens.IsAncillaryData:
            heading = round(ens.AncillaryData.Heading, 1)
            pitch = round(ens.AncillaryData.Pitch, 1)
            roll = round(ens.AncillaryData.Roll, 1)
            water_temp = round(ens.AncillaryData.WaterTemp, 1)

        if ens.IsSystemSetup:
            voltage = round(ens.SystemSetup.Voltage, 1)

        # Pass the ASCII serial data to the websocket
        self.socketio.emit('adcp_ens',
                           {
                               'adcp_ens_num': adcp_ens_num,
                               'ens_time': ens_time,
                               'transect_duration': transect_duration,
                               'voltage': voltage,
                               'heading': heading,
                               'pitch': pitch,
                               'roll': roll,
                               'water_temp': water_temp,
                           },
                           namespace='/rti')

        # Update the plot manager
        self.plot_mgr.add_ens(ens)

        # Record the ensembles
        self.record_ens(ens)

    def serial_thread_worker(self):
        """
        Thread worker to handle reading the serial port.
        :param mgr: This Object to get access to the variables.
        :return:
        """
        while self.serial_thread_alive:
            try:
                if self.serial_port.raw_serial.in_waiting:
                    try:
                        # Read the data from the serial port
                        self.serial_raw_bytes = self.serial_port.read(self.serial_port.raw_serial.in_waiting)

                        # Record the data
                        self.record_raw_data(self.serial_raw_bytes)

                        # Convert to ASCII
                        # Ignore any non-ASCII characters
                        raw_serial_ascii = self.serial_raw_bytes.decode('ascii', 'ignore')

                        # Replace ACK and NAK
                        raw_serial_ascii = raw_serial_ascii.replace("\6", "[ACK]")
                        #raw_serial_ascii = raw_serial_ascii.replace("\15", "[NAK]")

                        # Convert the data to ASCII
                        self.app_state["serial_raw_ascii"] += raw_serial_ascii

                        # Pass the ASCII serial data to the websocket
                        self.socketio.emit('serial_comm',
                                           {
                                               'data': self.app_state["serial_raw_ascii"]
                                           },
                                           namespace='/rti')

                        # Maintain a fixed buffer size
                        ascii_buff_size = len(self.app_state["serial_raw_ascii"])
                        if ascii_buff_size > 0:
                            if ascii_buff_size > self.app_state["max_ascii_buff"]:
                                # Remove the n number of characters to keep it within the buffer size
                                remove_buff_size = ascii_buff_size - self.app_state["max_ascii_buff"]
                                self.app_state["serial_raw_ascii"] = self.app_state["serial_raw_ascii"][remove_buff_size:]

                        # Pass data to codec to decode ADCP data
                        self.adcp_codec.add(self.serial_raw_bytes)

                    except Exception as ex:
                        # Do nothing
                        # This is to prevent from seeing binary data on screen
                        logging.info("Error Reading serial data" + str(ex))

                # Put a small sleep to allow more data to go into the buffer
                time.sleep(0.01)

            except serial.SerialException as se:
                logging.error("Error using the serial port.\n" + str(se))
                self.disconnect_serial()
            except Exception as ex:
                logging.error("Error processing the data.\n" + str(ex))
                self.disconnect_serial()

    def record_raw_data(self, serial_bytes):
        """
        Write the raw data from the serial port to
        a binary file.  This will write any data.
        :param serial_bytes: Serial bytes array
        """
        if self.is_record_raw_data:
            # Ensure the file is created
            self.create_river_project()

            # If the file is created, write the data
            if self.raw_file:
                self.raw_file.write(serial_bytes)

    def record_ens(self, ens: Ensemble):
        """
        Record the ensemble to the db file.
        Record the raw data to a raw binary file.
        :param ens: Ensemble data.
        """
        # Create the project db file if it does not exist
        self.create_river_project()

        # Write the ensemble to the db file
        if self.db_file:
            # Set the latest index of the ensemble in the db file
            # Set the burst number to the transect number
            # Set the is_batch_write to false.  We are not writing in bulk
            self.curr_ens_index = self.db_file.add_ensemble(ens, burst_num=self.transect_index, is_batch_write=False)
