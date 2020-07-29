from typing import List, Dict
import json


class DataloggrGui:

    def __init__(self):
        self.gui = {}
        self.gui["port_list"] = []
        self.gui["baud_list"] = []
        self.gui["btn_scan_disabled"] = False
        self.gui["btn_connect_disabled"] = False
        self.gui["btn_disconnect_disabled"] = True
        self.gui["btn_download_disabled"] = True
        self.gui["serial_connect_status"] = "Disconnected"
        self.gui["folder_path"] = ""
        self.gui["select_baud"] = 115200
        self.gui["debug"] = ""
        self.gui["log"] = ""
        self.gui["dl_status"] = {}

    def get_json(self):
        """
        Convert the object to JSON.
        :return: JSON of the object.
        """
        return json.dumps(self.gui)

    def get_gui(self):
        """
        Get the GUI status.
        :return: GUI status.
        """
        return self.gui

    def set_port_list(self, port_list: List[str]):
        """
        Set the COMM port list.
        :param port_list: Comm port list.
        :return:
        """
        self.gui["port_list"] = port_list

    def set_baud_list(self, baud_list: List[int]):
        """
        Set the baud rate list.
        :param baud_list: Baud Rate list.
        :return:
        """
        self.gui["baud_list"] = baud_list

    def set_dl_status(self, dl_status: Dict):
        """
        Set the DataLoggR Status.
        :param dl_status: DataLoggr Status dictionary.
        :return:
        """
        self.gui["dl_status"] = dl_status

    def set_debug(self, debug_msg: str):
        """
        Update the debug message.
        :param debug_msg: Debug Message.
        :return:
        """
        self.gui["debug"] += debug_msg

    def set_log(self, log_msg: str):
        """
        Update the log message.
        :param log_msg: Log message.
        :return:
        """
        self.gui["log_msg"] += log_msg

    def set_serial_connect(self):
        """
        Set the connected status.
        This will enable and disable the buttons.
        :return:
        """
        self.gui["serial_connect_status"] = "Connected"
        self.gui["btn_scan_disabled"] = False
        self.gui["btn_connect_disabled"] = True
        self.gui["btn_disconnect_disabled"] = False
        self.gui["btn_download_disabled"] = False

    def set_serial_disconnect(self):
        """
        Set the disconnected status.
        This will enable and disable the buttons.
        :return:
        """
        self.gui["serial_connect_status"] = "Disconnected"
        self.gui["btn_scan_disabled"] = False
        self.gui["btn_connect_disabled"] = False
        self.gui["btn_disconnect_disabled"] = True
        self.gui["btn_download_disabled"] = True

