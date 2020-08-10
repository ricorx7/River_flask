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

# Flask App Init
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
ui = FlaskUI(app)
ui.height = 900
ui.width = 1200

# Websockets to have seamless communication to the webpage
socketio = SocketIO(app, async_mode=async_mode)

# Create a plotly dashboard using flask
#plotly_dash = Dashboard()
#app = plotly_dash.create_dashboard(app)

thread = None
thread_lock = Lock()

# Socket IO 
count = 0

# Current serial port
selected_serial_port = None
selected_baud_rate = None

# Maintain the state of the application
app_mgr = AppManager(socketio=socketio)


@app.route("/")
def main_page():
    # Use Download page as main
    #return download_page(None, None)
    #return redirect('/serial')
    #return serial_page(None, None)
    bar = app_mgr.get_plot()
    #return render_template('serial.j2', form=form)
    return render_template('main.html', plot=bar, state=app_mgr.app_state)


@app.route('/plot')
def display_plot():
    bar = app_mgr.get_plot()
    return render_template('plot_full.j2', plot=bar, state=app_mgr.app_state)


@app.route('/live_plot')
def display_live_plot():
    return render_template('live_plot.html', state=app_mgr.app_state)


@app.route('/term')
def display_terminal():
    return render_template('terminal.html', state=app_mgr.app_state)


@app.route('/serial_scan', methods=['POST'])
def serial_scan():
    logging.debug("Scan Serial Ports")

    socketio.emit('status_report',
                {'data': 'Scan Serial Ports', 'count': count},
                namespace='/test')

    return jsonify({})


@app.route('/browse_folder', methods=['POST'])
def browse_folder():
    logging.debug("Browse for Folder")

    return jsonify({})


@app.route('/serial_connect', methods=['POST'])
def serial_connect():
    logging.debug("CALL Serial Connect")
    logging.debug(request.form)

    # Verify command is given
    if "selected_port" and "selected_baud" in request.form:
        # Get the command
        selected_port = request.form["selected_port"]
        selected_baud = request.form["selected_baud"]
        logging.debug(selected_port)
        logging.debug(selected_baud)

        # Send the command to the serial port
        result = app_mgr.connect_serial(selected_port, int(selected_baud))

        # Return good status
        return jsonify(result)

    # Return error, missing command
    return jsonify({'error': "Missing parameters to connect"})


@app.route('/serial_disconnect', methods=['POST'])
def serial_disconnect():
    logging.debug("CALL Serial Disconnect")
    logging.debug(request.form)

    # Disconnect to the serial port
    result = app_mgr.disconnect_serial()

    # Return the state of the app
    return jsonify(result)


@app.route('/serial_send_cmd', methods=['POST'])
def send_serial_cmd():
    logging.debug("CALL Send Command")

    logging.debug(request.form)

    # Verify command is given
    if "cmd" in request.form:
        # Get the command
        cmd = request.form["cmd"]
        logging.debug(cmd)

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
    break_result = app_mgr.send_serial_break()

    return jsonify(break_result)


@app.route('/playback_files', methods=['POST'])
def playback_files():
    logging.debug("CALL Playback File")

    logging.debug(request.form)

    # Send the command to the serial port
    playback_files_selected = app_mgr.playback_files()

    # Return good status
    return jsonify({'files': playback_files_selected})


@socketio.on('connect', namespace='/rti')
def ws_connect():
    """
    Call this function when the websocket is connected.
    This will create a background worker that will
    pass data to the websocket.  The thread is used
    to maintain the status of the backend.

    Let the AppMgr handle maintaining the state of the websocket data.
    :return:
    """
    global thread

    with thread_lock:
        # Create a thread to run a background worker
        if thread is None:
            @copy_current_request_context
            def ctx_bridge():
                # Background worker
                app_mgr.socketio_background_thread()

            # Start the thread in the background
            thread = socketio.start_background_task(ctx_bridge)
    logging.debug("Websocket connected")


@socketio.on('disconnect', namespace='/rti')
def ws_disconnect():
    """
    Call this this function when the websocket is
    disconnected.  This will cleanup everything.
    :return:
    """
    logging.debug('Client disconnected Websocket', request.sid)


# Run the flask APP
ui.run()


if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0')

