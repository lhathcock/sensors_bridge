import json
import csv
import re
import signal
import threading
import time
from os import remove, path, SEEK_END, unlink, kill, mkdir
import serial
import socket
import glob
import traceback
import serial.tools.list_ports
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
import multiprocessing
import serial.tools.list_ports
from multiprocessing import Process

from os.path import expanduser

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QApplication,
    QFileDialog, QTableWidgetItem,
    QComboBox, QDialogButtonBox, QHeaderView, QLineEdit, QWidget, QHBoxLayout,
    QToolButton, QTableWidget, QVBoxLayout, QSizePolicy, QSpacerItem, QPlainTextEdit, QMessageBox)

from ui.sensorsbridge import Ui_SensorsBridge

SESSION = None
VERIFY_SECURE = True
ROOT_PATH = path.dirname(path.realpath(__file__))
SB_USER_PATH = path.join(expanduser('~'), '.SensorsBridge')
if not path.isdir(SB_USER_PATH):
    mkdir(SB_USER_PATH)
SETTINGS_PATH = path.join(SB_USER_PATH, 'settings.txt')
DEFAULT_CONFIG = {
    "ecotriplet2": {
        "separator": "\t+",
        "baud_rate": 19200,
        "byte_size": 44
    },
    "co2procv": {
        "separator": ",",
        "baud_rate": 19200,
        "byte_size": 72,
        "extra_config": [b'\x1B', b'\x1B', b'1', b'1']
    },
    "dissolvedoxygen": {
        "separator": ",",
        "baud_rate": 9600,
        "byte_size": 72,
        "extra_config": [b'setbaud=9600\r\n', b'setbaud=9600\r\n', b'SetFormat=1\r\n', b'SetAvg=2\r\n', b'Start\r\n']
    },
    "ecotriplet1": {
        "separator": "\t+",
        "baud_rate": 19200,
        "byte_size": 48
    },
    "ecotriplet3": {
        "separator": "\t+",
        "baud_rate": 19200,
        "byte_size": 45
    }
}

STOP = False


class Bridge():

    def __init__(self, config):
        """
        Reads data from connected sensors and sends data to the receiving server.
        :param config: The configuration containing the sensors and other settings.
        :param type: Object
        """
        self.config = config
        self.sensors_config = config['sensors_config']
        self.basic_options = config['basic_options']
        self.server_options = config['server_options']
        self.udp_sensors = {s['code']: s for s in self.sensors_config if s['type'] == 'UDP'}
        self.file_extensions = ('.csv', '.txt')

    def connect_to_server(self, sensor, show_no_internet_error=True):
        """
        Connects sensors bridge to the server.
        :param com: The name of the port
        :type com: String
        :param show_no_internet_error: A boolean to show connection error or not
        :type show_no_internet_error: Boolean
        :return: The status of the connection
        :type: Boolean
        """
        global SESSION
        params = urlencode(
            {'username': self.server_options['username'],
             'password': self.server_options['password'], 'f': 'json'})
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        SESSION = requests.Session()

        try:
            response = SESSION.post(
                self.server_options['server_login'],
                data=params, headers=headers, verify=VERIFY_SECURE
            )
            if response.status_code != 200:
                if not show_no_internet_error:
                    msg = 'Error to login {}. {} ({}) data saved ' \
                          'locally until internet is restored'.format(
                        response.status_code, sensor['label'], sensor['code'])

                    msg_with_time = self.create_log(msg, sensor['name'])
                    print(msg_with_time)
                SESSION = None
                return False
            return True
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
            # print(msg_with_time)
            return False

    def create_log(self, message, sensor_name='', show_message=True):
        """
        Creates user log and saves it to file is output it to stdout.
        :param message: The log message.
        :type message: String
        :param sensor_name: The name of the sensor for which the log is outputted
        :type sensor_name: String
        :param show_message: A boolean showing or hiding log on stdout.
        :type show_message: Boolean
        :return:
        """
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        dt_name_str = now.strftime("%d_%m_%Y")
        file_name = 'log_{}.txt'.format(dt_name_str)
        file_path = path.join(self.basic_options['data_path'], file_name)
        if sensor_name != '':
            msg = '{}$ {} {}\n'.format(sensor_name, dt_string, message)
        else:
            msg = '{} {}\n'.format(dt_string, message)

        with open(file_path, 'a') as data_file:
            data_file.write(msg)
        if show_message:
            print(msg.strip())
        return msg.strip()

    def save_to_file(self, sensor, data):
        """
        Saves data to a file.
        :param sensor: A sensor dictionary containing all the details of a sensor.
        :type sensor: Object
        :param data: The data to be written to a file.
        :type data: String
        :return:
        """
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y")
        file_name = '{}_{}.csv'.format(dt_string, sensor['name'])
        file_path = path.join(self.basic_options['data_path'], file_name)
        try:
            if not path.isfile(file_path):
                with open(file_path, 'w', newline='') as csvfile:
                    wr = csv.writer(csvfile, delimiter=',', lineterminator='\n')
                    wr.writerow(data.keys())

            with open(file_path, 'a') as data_file:
                wr = csv.writer(data_file, delimiter=',', lineterminator='\n')
                wr.writerow(data.values())
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])

    def save_to_temp_file(self, sensor, data):
        """
        Save data to temporary files till internet is reconnected.
        :param sensor: The sensor object
        :type sensor: Object
        :param data: The key/value data
        :type data: Dictionary
        :return:
        """
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y_temp")
        file_name = '{}_{}.csv'.format(dt_string, sensor['name'])
        file_path = path.join(self.basic_options['data_path'], file_name)

        if not path.isfile(file_path):
            with open(file_path, 'w', newline='') as csvfile:
                wr = csv.writer(csvfile, delimiter=',', lineterminator='\n')
                wr.writerow(data.keys())

        with open(file_path, 'a') as data_file:
            wr = csv.writer(data_file, delimiter=',', lineterminator='\n')
            wr.writerow(data.values())

    def send_to_server(self, sensor, data):
        """
        Send data to the server.
        :param sensor: The sensor object
        :type sensor: Object
        :param data: The key/value data
        :type data: Dictionary
        :return: True if sent or False if not
        :rtype: Boolean
        """
        global SESSION
        if SESSION is None:
            return False
        url = '{}{}'.format(self.server_options['server'], sensor['name'])

        try:
            response = SESSION.post(url, data=data, verify=VERIFY_SECURE)
            if response.status_code != 200:
                msg = 'Error: {} Failed to send {} at port {}. ' \
                      'Saving it to local file.'.format(
                    response.status_code, sensor['name'], sensor['code']
                )

                msg_with_time = self.create_log(msg, sensor['name'])
                print(msg_with_time)
                SESSION = None
                return False
            else:
                # if com == 'GPRMC':
                # print ('Sent {} {}'.format(sensor['name'], data))
                return True
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
            print(msg_with_time)
            return False
        # print (response.status_code)

    def send_temp_files_by_com(self, sensor):
        """
        Send temporary data to the server by port.
        :param sensor: The sensor object
        :type sensor: Object
        :return:
        """
        global SESSION
        if SESSION is None:  # dont send if the user hasn't logged in
            return
        name = sensor['name']
        temp_files = glob.glob(self.basic_options['data_path'] + '/*temp*' + name + '*')
        header = sensor['header'].split(',')
        header = [h for h in header if h not in sensor['exclude']]
        header.append('datetime')
        # print (temp_files)
        for temp_file in temp_files:  # get com port from temp file
            if not path.exists(temp_file):
                continue
            msg = 'Sending backup {}'.format(temp_file)
            msg_with_time = self.create_log(msg, sensor['name'])
            print(msg_with_time)
            results = []
            with open(temp_file, "r") as f:
                lines = f.readlines()

                for i, line in enumerate(lines):
                    if i == 0:
                        continue
                    data = dict(zip(header,
                                    line.strip().split(',')))
                    # print (data)
                    result = self.send_to_server(sensor, data)
                    results.append(result)
            msg2 = 'Completed sending backup {}'.format(temp_file)
            msg_with_time = self.create_log(msg2, sensor['name'])
            # print(msg_with_time)
            # print (results)
            if False not in results:
                try:
                    remove(temp_file)  # delete file after all data is sent
                except:  # error may happen when deleting file being read so pass it
                    pass
        header.remove('datetime')

    def send_temp_files(self):
        """
        Send temporary data to the server.
        :return:
        """
        global SESSION
        if SESSION is None:  # dont send if the user hasn't logged in
            return
        temp_files = glob.glob(self.basic_options['data_path'] + '/*temp*')
        # print (temp_files)
        for temp_file in temp_files:  # get com port from temp file

            if not path.exists(temp_file):
                continue
            sensors = [l for l in self.sensors_config
                       if l['name'] in temp_file]

            if len(sensors) > 0:
                sensor = sensors[0]
            else:
                continue  # because it is not a temp file
            header = sensor['header']
            header.append('datetime')
            msg = 'Sending backup {}'.format(temp_file)
            msg_with_time = self.create_log(msg, sensor['name'])
            # print(msg_with_time)
            with open(temp_file, "r") as f:
                lines = f.readlines()

                for line in lines:
                    data = dict(zip(header, line.strip().split(',')))
                    self.send_to_server(sensor, data)
            msg2 = 'Completed sending backup {}'.format(temp_file)
            msg_with_time = self.create_log(msg2, sensor['name'])
            print(msg_with_time)
            try:
                remove(temp_file)  # delete file after all data is sent
            except:  # error may happen when deleting file being read so pass it
                pass
            header.remove('datetime')

    def delete_old_files(self):
        """
        Delete old files in the data folder.
        :return:
        """
        current_time = time.time()
        txt_data = glob.glob('{}\\*'.format(self.basic_options['data_path']))

        for f in txt_data:
            name = None
            file_name = path.basename(f)
            if not file_name.endswith(self.file_extensions):# exclude other files
                continue
            if 'log' not in file_name:

                file_sensors = [l for l in self.sensors_config
                                if l['name'] in file_name]

                if len(file_sensors) > 0:
                    name = file_name

            elif 'log' in file_name:
                name = 'log'
            else:
                continue
            if name is None:
                continue

            creation_time = path.getctime(f)
            if (current_time - creation_time) / (24 * 3600) >= \
                    self.basic_options['file_keep_limit']:

                unlink(f)
                msg = '{} removed'.format(f)
                msg_with_time = self.create_log(msg, name)
                print(msg_with_time)

    def filter_data(self, data, sensor):
        """
        Exclude data by key/header.
        :param sensor: The sensor object
        :type sensor: Object
        :param data: The key/value data
        :type data: Dictionary
        :return:
        """
        new_dict = {}
        for key, value in data.items():
            if key not in sensor['exclude']:
                new_dict[key] = value
        return new_dict

    def read_udp(self):
        """
        Reads UDP stream and send it to the server and write it a file.
        :return:
        """
        show_no_internet_error = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

        sock.bind(('', self.basic_options['udp_port']))

        while True:
            if STOP:
                break
            data_b, addr = sock.recvfrom(4096)
            utc_time = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S.%f")
            data_str = data_b.decode()
            # now = time.time()
            if '$' not in data_str:
                continue

            row = data_str.lstrip('$').split('*')[0].split(',')
            # print (row)
            # prev_sec = now - program_starts
            if len(row) > 0:
                if row[0] in self.udp_sensors.keys():
                    # if row[0] == com:
                    code = row[0]
                    sensor = self.udp_sensors[code]
                    header = sensor['header'].split(',')

                    if len(row[1:]) != len(header):
                        continue
                    # print("{0} {1}".format(now - program_starts, row[0]))
                    data = dict(zip(header, row[1:]))
                    data['datetime'] = utc_time
                    # print (data)
                    if row[0] == 'GPRMC':
                        self.process_location(data)
                    data = self.filter_data(data, self.udp_sensors[code])
                    # print (data)
                    self.manage_data(data, sensor, show_no_internet_error)

    def process_location(self, data):
        """
        Convert nmea lat lon to decimal degrees.
        :param data: The key/value data
        :type data: Dictionary
        :return:
        """
        # ddmm.mmmm lat
        # dddmm.mmmm lon
        # dd + mm.mmmm/60 for latitude
        # ddd + mm.mmmm/60 for longitude
        lat_hemi = 1
        lon_hemi = 1
        if data.get('latitude_direction') == 'S':
            lat_hemi = -1
        if data.get('longitude_direction') == 'W':
            lon_hemi = -1
        lat_string = data.get('latitude')
        try:
            lat_degs = int(lat_string[0:2])
            lat_mins = float(lat_string[2:])
            lat = (lat_degs + (lat_mins / 60)) * lat_hemi
            # Longitude
            lon_string = data.get('longitude')
            # print (lon_string)
            lon_degs = int(lon_string[0:3])
            lon_mins = float(lon_string[3:])
            lon = (lon_degs + (lon_mins / 60)) * lon_hemi
            data['latitude'] = str(lat)
            data['longitude'] = str(lon)
        except:
            msg_with_time = self.create_log(traceback.format_exc(), 'gpsposition')
            print(msg_with_time)
            data['latitude'] = 'null'
            data['longitude'] = 'null'

    def read_com(self, sensor):
        """
        Reads COM port stream and send it to the server and write it a file.
        :param sensor: The sensor object
        :type sensor: Object
        :return:
        """
        show_no_internet_error = True
        try:
            a_serial = serial.Serial(
                sensor['code'], DEFAULT_CONFIG[sensor['name']]['baud_rate'],
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE
            )

            if 'extra_config' in DEFAULT_CONFIG[sensor['name']].keys():
                for config in DEFAULT_CONFIG[sensor['name']]['extra_config']:
                    a_serial.write(config)

            header = sensor['header'].split(',')

            separator = DEFAULT_CONFIG[sensor['name']]['separator']
            while True:
                if STOP:
                    break
                utc_time = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S.%f")
                c = a_serial.readline()

                row = re.split(separator, c.decode().strip())
                # if sensor['name'] == 'co2procv':
                #     print(row)
                if len(row) != len(header):
                    #TODO check the length of row when pco2 is not connected and try to connect pyserial here.
                    # print (len(row))
                    if DEFAULT_CONFIG[sensor['name']] == 'co2procv' and row == 'Stopping user interface':
                        a_serial = serial.Serial(
                            sensor['code'], DEFAULT_CONFIG[sensor['name']]['baud_rate'],
                            parity=serial.PARITY_NONE,
                            bytesize=serial.EIGHTBITS,
                            stopbits=serial.STOPBITS_ONE
                        )
                        for config in DEFAULT_CONFIG[sensor['name']]['extra_config']:
                            a_serial.write(config)
                        print ('connected to ', sensor['name'])

                    msg_with_time = self.create_log(row, sensor['name'])
                    # print(msg_with_time)
                    continue
                data = dict(zip(header, row))

                data['datetime'] = utc_time

                self.manage_data(data, sensor, show_no_internet_error)
                # print (data)
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
            # print('Failed data: ', sensor['code'], data)
            # print(msg_with_time)

    def manage_data(self, data, sensor, show_no_internet_error):
        """
        Sends to the server and saves to a local file.
        If there is no internet, it saves it to a temporary file.
        :param sensor: The sensor object
        :type sensor: Object
        :param data: The key/value data
        :type data: Dictionary
        :param show_no_internet_error: True if error should be shown or False if not.
        :type show_no_internet_error: Boolean
        :return:
        """
        # print (SESSION,port_name,  data )
        if SESSION is not None:
            # if port_name == 'GPRMC':
            # print ('sending 22', port_name, data)
            if self.config["server_options"]["send_data"]:
                self.send_to_server(sensor, data)
        else:
            # if port_name == 'GPRMC':
            #     print ("SESSION ", SESSION, port_name)
            # print(data)
            if self.config["server_options"]["send_data"]:
                self.save_to_temp_file(sensor, data)
                show_no_internet_error = self.connect_to_server(sensor, show_no_internet_error)
                # print (SESSION)
                if show_no_internet_error:  # there is connection
                    # send data that was not sent due to internet problem
                    if SESSION is not None:
                        self.send_temp_files_by_com(sensor)
        self.save_to_file(sensor, data)


class SensorsBridge(QDialog, Ui_SensorsBridge):
    log = pyqtSignal(str)
    configFolder = pyqtSignal(str)

    def __init__(self):
        """
        The user interface dialog that loads settings and
        gives the users options to configure and run the data capture.
        """
        QDialog.__init__(self, None)
        self.setupUi(self)
        self._data_folder = None
        self.data_folder_btn.clicked.connect(
            lambda: self.file_dialog(self.data_folder_lne)
        )
        self.config_folder_btn.clicked.connect(
            lambda: self.file_dialog(self.config_folder_le)
        )
        self.configFolder.connect(self.load_config)

        self._input_gpx_folder_path = None
        self.interfaces = ['COM port', 'UDP']
        self.com_ports = []
        for i in serial.tools.list_ports.comports():
            self.com_ports.append(str(i).split(" ")[0])

        self.basic_options = None
        self.server_options = None
        self.sensors_config = None
        self.header_indexes = {'3': 'header', '4': 'exclude'}
        self.config_path = ''
        self.init_gui()

    def load_config(self):
        """
        Loads the configuration file.
        :return:
        """
        self.config_folder = self.config_folder_le.text()
        if path.isdir(self.config_folder):
            config_path = path.join(self.config_folder, 'config.json')
            if path.isfile(config_path):
                self.config_path = config_path.replace('\\', '/')
                with open(self.config_path) as f:
                    self.config = json.load(f)

                self.populate_gui()
                with open(SETTINGS_PATH, 'w') as s:
                    s.write(self.config_path)

    def init_gui(self):
        """
        Initializes the widgets with signals
        :return:
        """
        self.log_boxes = {}

        self.load_default_config()

        self.setWindowFlags(
            self.windowFlags() |
            Qt.WindowSystemMenuHint |
            Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint
        )
        icon_path = self.resource_path('favicon.ico')
        self.setWindowIcon(QIcon(icon_path))
        pw = self.password_le
        pw.setEchoMode(QLineEdit.Password)
        pw.show()
        self.server_gb.toggled.connect(self.set_connect_to_server)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Run")
        self.buttonBox.button(QDialogButtonBox.Discard).setText("Stop")
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("Exit")

        self.sensors_config_tw.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.sensors_config_tw.horizontalHeader().setVisible(True)
        self.sensors_config_tw.cellChanged.connect(self.sensor_label_changed)

        self.add_btn.clicked.connect(self.add_sensor)
        self.remove_btn.clicked.connect(self.remove_sensor)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_config)
        self.log.connect(self.insert_text_to_log_box)

    def load_default_config(self):
        """
        Load the default configuration if there is no configuration already set.
        :return:
        """
        if path.isfile(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r') as s:

                self.config_path = s.readline().strip()
                self.config_folder = path.dirname(self.config_path)
        else:
            self.config_path = path.join(ROOT_PATH, 'config.json')
            self.config_folder = ROOT_PATH
            with open(SETTINGS_PATH, 'w') as s:
                s.write(self.config_path)

        if path.isfile(self.config_path):

            self.config_folder_le.setText(self.config_folder.replace('\\', '/'))

            with open(self.config_path) as f:
                self.config = json.load(f)
            self.populate_gui()
        else:
            self.config_path = None

    def populate_gui(self):
        """
        Populate the GUI fields using the configuration.
        :return:
        """
        if 'basic_options' in self.config.keys():
            self.basic_options = self.config['basic_options']
            if path.isdir(self.basic_options['data_path']):
                self.data_folder_lne.setText(self.basic_options['data_path'])

            self.file_keep_limit_sb.setValue(self.basic_options['file_keep_limit'])

            self.udp_port_sb.setValue(self.basic_options['udp_port'])

        if 'server_options' in self.config.keys():
            self.server_options = self.config['server_options']
            self.server_le.setText(self.server_options['server'])
            self.server_login_le.setText(self.server_options['server_login'])
            self.username_le.setText(self.server_options['username'])
            self.password_le.setText(self.server_options['password'])
            self.server_gb.setChecked(self.server_options["send_data"])

        if 'sensors_config' in self.config.keys():
            self.sensors_config = self.config['sensors_config']
            self.load_sensor_config()
            self.create_log_tab()

        self.header_indexes = {'3': 'header', '4': 'exclude'}

    @staticmethod
    def resource_path(relative_path):
        """
         Get absolute path to resource, works for dev and for PyInstaller
        :param relative_path:
        :return:
        """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath(".")

        return path.join(base_path, relative_path)

    def set_connect_to_server(self, status):
        """
        Sets connection to the server setting using the server config groupbox checkbox.
        :param status:
        :return:
        """
        self.server_options["send_data"] = status

    def show_message(self, title, msg):
        """
        Show messages as a popup.
        :param title: The type of the message. "Error", "Information"
        :type title: String
        :param msg: The message to be displayed.
        :return:
        """
        msgBox = QMessageBox()
        if title == 'Error':
            icon = QMessageBox.Critical
        elif title == "Information":
            icon = QMessageBox.Information
        else:
            icon = QMessageBox.Information
        msgBox.setIcon(icon)
        msgBox.setText(msg)
        msgBox.setWindowTitle('Sensors Bridge {}'.format(title))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        icon_path = self.resource_path('favicon.ico')
        msgBox.setWindowIcon(QIcon(icon_path))
        msgBox.exec_()

    def interface_changed(self, value):
        """
        A slot emitted when the user changes the combobox of Type
        (communication interfaces type)
        :param value: The combobox value newly selected
        :type value: String
        :return:
        """
        if 'COM' in value:
            combo2 = QComboBox()
            for com in self.com_ports:
                combo2.addItem(com)

            self.sensors_config_tw.setCellWidget(
                self.sensors_config_tw.currentRow(), 2, combo2)
        else:
            self.sensors_config_tw.removeCellWidget(
                self.sensors_config_tw.currentRow(), 2)

            item2 = QTableWidgetItem('')
            self.sensors_config_tw.setItem(
                self.sensors_config_tw.currentRow(), 2, item2)

    def add_sensor(self):
        """
        Adds sensor rows when the user clicks on the add button in the
        sensors configuration. The new row is added next to a selected row.
        :return:
        """
        idx = self.sensors_config_tw.currentRow() + 1
        self.sensors_config_tw.insertRow(idx)

        combo = QComboBox()
        for t in self.interfaces:
            combo.addItem(t)
            combo.setCurrentIndex(0)
        self.sensors_config_tw.setCellWidget(idx, 1, combo)

        combo2 = QComboBox()
        for com in self.com_ports:
            combo2.addItem(com)

        self.sensors_config_tw.setCellWidget(idx, 2, combo2)

        combo.currentTextChanged.connect(self.interface_changed)

        item3 = QTableWidgetItem('')
        btn_widget, btn = self.create_table_edit_button()
        btn.setObjectName('{}:{},{}'.format(3, idx, ''))
        btn.clicked.connect(self.show_list)
        self.sensors_config_tw.setCellWidget(idx, 3, btn_widget)
        self.sensors_config_tw.setItem(idx, 3, item3)

        item4 = QTableWidgetItem('')
        btn_widget2, btn2 = self.create_table_edit_button()
        btn2.setObjectName('{}:{},{}'.format(4, idx, ''))
        btn2.clicked.connect(self.show_list)
        self.sensors_config_tw.setItem(idx, 4, item4)
        self.sensors_config_tw.setCellWidget(idx, 4, btn_widget2)

    def remove_sensor(self):
        """
        Removes a selected sensors row when the user clicks on a remove button.
        :return:
        """
        self.sensors_config_tw.removeRow(
            self.sensors_config_tw.currentRow())

    def add_header(self):
        """
        Adds a header or exclude field of a sensor in the header or exclude popup.
        :return:
        """
        dialog = self.sender().parentWidget()
        table = [c for c in dialog.children() if isinstance(c, QTableWidget)]
        if len(table) < 1:
            return
        table = table[0]

        table.insertRow(table.currentRow() + 1)

    def remove_header(self):
        """
        Removes a header or exclude field of a sensor in the header or exclude popup.
        :return:
        """
        dialog = self.sender().parentWidget()
        table = [c for c in dialog.children() if isinstance(c, QTableWidget)]
        if len(table) < 1:
            return
        table = table[0]
        table.removeRow(table.currentRow())

    def save_config(self, silent=False):
        """
        Saves the configuration from the user-interface fields.
        :param silent: Hide or show error
        :type Boolean: Boolean
        :return:
        """
        if not path.isdir(self.config_folder):
            if not silent:
                self.show_message('Error',
                                  'Configuration folder is not selected in Basic Options')
                return
            else:
                self.config_folder = ROOT_PATH
        config = self.read_config()
        self.config_path = path.join(self.config_folder, 'config.json').replace('\\', '/')

        self.config = config

        with open(self.config_path, 'w') as outfile:
            json.dump(config, outfile)
        if self.buttonBox.button(QDialogButtonBox.Ok).text() == 'Run':
            self.buttonBox.button(QDialogButtonBox.Ok).setDisabled(False)
        if not silent:
            self.show_message('Information', 'Successfully saved the configuration in {}'.format(self.config_path))

        return config

    def file_dialog(self, line_edit):
        """
        Displays a file dialog for a user to specify a GPX Folder.
        :param line_edit: The line edit in which the folder is going to be set.
        :type line_edit: QLineEdit
        """
        title = QApplication.translate(
            "SensorsBridge",
            "Select a Folder"
        )

        last_path = expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self.parent(),
            title,
            last_path,
            QFileDialog.ShowDirsOnly
        )
        path = path.replace('\\', '/')
        if len(path) > 0:
            line_edit.setText(path)

        if line_edit == self.data_folder_lne:
            self._data_folder = path

        if line_edit == self.config_folder_le:
            self.config_folder = path
            self.sensors_config_tw.blockSignals(True)
            self.configFolder.emit(path)
            self.sensors_config_tw.blockSignals(False)

    def show_list(self):
        """
        Shows a dialog with list of headers or excludes from the respective cells.
        :return:
        """
        dialog = QDialog(self)
        buttonBox = QDialogButtonBox(dialog)
        buttonBox.setEnabled(True)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel |
            QDialogButtonBox.Ok | QDialogButtonBox.Save)

        obj_name = self.sender().objectName()

        obj_names = obj_name.split(',')
        indexes = obj_names[0].split(':')
        col_index = indexes[0]

        row_index = indexes[1]
        buttonBox.setObjectName("{},{}".format(row_index, col_index))
        name = obj_names[1]
        if self.sensors_config is not None:
            confs = [c for c in self.sensors_config if c['name'] == name]
        else:
            confs = []

        if len(confs) == 1:
            conf = confs[0]
            label = conf['label']
        else:
            label = 'New'
        header = self.sensors_config_tw.item(
            int(row_index), int(col_index)).text().split(',')
        dialog.setWindowTitle('{} {}'.format(
            label, self.header_indexes[col_index]))
        dialog.resize(278, 457)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        v_layout = QVBoxLayout(dialog)
        list_table = QTableWidget()
        list_table.setRowCount(len(header))
        list_table.setColumnCount(1)

        list_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        list_table.horizontalHeader().setVisible(True)
        h_item = QTableWidgetItem()
        h_item.setText(self.header_indexes[col_index].title())

        list_table.setHorizontalHeaderItem(0, h_item)

        for idx, head in enumerate(header):
            item = QTableWidgetItem(head)
            list_table.setItem(idx, 0, item)

        btn_add = QToolButton()
        btn_add.setText("Add")
        btn_remove = QToolButton()
        btn_remove.setText("Remove")
        playout = QHBoxLayout()
        playout.addWidget(btn_add)
        playout.addWidget(btn_remove)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        playout.addItem(spacerItem)
        v_layout.addLayout(playout)
        v_layout.addWidget(list_table)
        v_layout.addWidget(buttonBox)
        btn_remove.clicked.connect(self.remove_header)
        btn_add.clicked.connect(self.add_header)
        buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_header)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.save_header)
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(dialog.close)
        dialog.show()

    def validate_com(self):
        pass

    def save_header(self):
        """
        After user make changes, save the header or exclude column based of user selection.
        :return:
        """
        row_col = self.sender().parentWidget().objectName()

        row_col = row_col.split(',')
        row = int(row_col[0])
        col = int(row_col[1])
        dialog = self.sender().parentWidget().parentWidget()
        table = [c for c in dialog.children() if isinstance(c, QTableWidget)]
        header = []
        if len(table) < 1:
            return
        table = table[0]
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                cell_item = table.item(r, c)
                if cell_item is not None:
                    text = cell_item.text().strip()
                    if len(text) > 0:
                        header.append(text)
        # print (row, col)
        self.sensors_config_tw.item(row, col).setText(','.join(header))

        self.sensors_config_tw.viewport().update()
        if self.sender().text() == 'OK':
            dialog.close()

    def sensor_label_changed(self, row, col):
        """
        A slot emitted when a user changes the sensor label. The slot sets object names to
        the edit buttons of header and exclude fields.
        :param row: The edited cell row index
        :type row: Integer
        :param col: The edited column index
        :type col: Integer
        :return:
        """
        if col == 0:
            name = self.sensors_config_tw.item(row, col).text().replace(' ', '')
            widget_3 = self.sensors_config_tw.cellWidget(row, 3)
            widget_3s = [w for w in widget_3.children() if isinstance(w, QToolButton)]
            if len(widget_3s) == 0:
                return
            header_btn = widget_3s[0]
            header_btn.setObjectName('{}:{},{}'.format(3, row, name))

            name = self.sensors_config_tw.item(row, col).text().replace(' ', '')
            widget_4 = self.sensors_config_tw.cellWidget(row, 4)
            widget_4s = [w for w in widget_4.children() if isinstance(w, QToolButton)]
            if len(widget_4s) == 0:
                return
            exclude_btn = widget_4s[0]
            exclude_btn.setObjectName('{}:{},{}'.format(4, row, name))

    def load_sensor_config(self):
        """
        Load sensor configuration by reading from the configuration
        file's sensors_config property.
        :return:
        """
        self.sensors_config_tw.setRowCount(0)
        for idx, (conf) in enumerate(self.sensors_config):

            self.sensors_config_tw.insertRow(idx)
            item0 = QTableWidgetItem(conf['label'])

            self.sensors_config_tw.setItem(idx, 0, item0)
            combo = QComboBox()
            for t in self.interfaces:
                combo.addItem(t)
                if 'COM' in conf['code']:
                    combo.setCurrentIndex(0)
                else:
                    combo.setCurrentIndex(1)
            self.sensors_config_tw.setCellWidget(idx, 1, combo)

            if 'COM' in conf['code']:
                combo2 = QComboBox()
                for com in self.com_ports:
                    combo2.addItem(com)

                index = combo2.findText(conf['code'], Qt.MatchFixedString)

                if index >= 0:
                    combo2.setCurrentIndex(index)
                else:
                    combo2.addItem(conf['code'])
                    combo2.setCurrentIndex(0)
                self.sensors_config_tw.setCellWidget(idx, 2, combo2)
            else:
                item2 = QTableWidgetItem(conf['code'])

                self.sensors_config_tw.setItem(idx, 2, item2)

            item3 = QTableWidgetItem(conf['header'])
            btn_widget, btn = self.create_table_edit_button()
            btn.setObjectName('{}:{},{}'.format(3, idx, conf['name']))
            btn.clicked.connect(self.show_list)
            self.sensors_config_tw.setCellWidget(idx, 3, btn_widget)
            self.sensors_config_tw.setItem(idx, 3, item3)

            item4 = QTableWidgetItem(conf['exclude'])
            btn_widget2, btn2 = self.create_table_edit_button()
            btn2.setObjectName('{}:{},{}'.format(4, idx, conf['name']))
            btn2.clicked.connect(self.show_list)
            self.sensors_config_tw.setItem(idx, 4, item4)
            self.sensors_config_tw.setCellWidget(idx, 4, btn_widget2)

    def create_table_edit_button(self):
        """
        Adds an edit button that can be added to a cell.
        :return:
        """
        widget = QWidget()

        btn_edit = QToolButton()
        btn_edit.setText("Edit")

        h_layout = QHBoxLayout(widget)
        h_layout.addWidget(btn_edit)
        h_layout.setAlignment(Qt.AlignRight)
        h_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(h_layout)
        return widget, btn_edit

    def create_log_tab(self):
        """
        Creates an empty log tab for all the sensors.
        :return:
        """
        self.log_tab.clear()
        for sensor in self.sensors_config:
            log_box = QPlainTextEdit(self.parent())

            log_box.setObjectName(sensor['name'])
            self.log_boxes[sensor['name']] = log_box
            self.log_tab.addTab(log_box, sensor['label'])

    def read_a_file(self, file_path, name):
        """
        Reads a log or data file from a file path.
        :param file_path: The file path
        :type file_path: String
        :param name: Sensor or type name
        :type name: String
        :return:
        """
        the_file = open(file_path, 'r')

        # file_name = path.basename(file_path)
        # if 'log_' in file_name:
        #     name = 'log'
        # else:
        #     name = file_name.split('_')[-1].split('.')[0]
        # # print (name)
        the_file.seek(0, SEEK_END)  # End-of-file
        # print (file_path)
        while True:
            if STOP:
                break
            line = the_file.readlines()

            if not line:
                continue
            line_str = ''.join(line).lower()
            # print(name, line)
            if 'error' in line_str or 'trackback' in line_str:
                self.log.emit('<br>'.join(line))
            else:
                for r in line:

                    if name != 'log':
                        # print(name, r)
                        self.log.emit('{}${}'.format(name, r))
                    else:
                        # print(r)
                        self.log.emit(r)# the log file already has name$message layout

        the_file.close()

    def run_reading_log_file(self):
        """
        Executes the thread to read a log file.
        :return:
        """
        now = datetime.now()
        dt_name_str = now.strftime("%d_%m_%Y")
        file_name = 'log_{}.txt'.format(dt_name_str)
        log_file = path.join(self.basic_options['data_path'], file_name)

        if not path.isfile(log_file):
            return

        t = threading.Thread(
            name='background', target=self.read_a_file, args=(log_file, 'log',)
        )
        t.start()
        return t

    def run_reading_data_file(self, sensor):
        """
        Executes the thread to read data file.
        :param sensor: The name of the sensor for which the data is going to be read.
        :type sensor: Dictionary
        :return:
        """
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y")
        file_name = '{}_{}.csv'.format(dt_string, sensor['name'])
        file_path = path.join(self.basic_options['data_path'], file_name)

        if not path.isfile(file_path):
            f = open(file_path, 'w')
            f.close()
        # print (file_path)
        t = threading.Thread(name='background', target=self.read_a_file,
                             args=(file_path,sensor['name']))
        t.start()
        return t

    def read_config(self):
        """
        Read the configuration from the user interface.
        :return:
        """
        config = {}
        sensors_config = []
        basic_options = {}
        server_options = {}

        for row in range(self.sensors_config_tw.rowCount()):
            conf = {}

            for col in range(self.sensors_config_tw.columnCount()):
                head = self.sensors_config_tw.horizontalHeaderItem(col).text()
                head = head.lower()

                cell_item = self.sensors_config_tw.item(row, col)
                cell_widget = self.sensors_config_tw.cellWidget(row, col)

                if cell_item is not None:
                    conf[head] = cell_item.text()
                    if head == 'label':
                        conf['name'] = re.sub(' ', '', conf['label'].lower())
                if cell_item is None and cell_widget is not None:
                    cell_widget = self.sensors_config_tw.cellWidget(row, col)
                    conf[head] = cell_widget.currentText()

            sensors_config.append(conf)

        basic_options['data_path'] = self.data_folder_lne.text()
        basic_options['file_keep_limit'] = self.file_keep_limit_sb.value()
        basic_options['udp_port'] = self.udp_port_sb.value()
        server_options['server'] = self.server_le.text()
        server_options['server_login'] = self.server_login_le.text()
        server_options['username'] = self.username_le.text()
        server_options['password'] = self.password_le.text()
        server_options['send_data'] = self.server_gb.isChecked()

        config['basic_options'] = basic_options
        config['server_options'] = server_options
        config['sensors_config'] = sensors_config

        return config

    def insert_text_to_log_box(self, str):
        """
        Inserts data or log to the respective sensor tab in the log tab.
        :param str: The text to be inserted.
        :type str: String
        :return:
        """
        if '$' in str:
            names = str.split('$')

            log_box = self.log_boxes[names[0]]

            if '<br>' in names[1]:
                html = '<div style="color:red;">{}</div>'.format(names[1])
                log_box.appendHtml(html)
            else:
                log_box.appendPlainText(names[1].strip())

    def accept(self):
        """
        A slot raised when the user presses the Run button.
        This empty function prevents the closing of the
        dialog after pressing the Run button.
        :return:
        """
        pass


if __name__ == "__main__":
    import sys
    # Prevent the multiprocessing window from executiving this several times.
    multiprocessing.freeze_support()
    processes = []
    threads = []

    def except_hook(cls, exception, traceback):
        """
        Fixes the issue of exception not showing in PyQt.
        """
        sys.__excepthook__(cls, exception, traceback)


    def run_process(app):

        """
        Runs the data capture and sending after reading and saving the configuration.
        It uses multiprocessing library to run data capture of all sensors simultaneously.
        There will be only one process for the UDP to capture data. Each COM ports will have
        their own process.
        :param app: SensorsBridge class
        :type app: Class
        :return:
        """
        global STOP
        if len(processes) > 0:
            processes.clear()
        if len(threads) > 0:
            threads.clear()
        STOP = False
        config = app.save_config(True)
        if len(config['basic_options']['data_path'].strip())==0:
            app.show_message('Error', 'Unable to run as no data folder is selected.')
            return
        if not path.isdir(config['basic_options']['data_path'].strip()):
            app.show_message('Error', 'Unable to run as the data folder does not exist.')
            return
        if len(config['sensors_config']) == 0:
            app.show_message('Error', 'Unable to run as no sensor configuration is filled out.')
            return

        for sensor in config['sensors_config']:
            if app.data_log_ck.isChecked():
                t = app.run_reading_data_file(sensor)
                threads.append(t)

        app.buttonBox.button(QDialogButtonBox.Ok).setDisabled(True)
        if app.sys_msg_log_ck.isChecked():
            t = app.run_reading_log_file()
            threads.append(t)
        bridge = Bridge(config)
        app.buttonBox.button(QDialogButtonBox.Ok).setText("Running...")
        app.toolBox.setCurrentIndex(2)

        with open(app.config_path, 'w') as outfile:
            json.dump(config, outfile)

        for sensor in config['sensors_config']:
            msg = 'Started capturing {} data.'.format(
                sensor['label']
            )

            bridge.create_log(msg, sensor['name'])

            if sensor['type'] == 'COM port':  # To exclude UDP reading

                if config["server_options"]["send_data"]:
                    bridge.connect_to_server(sensor)

                p = Process(target=bridge.read_com, args=(sensor,))
                p.name = sensor['label']
                p.daemon = True
                processes.append(p)

        p0 = Process(target=bridge.read_udp)
        p0.name = 'GPS Position'
        p0.daemon = True
        processes.append(p0)
        try:
            for p in processes:
                # print (p)
                p.start()
        except AssertionError:
            pass

        bridge.delete_old_files()


    def terminate_processes(app):
        """
        Stops the multiple process being run.
        :param app: SensorsBridge class
        :type app: Class
        :return:
        """
        global STOP
        STOP = True
        app.buttonBox.button(QDialogButtonBox.Ok).setText("Run")
        try:
            for i, p in enumerate(processes):
                p.terminate()

            for j, t in enumerate(threads):
                t.exit()
                # threads.pop(j)
        except AttributeError:
            pass
        except AssertionError:
            pass
        app.buttonBox.button(QDialogButtonBox.Ok).setDisabled(False)


    def main():
        """
        The main method that opens the application dialog and
        connects run and terminate process signals.
        :return:
        """
        app = QApplication([])
        sensor_bridge = SensorsBridge()
        sensor_bridge.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: run_process(sensor_bridge)
        )
        sensor_bridge.buttonBox.button(QDialogButtonBox.Discard).clicked.connect(
            lambda: terminate_processes(sensor_bridge)
        )

        sensor_bridge.rejected.connect(lambda: terminate_processes(sensor_bridge))

        sensor_bridge.show()
        app.exec_()

    sys.excepthook = except_hook
    main()
