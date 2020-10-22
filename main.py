import json
import csv
import re
import time
import os
import serial
import socket
import sys
import glob
import traceback
import urllib3
from PyQt5.QtGui import QIcon

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import serial.tools.list_ports
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
import multiprocessing
import serial.tools.list_ports
from multiprocessing import Process

from os.path import expanduser

from PyQt5.QtCore import pyqtSignal, QObject, Qt


from PyQt5.QtWidgets import (
    QDialog, QApplication,
    QFileDialog, QTableWidgetItem,
    QComboBox, QDialogButtonBox, QHeaderView, QTextEdit, QLineEdit, QAction, QWidget, QPushButton, QHBoxLayout,
    QToolButton, QListWidget, QTableWidget, QVBoxLayout, QSizePolicy, QSpacerItem)
from urllib3.exceptions import InsecureRequestWarning

from ui.sensorsbridge import Ui_SensorsBridge


SESSION = None
ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = '{}/config.json'.format(ROOT_PATH)

STOP = False
import logging

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        # print (record)
        if record: XStream.stdout().write('%s\n'%record)
        # if record: XStream.stderr().write('%s\n' % record)

        # originally: XStream.stdout().write("{}\n".format(record))

logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class XStream(QObject):
    _stdout = None
    _stderr = None
    messageWritten = pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        # if ( not self.signalsBlocked() ):
        self.messageWritten.emit(msg)

    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        # print(XStream._stdout)
        return XStream._stdout
    @staticmethod
    def stderr():

        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        # print(XStream._stderr)
        return XStream._stderr


class Bridge():

    # log = pyqtSignal(str)

    def __init__(self, config):
        # QThread.__init__(self)
        self.config = config
        self.sensors_config = config['sensors_config']
        self.basic_options = config['basic_options']
        self.server_options = config['server_options']
        self.udp_sensors = {s['code']:s for s in self.sensors_config if s['type'] =='UDP'}
        self.default_config = config['default_config']

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
        verify_ssl = False

        try:
            response = SESSION.post(
                self.server_options['server_login'],
                data=params, headers=headers, verify=verify_ssl
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
            print(msg_with_time)
            return False


    # def set_log_box(self, log_box):
    #     self.log_box = log_box

    def create_log(self, message, sensor_name='', show_message=True):
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        dt_name_str = now.strftime("%d_%m_%Y")
        file_name = 'log_{}.txt'.format(dt_name_str)
        file_path = os.path.join(self.basic_options['data_path'], file_name)
        if sensor_name != '':
            msg = '{}${} {}\n'.format(sensor_name, dt_string, message)
        else:
            msg = '{} {}\n'.format(dt_string, message)
        logger.debug(msg.strip())
        # print (msg.strip())
        with open(file_path, 'a') as data_file:
            data_file.write(msg.replace('$', ':'))
        # print ("This test ", msg)

        # LOG.info(msg.strip())
        # if self.dlg.log_text_edit is not None:
        #     self.dlg.log_text_edit.append(msg.strip())
        # self.log.emit(msg.strip())
        if show_message:
        #     # self.log_text_edit.append(msg.strip())
            print(msg.strip())
        return msg.strip()

    def read_file(self, file_path):
        thefile = open(file_path)
        # print(os.SEEK_END)
        thefile.seek(0, os.SEEK_END)  # End-of-file
        while True:

            line = thefile.readline()
            if not line:
                time.sleep(0.1)  # Sleep briefly
                continue
            yield line

    def save_to_file(self, sensor, data):
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y")
        file_name = '{}_{}.csv'.format(dt_string, sensor['name'])
        file_path = os.path.join(self.basic_options['data_path'], file_name)
        try:
            if not os.path.isfile(file_path):
                with open(file_path, 'w', newline='') as csvfile:
                    wr = csv.writer(csvfile, delimiter=',', lineterminator='\n')
                    wr.writerow(data.keys())

            with open(file_path, 'a') as data_file:
                wr = csv.writer(data_file, delimiter=',', lineterminator='\n')
                wr.writerow(data.values())
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])

    def save_to_temp_file(self, sensor, data):
        # print (data)
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y_temp")
        file_name = '{}_{}.csv'.format(dt_string, sensor['name'])
        file_path = os.path.join(self.basic_options['data_path'], file_name)

        if not os.path.isfile(file_path):
            with open(file_path, 'w', newline='') as csvfile:
                wr = csv.writer(csvfile, delimiter=',', lineterminator='\n')
                wr.writerow(data.keys())

        with open(file_path, 'a') as data_file:
            wr = csv.writer(data_file, delimiter=',', lineterminator='\n')
            wr.writerow(data.values())

        #
        #
        # now = datetime.now()
        # dt_string = now.strftime("%d_%m_%Y_temp")
        # file_name = '{}_{}.txt'.format(dt_string, sensor['name'])
        # file_path = os.path.join(self.basic_options['data_path'], file_name)
        # with open(file_path, 'a') as data_file:
        #     data_file.write(','.join(data) + '\n')

    def send_to_server(self, sensor, data):
        global SESSION
        if SESSION is None:
            return False
        url = '{}{}'.format(self.server_options['server'], sensor['name'])
        verify_ssl = False
        # if self.server_options['server'].startswith('https'):
        #     verify_ssl = True
        # print(verify_ssl)
        try:
            response = SESSION.post(url, data=data, verify=verify_ssl)
            if response.status_code != 200:
                msg = 'Error: {} Failed to send {} at port {}. Saving it to local file.'.format(
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
            if not os.path.exists(temp_file):
                continue
            msg = 'Sending backup {}'.format(temp_file)
            msg_with_time = self.create_log(msg,sensor['name'])
            print(msg_with_time)
            results = []
            with open(temp_file, "r") as f:
                lines = f.readlines()

                for i, line in enumerate(lines):
                    if i ==0:
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
                    os.remove(temp_file)  # delete file after all data is sent
                except:  # error may happen when deleting file being read so pass it
                    pass
        header.remove('datetime')

    def send_temp_files(self):
        global SESSION
        if SESSION is None:  # dont send if the user hasn't logged in
            return
        temp_files = glob.glob(self.basic_options['data_path'] + '/*temp*')
        # print (temp_files)
        for temp_file in temp_files:  # get com port from temp file
            if not os.path.exists(temp_file):
                continue
            sensors = [l for l in self.sensors_config
                    if self.sensors_config['name'] in temp_file]

            if len(sensors) > 0:
                sensor = sensors[0]
            else:
                continue  # because it is not a comp file
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
                os.remove(temp_file)  # delete file after all data is sent
            except:  # error may happen when deleting file being read so pass it
                pass
            header.remove('datetime')

    def delete_old_files(self):
        current_time = time.time()
        txt_data = glob.glob('{}\\*.txt'.format(self.basic_options['data_path']))
        for f in txt_data:
            creation_time = os.path.getctime(f)
            if (current_time - creation_time) // (24 * 3600) >= self.basic_options['file_keep_limit']:
                os.unlink(f)
                msg = '{} removed'.format(f)
                msg_with_time = self.create_log(msg)
                print(msg_with_time)

    def filter_data(self, data, sensor):
        new_dict = {}
        for key, value in data.items():
            if key not in sensor['exclude']:
                new_dict[key] = value
        return new_dict

    def read_udp(self):
        show_no_internet_error = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        # self.connect_to_server('Ancillary')
        sock.bind(('', self.basic_options['udp_port']))
        # program_starts = time.time()
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
                    header =sensor['header'].split(',')

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
        # convert nmea lat lon to decimal degrees.
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
        show_no_internet_error = True
        try:
            a_serial = serial.Serial(
                sensor['code'], self.default_config[sensor['name']]['baud_rate'],
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE
            )
            if sensor['code'] == 'COM7':
                a_serial.write(b'setbaud=9600\r\n')
                a_serial.write(b'setbaud=9600\r\n')
                a_serial.write(b'SetFormat=1\r\n')
                a_serial.write(b'SetAvg=2\r\n')
                a_serial.write(b'Start\r\n')
            header = sensor['header'].split(',')
            logger.info (header)
            separator = self.default_config[sensor['name']]['separator']
            while True:
                if STOP:
                    break
                utc_time = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S.%f")
                c = a_serial.readline()
                # print (c)
                row = re.split(separator, c.decode().strip())
                # print (sensor['header'])
                # print(self.create_log(', '.join(row),sensor['name'] ))
                # print ( len(row), len(header))

                if len(row) != len(header):
                    continue
                data = dict(zip(header, row))

                data['datetime'] = utc_time
                logger.info(row)
                self.manage_data(data, sensor, show_no_internet_error)
                # print (data)
            #
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
            # print('Failed data: ', sensor['code'], data)
            # print(msg_with_time)

    def manage_data(self, data, sensor, show_no_internet_error):
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
    # log = pyqtSignal(str)

    def __init__(self, parent=None):

        QDialog.__init__(self, parent)
        # super(SensorsBridge, self).__init__(parent)
        self.setupUi(self)
        self._data_folder = None
        self.data_folder_btn.clicked.connect(
            lambda: self.file_dialog(self.data_folder_lne)
        )
        self._input_gpx_folder_path = None
        self.interfaces = ['COM port', 'UDP']
        self.com_ports = []
        for i in serial.tools.list_ports.comports():
            self.com_ports.append(str(i).split(" ")[0])
        with open(CONFIG_PATH) as f:
            self.config =json.load(f)
        self.basic_options = self.config['basic_options']
        self.server_options = self.config['server_options']
        self.sensors_config = self.config['sensors_config']
        self.log_messages = {}
        self.header_indexes = {'3':'header', '4':'exclude'}
        self.log_box = None
        self.init_gui()

    def init_gui(self):

        self.setWindowFlags(
            self.windowFlags() |
            Qt.WindowSystemMenuHint |
            Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint
        )

        self.setWindowIcon(QIcon('{}/favicon.ico'.format(ROOT_PATH)))
        pw = self.password_le
        pw.setEchoMode(QLineEdit.Password)
        pw.show()
        self.server_gb.toggled.connect(self.connect_to_server)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Run")
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("Exit")
        self.data_folder_lne.setText(self.basic_options['data_path'])
        self.file_keep_limit_sb.setValue(self.basic_options['file_keep_limit'])
        self.server_le.setText(self.server_options['server'])
        self.server_login_le.setText(self.server_options['server_login'])
        self.username_le.setText(self.server_options['username'])
        self.password_le.setText(self.server_options['password'])
        # print(self.server_options["send_data"])
        self.server_gb.setChecked(self.server_options["send_data"])

        self.udp_port_sb.setValue(self.basic_options['udp_port'])
        self.sensors_config_tw.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.sensors_config_tw.horizontalHeader().setVisible(True)

        self.init_interface_type()
        self.add_btn.clicked.connect(self.add_sensor)
        self.remove_btn.clicked.connect(self.remove_sensor)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_config)

        # self.read_config()
    def connect_to_server(self, status):
       self.server_options["send_data"]  = 1

    def interface_changed(self, value):

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
        print ('Removed')
        self.sensors_config_tw.removeRow(
            self.sensors_config_tw.currentRow())

    def add_header(self):
        dialog = self.sender().parentWidget()
        table = [c for c in dialog.children() if isinstance(c, QTableWidget)]
        if len(table) < 1:
            return
        table = table[0]

        table.insertRow(table.currentRow()+1)


    def remove_header(self):
        dialog = self.sender().parentWidget()
        table = [c for c in dialog.children() if isinstance(c, QTableWidget)]
        if len(table) < 1:
            return
        table = table[0]
        table.removeRow(table.currentRow())


    def save_config(self):
        config = self.read_config()
        self.config.clear()
        self.config = config
        with open(CONFIG_PATH, 'w') as outfile:
            json.dump(config, outfile)

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
        if len(path) > 0:
            line_edit.setText(path)

        if line_edit == self.data_folder_lne:
            self._data_folder = path

    def show_list(self):
        dialog = QDialog(self)
        buttonBox = QDialogButtonBox(dialog)
        buttonBox.setEnabled(True)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel |
            QDialogButtonBox.Ok | QDialogButtonBox.Save)


        obj_name = self.sender().objectName()
        # print (obj_name)
        obj_names = obj_name.split(',')
        indexes = obj_names[0].split(':')
        col_index = indexes[0]

        row_index = indexes[1]
        buttonBox.setObjectName("{},{}".format(row_index, col_index))
        name = obj_names[1]

        confs = [c for c in self.sensors_config if c['name'] == name]
        if len(confs) == 1:

            conf = confs[0]
            header = conf[self.header_indexes[col_index]].split(',')
            label = conf['label']
        else:
            header = []
            label = 'New'
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
        # item = list_table.horizontalHeaderItem(0)
        # item.setText("Header")

        for idx, head in enumerate(header):
            print (head)
            # list_table.insertRow(idx)
            item = QTableWidgetItem(head)
            list_table.setItem(idx, 0, item)

        # pwidget = QWidget()

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
        # print (col_index, row_index)
        buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_header)

        dialog.show()

    def validate_com(self):
        pass

    def save_header(self):
        row_col =  self.sender().parentWidget().objectName()
        # print ( 2, self.sender().parentWidget().parentWidget().objectName())
        # row_col = self.sender().parentWidget().button(QDialogButtonBox.Save).objectName()
        # print (3, row_col)
        row_col = row_col.split(',')
        row = int(row_col[0])
        col = int(row_col[1])
        dialog = self.sender().parentWidget().parentWidget()
        table = [c for c in dialog.children() if isinstance(c,QTableWidget)]
        header = []
        if len(table) < 1:
            return
        table = table[0]
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                cell_item = table.item(r, c)
                text = cell_item.text().strip()
                if len(text)> 0:
                    header.append(text)
        # print (row, col)
        self.sensors_config_tw.item(row, col).setText(','.join(header))

        self.sensors_config_tw.viewport().update()

    def init_interface_type(self):
        # print (self.sensors_config)
        for idx, (conf) in enumerate(self.sensors_config):
            # idx = idx+1
            self.sensors_config_tw.insertRow(idx)
            item0 = QTableWidgetItem(conf['label'])
            # print (conf)
            self.sensors_config_tw.setItem(idx, 0, item0)
            combo = QComboBox()
            for t in self.interfaces:
                combo.addItem(t)
                if 'COM' in conf['code']:
                    combo.setCurrentIndex(0)
                else:
                    combo.setCurrentIndex(1)
            self.sensors_config_tw.setCellWidget(idx,1, combo)

            if 'COM' in conf['code']:
                combo2 = QComboBox()
                for com in self.com_ports:
                    combo2.addItem(com)

                index = combo2.findText(conf['code'], Qt.MatchFixedString)
                # print (index, conf['code'])

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
            btn.setObjectName('{}:{},{}'.format(3,idx, conf['name']))
            btn.clicked.connect(self.show_list)
            self.sensors_config_tw.setCellWidget(idx, 3, btn_widget)
            self.sensors_config_tw.setItem(idx, 3, item3)

            item4 = QTableWidgetItem(conf['exclude'])
            btn_widget2,btn2 = self.create_table_edit_button()
            btn2.setObjectName('{}:{},{}'.format(4, idx, conf['name']))
            btn2.clicked.connect(self.show_list)
            self.sensors_config_tw.setItem(idx,4, item4)
            self.sensors_config_tw.setCellWidget(idx, 4, btn_widget2)

    def create_table_edit_button(self):

        pWidget = QWidget()

        btn_edit = QToolButton()
        btn_edit.setText("Edit")

        pLayout = QHBoxLayout(pWidget)
        pLayout.addWidget(btn_edit)
        pLayout.setAlignment(Qt.AlignRight)
        pLayout.setContentsMargins(0, 0, 0, 0)
        pWidget.setLayout(pLayout)
        return pWidget, btn_edit

    def create_log_tab(self, name):

        # self.tabCloseRequested.connect(self.closeTab)
        # print(name)
        self.log_box = QTextEdit(self.parent())
        self.log_box.setObjectName(name.lower().replace(' ', ''))
        self.log_tab.addTab(self.log_box, name)


    def read_config(self):
        config = {}
        sensors_config = []
        basic_options = {}
        server_options = {}
        # i is always in range 4 in my code
        for row in range(self.sensors_config_tw.rowCount()):
            conf = {}
            # conf['label'] = self.sensors_config_tw.verticalHeaderItem(row).text()
            # conf['name'] = re.sub(' ', '', conf['label'].lower())
            # print ("NAME", conf['name'])
            for col in range(self.sensors_config_tw.columnCount()):
                head = self.sensors_config_tw.horizontalHeaderItem(col).text()
                head = head.lower()

                cell_item = self.sensors_config_tw.item(row, col)
                cell_widget = self.sensors_config_tw.cellWidget(row, col)
                # print (cell_item, cell_widget)
                # if (cell_item):
                #     print (cell_item.currentText())
                if cell_item is not None:

                    conf[head] = cell_item.text()
                    if head == 'label':
                        conf['name'] = re.sub(' ', '', conf['label'].lower())
                if cell_item is None and cell_widget is not None:
                    cell_widget = self.sensors_config_tw.cellWidget(row, col)
                    conf[head] = cell_widget.currentText()

                # if item is not None:
                #     print (item.text())
            sensors_config.append(conf)
        # print (sensors_config)
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
        config['default_config'] = self.config['default_config']
        config['default_sensors_config'] = self.config['default_sensors_config']
        # print (config)

        return config

    def insert_log_text(self, str):
        # print(self.log_box, " connected" )
        if '$' in str:
            names = str.split('$')

            if self.log_box.objectName() ==names[0]:

                if names[0] not in self.log_messages.keys():
                    self.log_messages[names[0]] = []

                self.log_messages[names[0]].append(names[1])
                self.log_box.append(names[1])

        else:
            self.log_box.append(str)

    def accept(self):
        self.buttonBox.button(QDialogButtonBox.Ok).setDisabled(True)
        # for sensor in self.sensors_config:
        #     self.create_log_tab(sensor['label'])
        # XStream.stdout().messageWritten.connect(self.insert_log_text)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

if __name__ == "__main__":

    multiprocessing.freeze_support()
    processes = []
    def run_process(app):
        config = app.read_config()
        bridge = Bridge(config)
        app.toolBox.setCurrentIndex(2)

        with open(CONFIG_PATH, 'w') as outfile:
            json.dump(config, outfile)


        # run GPS and meteorology
        logger_init = False

        for sensor in config['sensors_config']:

            if sensor['type'] == 'COM port':  # To exclude UDP reading
                msg = 'Sensors Bridge connected to {} ({})'.format(
                    sensor['name'], sensor['code']
                )
                app.create_log_tab(sensor['label'])
                if not logger_init:
                    XStream.stdout().messageWritten.connect(app.insert_log_text)
                    XStream.stderr().messageWritten.connect(app.insert_log_text)
                    logger_init = True
                msg_with_time = bridge.create_log(msg, sensor['name'])
                if config["server_options"]["send_data"]:
                    bridge.connect_to_server(sensor)

                p = Process(target=bridge.read_com, args=(sensor,))
                p.name = sensor['label']
                processes.append(p)
            # if sensor['name'] == 'gpsposition':
                # msg = 'Sensors Bridge connected to ancillary data ({})'.format(
                #     config['basic_options']['udp_port']
                # )
                # app.create_log_tab(sensor['label'])
                # # XStream.stdout().messageWritten.connect(app.insert_log_text)
                # msg_with_time = bridge.create_log(msg, sensor['name'],)
                # print ('gps')
                # p0 = Process(target=bridge.read_udp)
                # p0.name = sensor['label']
                # processes.append(p0)
        # XStream.stdout().messageWritten.connect(app.insert_log_text)
        msg = 'Sensors Bridge connected to ancillary data ({})'.format(
            config['basic_options']['udp_port']
        )
        app.create_log_tab('GPS Position')
        # XStream.stdout().messageWritten.connect(app.insert_log_text)
        msg_with_time = bridge.create_log(msg, 'gpsposition')
        # print('gps')
        p0 = Process(target=bridge.read_udp)
        p0.name = 'GPS Position'
        processes.append(p0)

        for p in processes:
            p.start()
            # XStream.stdout().messageWritten.connect(app.insert_log_text)

        bridge.delete_old_files()
    def terminate_processes():
        global STOP
        STOP = True
        for p in processes:
            p.terminate()

    def main():
        # appctxt = ApplicationContext()
        app = QApplication([])
        sensor_bridge = SensorsBridge()
        sensor_bridge.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: run_process(sensor_bridge)
        )
        sensor_bridge.buttonBox.button(QDialogButtonBox.Save).clicked.connect(
             sensor_bridge.save_config
        )
        sensor_bridge.rejected.connect(terminate_processes)

        sensor_bridge.show()
        app.exec_()
    sys.excepthook = except_hook
    main()
