import re
import time
import os
import serial
import socket
import glob
import traceback
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
from config import (
    USERNAME,
    PASSWORD,
    SERVER_LOGIN,
    SERVER,
    PORT_INFO,
    DATA_PATH,
    LAN_PORT
)

SESSION = None


def connect_to_server(com, show_internet_error=True):
    """
    Connects sensors bridge to the server.
    :param com: The name of the port
    :type com: String
    :param show_internet_error: A boolean to show connection error or not
    :type show_internet_error: Boolean
    :return: The status of the connection
    :type: Boolean
    """
    global SESSION
    params = urlencode(
        {'username': USERNAME, 'password': PASSWORD, 'f': 'json'})
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    SESSION = requests.Session()

    response = SESSION.post(SERVER_LOGIN, data=params, headers=headers)
    # print(response.status_code)
    if response.status_code != 200:
        if show_internet_error:
            msg = 'Error to login {}. {} ({}) data saved locally until internet is restored'.format(
                response.status_code, PORT_INFO[com]['name'], com)

            msg_with_time = create_log(msg)
            print(msg_with_time)
        SESSION = None
        return False

    return True


def create_log(message):
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
    dt_name_str = now.strftime("%d_%m_%Y")
    file_name = 'log_{}.txt'.format(dt_name_str)
    file_path = os.path.join(DATA_PATH, file_name)
    msg = '{} {}\n'.format(dt_string, message)
    with open(file_path, 'a') as data_file:
        data_file.write(msg)
    return msg.strip()


def read_file(file_path):
    thefile = open(file_path)
    print(os.SEEK_END)
    thefile.seek(0, os.SEEK_END)  # End-of-file
    while True:

        line = thefile.readline()
        if not line:
            time.sleep(0.1)  # Sleep briefly
            continue
        yield line


def save_to_file(com, data):
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y")
    file_name = '{}_{}.txt'.format(dt_string, PORT_INFO[com]['name'])
    file_path = os.path.join(DATA_PATH, file_name)
    with open(file_path, 'a') as data_file:
        data_file.write(','.join(data) + '\n')


def save_to_temp_file(com, data):
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_temp")
    file_name = '{}_{}.txt'.format(dt_string, PORT_INFO[com]['name'])
    file_path = os.path.join(DATA_PATH, file_name)
    with open(file_path, 'a') as data_file:
        data_file.write(','.join(data) + '\n')


def send_to_server(com, data):
    global SESSION
    # print(SESSION)
    url = '{}{}'.format(SERVER, PORT_INFO[com]['name'])
    response = SESSION.post(url, data=data)

    if response.status_code != 200:
        msg = 'Error: {} Failed to send {} at port {}. Saving it to local file.'.format(
            response.status_code, PORT_INFO[com]['name'], com
        )

        msg_with_time = create_log(msg)
        print(msg_with_time)


def send_temp_files_by_com(com):
    global SESSION
    if SESSION is None:  # dont send if the user hasn't logged in
        return
    name = PORT_INFO[com]['name']
    temp_files = glob.glob(DATA_PATH + '/*temp*' + name + '*')
    header = PORT_INFO[com]['header']
    header.append('datetime')
    # print (temp_files)
    for temp_file in temp_files:  # get com port from temp file
        if not os.path.exists(temp_file):
            continue
        msg = 'Sending backup {}'.format(temp_file)
        msg_with_time = create_log(msg)
        # print(msg_with_time)
        with open(temp_file, "r") as f:
            lines = f.readlines()

            for line in lines:
                data = dict(zip(header,
                                line.strip().split(',')))

                send_to_server(com, data)
        msg2 = 'Completed sending backup {}'.format(temp_file)
        msg_with_time = create_log(msg2)
        print(msg_with_time)
        try:
            os.remove(temp_file)  # delete file after all data is sent
        except:  # error may happen when deleting file being read so pass it
            pass


def send_temp_files():
    global SESSION
    if SESSION is None:  # dont send if the user hasn't logged in
        return
    temp_files = glob.glob(DATA_PATH + '/*temp*')
    # print (temp_files)
    for temp_file in temp_files:  # get com port from temp file
        if not os.path.exists(temp_file):
            continue
        coms = [l for l in PORT_INFO.keys()
                if PORT_INFO[l]['name'] in temp_file]

        if len(coms) > 0:
            com = coms[0]
        else:
            continue  # because it is not a comp file
        header = PORT_INFO[com]['header']
        header.append('datetime')
        msg = 'Sending backup {}'.format(temp_file)
        msg_with_time = create_log(msg)
        # print(msg_with_time)
        with open(temp_file, "r") as f:
            lines = f.readlines()

            for line in lines:
                data = dict(zip(header,
                                line.strip().split(',')))
                send_to_server(com, data)
        msg2 = 'Completed sending backup {}'.format(temp_file)
        msg_with_time = create_log(msg2)
        print(msg_with_time)
        try:
            os.remove(temp_file)  # delete file after all data is sent
        except:  # error may happen when deleting file being read so pass it
            pass


def delete_old_files():
    current_time = time.time()
    for f in os.listdir(DATA_PATH):
        creation_time = os.path.getctime(f)
        if (current_time - creation_time) // (24 * 3600) >= 3:
            os.unlink(f)
            msg = '{} removed'.format(f)
            msg_with_time = create_log(msg)
            print(msg_with_time)


def read_udp():
    show_no_internet_error = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    sock.bind(('', LAN_PORT))
    while True:
        data_b, addr = sock.recvfrom(4096)
        utc_time = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S.%f")
        data_str = data_b.decode()
        if '$' or '*' not in data_str:
            continue

        row = data_str.rstrip('$').split('*')[0].split(',')
        if len(row) > 0:
            if row[0] in PORT_INFO.keys():
                data = dict(zip(PORT_INFO[row[0]]['header'], row[1:]))

                if row[0] == 'GPRMC':
                    process_location(data)
                data['datetime'] = utc_time
                manage_data(data, row[0], show_no_internet_error)
                print(data)


def process_location(data):
    # convert nmea lat lon to decimal degrees.
    # dd + mm.mmmm/60 for latitude
    # ddd + mm.mmmm/60 for longitude
    lat_hemi = 1
    lon_hemi = 1
    if data.get('latitude_direction') == 'S':
        lat_hemi = -1
    if data.get('longitude_direction') == 'W':
        lon_hemi = -1
    lat_string = data.get('latitude')
    lat_degs = int(lat_string[0:2])
    lat_mins = float(lat_string[2:])
    lat = (lat_degs + (lat_mins / 60)) * lat_hemi
    # Longitude
    lon_string = data.get('longitude')
    lon_degs = int(lon_string[0:3])
    lon_mins = float(lon_string[3:])
    lon = (lon_degs + (lon_mins / 60)) * lon_hemi
    data['latitude'] = lat
    data['longitude'] = lon


def read_com(com):
    show_no_internet_error = False
    try:
        a_serial = serial.Serial(
            com, PORT_INFO[com]['baud_rate'],
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE
        )
        if com == 'COM7':
            a_serial.write(b'setbaud=9600\r\n')
            a_serial.write(b'setbaud=9600\r\n')
            a_serial.write(b'SetFormat=1\r\n')
            a_serial.write(b'SetAvg=2\r\n')
            a_serial.write(b'Start\r\n')
        while True:
            utc_time = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S.%f")
            c = a_serial.readline()
            row = re.split(PORT_INFO[com]['separator'], c.decode().strip())
            if len(row) < 4:
                continue
            data = dict(zip(PORT_INFO[com]['header'], row))

            data['datetime'] = utc_time
            manage_data(data, com, show_no_internet_error)

    except:
        msg_with_time = create_log(traceback.format_exc())
        print(msg_with_time)


def manage_data(data, port_name, show_no_internet_error):
    if SESSION is not None:
        send_to_server(port_name, data)
    else:
        # print ("SESSION ", SESSION, com)
        # print(data)
        save_to_temp_file(port_name, data.values())
        show_no_internet_error = connect_to_server(port_name, show_no_internet_error)
        if show_no_internet_error:  # there is connection
            # send data that was not sent due to internet problem
            send_temp_files_by_com(port_name)
    save_to_file(port_name, data.values())
