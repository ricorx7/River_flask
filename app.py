from flask import Flask, render_template, request, copy_current_request_context, jsonify, flash
from flaskwebgui import FlaskUI
from threading import Lock
from flask_socketio import SocketIO, emit
from forms import SerialPortForm
import json
import rti_python.Datalogger.DataloggerHardware as data_logger
from vm import DataloggrGui
import plotly
import plotly.graph_objs as go
from app_manager import AppManager
import logging


import pandas as pd
import numpy as np
import json

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
ui = FlaskUI(app)
ui.height = 800
ui.width = 1200
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# Datalogger hardware
logger_hardware = data_logger.DataLoggerHardware()

# GUI object to keep track of state
gui = DataloggrGui.DataloggrGui()

# Socket IO 
count = 0

# Current serial port
selected_serial_port = None
selected_baud_rate = None

# Maintain the state of the application
app_mgr = AppManager(socketio=socketio)

def background_thread():
    """
    Background worker.  This will maintain the status of the
    backend and the GUI.
    Send the status of the Datalogger download process.
    This will continously check the status of the process.
    """
    count = 0
    while True:
        # Wait time
        socketio.sleep(5)
        count += 1

        # Send a debug status to websocket
        socketio.emit('status_report',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

        # Get the Datalogger status
        dl_status = logger_hardware.get_status()

        # Set the Datalogger status to the gui
        gui.set_dl_status(dl_status)

        # Get the gui status as json
        json_gui = gui.get_json()

        # Pass the status to the websocket
        socketio.emit('gui_status', json_gui, namespace='/test')


@app.route("/")
def main_page():
    # Use Download page as main
    #return download_page(None, None)
    #return redirect('/serial')
    #return serial_page(None, None)
    form = SerialPortForm()
    bar = app_mgr.get_plot()
    #return render_template('serial.j2', form=form)
    return render_template('main.j2', form=form, plot=bar)


@app.route('/plot')
def display_plot():
    bar = app_mgr.get_plot()
    return render_template('plot_full.j2', plot=bar)


@app.route('/term')
def display_terminal():
    return render_template('terminal.j2',
                           bauds=app_mgr.app_state['baud_list'],
                           ports=app_mgr.app_state['serial_port_list'],
                           is_serial_connected=app_mgr.app_state['is_serial_connected'],
                           selected_baud=app_mgr.app_state['selected_baud'],
                           selected_serial_port=app_mgr.app_state['selected_serial_port'])


@app.route('/serial_scan', methods=['POST'])
def serial_scan():
    print("Scan Serial Ports")

    socketio.emit('status_report',
                {'data': 'Scan Serial Ports', 'count': count},
                namespace='/test')

    # Set the debug messages
    gui.set_debug("Scan Serial Ports")

    # Set the port list
    gui.set_port_list(data_logger.get_serial_ports())

    return jsonify(data=gui.get_gui())


@app.route('/browse_folder', methods=['POST'])
def browse_folder():
    print("Browse for Folder")

    # Browser for a folder using TKinker
    folder_path = logger_hardware.browse_folder()

    # Get the status
    dl_status = logger_hardware.get_status()

    # Set the status to the gui
    gui.set_dl_status(dl_status)

    # Convert the status to JSON and pass to websocket
    json_dl_status = json.dumps(dl_status)
    socketio.emit('dl_status',
                    json_dl_status,
                    namespace='/test')

    return jsonify(data={'folder_path': folder_path})


@app.route('/serial_connect', methods=['POST'])
def serial_connect():
    print("CALL Serial Connect")
    print(request.form)

    # Verify command is given
    if "selected_port" and "selected_baud" in request.form:
        # Get the command
        selected_port = request.form["selected_port"]
        selected_baud = request.form["selected_baud"]
        print(selected_port)
        print(selected_baud)

        # Send the command to the serial port
        result = app_mgr.connect_serial(selected_port, int(selected_baud))

        # Return good status
        return jsonify(result)

    # Return error, missing command
    return jsonify({'error': "Missing parameters to connect"})


@app.route('/serial_disconnect', methods=['POST'])
def serial_disconnect():
    print("CALL Serial Disconnect")
    print(request.form)

    # Disconnect to the serial port
    result = app_mgr.disconnect_serial()

    # Return the state of the app
    return jsonify(result)


@app.route('/download', methods=['POST'])
def download():
    print("CALL Download")

    # Start the download process
    logger_hardware.download()

    return jsonify(data={
        'Status': 'Downloading'
    })

    # If not valid, return errors
    return jsonify(data=form.errors)


@app.route('/serial_send_cmd', methods=['POST'])
def send_serial_cmd():
    print("CALL Send Command")

    print(request.form)

    # Verify command is given
    if "cmd" in request.form:
        # Get the command
        cmd = request.form["cmd"]
        print(cmd)

        # Send the command to the serial port
        app_mgr.send_serial_cmd(cmd)

        # Return good status
        return jsonify({'status': 'Send Command ' + cmd})

    # Return error, missing command
    return jsonify({'error': "Missing Command"})


@app.route('/serial_break', methods=['POST'])
def serial_break():
    logging.debug("CALL Serial BREAK")

    # Start the download process
    app_mgr.send_serial_break()

    return jsonify(data={
        'status': 'Serial BREAK'
    })

    # If not valid, return errors
    return jsonify(data=form.errors)

"""
@app.route("/serial", methods=['GET', 'POST'])
#def serial_page(selected_port: str = None, selected_baud: str = None):
def serial_page():
    # Global values to keep track of selected items
    global selected_serial_port
    global selected_baud_rate

    # Create the form
    serial_port_form = SerialPortForm()

    # Set the selected values if previously set
    serial_port_form.comm_port.choices = data_logger.get_serial_ports_tuple()
    if selected_serial_port:
        serial_port_form.comm_port.default = selected_serial_port
    if selected_baud_rate:
        serial_port_form.baud_rate.default = selected_baud_rate

    # Check for POST
    if serial_port_form.validate_on_submit():
        flash('COMM Port {}, Baud Rate={}'.format(serial_port_form.comm_port.data, serial_port_form.baud_rate.data))
        selected_serial_port = serial_port_form.comm_port.data
        selected_baud_rate = serial_port_form.baud_rate.data
        if serial_port_form.scan.data:
            flash("SCAN New Ports")
        if serial_port_form.connect.data:
            flash("Connect ADCP Serial Port")
        if serial_port_form.disconnect.data:
            flash("Disconnect ADCP Serial Port")
        print("Scan Value : {value}".format(value=serial_port_form.scan.data))
        print("Connect Value : {value}".format(value=serial_port_form.connect.data))
        print("Disconnect Value : {value}".format(value=serial_port_form.disconnect.data))
        return redirect('/serial')
        #return serial_page(serial_port_form.comm_port.data, serial_port_form.baud_rate.data)

    # Check for errors
    if serial_port_form.errors:
        print("***ERROR with SerialPort Page***")
        for error in serial_port_form.errors:
            print(error)

    # GET
    return render_template('serialport.j2', title='Serial Port', form=serial_port_form)


@app.route("/download")
def download_page(selected_comm: str, selected_baud: str):
    comm_port_list = logger_hardware.get_serial_ports()
    baud_list = logger_hardware.get_baud_rates()
    if selected_comm:
        print("Selected Port: " + selected_comm)
    if selected_baud:
        print("Selected Port: " + selected_baud)

    # Remove the duplicate selected comm port
    if selected_comm in comm_port_list:
        comm_port_list.remove(selected_comm)
    if selected_baud in baud_list:
        baud_list.remove(selected_baud)

    return render_template("download.j2", comm_ports=comm_port_list, bauds=baud_list, selected_comm_port=selected_comm, selected_baud=selected_baud, async_mode=socketio.async_mode)


@app.route("/scan_serial", methods=['POST'])
def scan_serial():
    selected_comm_port = request.form.get('comm_port_selected')
    selected_baud = request.form.get('baud_selected')
    print(selected_comm_port)
    print(selected_baud)
    return download_page(selected_comm_port, selected_baud)

@socketio.on('connect_serial', namespace='/test')
def serial_connect(message):
    print("CONNECT SERIAL PORT")
    emit('my_response', {'data': message['data']})

@socketio.on('disconnect_serial', namespace='/test')
def serial_disconnect(message):
    print("DISCONNECT SERIAL PORT")
    emit('my_response', {'data': message['data']})


@socketio.on('my event', namespace='/test')
def test_message(message):
    emit('my_response', {'data': message['data']})

@socketio.on('my broadcast event', namespace='/test')
def test_broad_message(message):
    emit('my_response', {'data': message['data']}, broadcast=True)
"""


@socketio.on('connect', namespace='/test')
def ws_connect():
    """
    Call this function when the websocket is connected.
    This will create a background worker that will
    pass data to the websocket.  The thread is used
    to maintain the status of the backend.
    :return:
    """
    global thread

    # Update the GUI status
    # Set the port list and baud rate list
    gui.set_port_list(data_logger.get_serial_ports())
    gui.set_baud_list(data_logger.get_baud_rates())

    with thread_lock:
        # Create a thread to run a background worker
        if thread is None:
            @copy_current_request_context
            def ctx_bridge():
                # Background worker
                #background_thread()
                app_mgr.socketio_background_thread()

            # Start the thread in the background
            thread = socketio.start_background_task(ctx_bridge)
    emit('status_report', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def ws_disconnect():
    """
    Call this this function when the websocket is
    disconnected.  This will cleanup everything.
    :return:
    """
    print('Client disconnected', request.sid)


# Run the flask APP
ui.run()


if __name__ == '__main__':
    socketio.run(app, debug=False)

