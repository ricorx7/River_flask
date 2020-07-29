from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired
import rti_python.Datalogger.DataloggerHardware as datalogger


class SerialPortForm(FlaskForm):
    comm_port = SelectField('COMM Port', choices=datalogger.get_serial_ports_tuple())
    baud_rate = SelectField('Baud Rate', choices=datalogger.get_baud_rates_tuple())
    scan = SubmitField('SCAN')
    connect = SubmitField('CONNECT')
    disconnect = SubmitField('DISCONNECT')


class SerialPortSendCmd(FlaskForm):
    cmd = StringField("Command")
    send_cmd = SubmitField("SEND")
