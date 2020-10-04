import re
import time
import os
import serial
import requests
from urllib.parse import urlencode
from config import USERNAME, PASSWORD, SERVER_LOGIN

from config import SERVER, PORT_INFO

# TODO create a log file to store all activity (with options of verbose and error)
# verbose-log:
# all communication-data received,
# successfully sent,
# failed to receive and failed to send
# error-log:
# store only failures to read and send data to the server.
# error log and verbose log will be different files.
# ----------------------------------------
# TODO First - Save all data to file while sending it to the server
# TODO Future - Write it to temporary file, if the script is unable to send to the server
# TODO Connect to all ports in one script using multiprocessing!

file_path = r"C:\Users\User\Desktop\Sensor Data\sensor6.raw"

# URL-encode the token parameters
params = urlencode(
    {'username': USERNAME, 'password': PASSWORD, 'f': 'json'})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
SESSION = requests.Session()
response = SESSION.post(SERVER_LOGIN, data=params, headers=headers)


def create_log():
    pass


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
    path = r'C:\Users\User\Desktop\sensors_bridge\data'
    file_path = os.path.join(path, PORT_INFO[com]['name'] + '.txt')
    with open(file_path, 'a') as data_file:
        data_file.write(','.join(data) + '\n')


def send_to_server(com, data):
    url = '{}/{}'.format(SERVER, PORT_INFO[com]['name'])
    response = SESSION.post(url, data=data)

    if response.status_code == 200:
        print('Sent data to the server')
    else:
        print('Error: ', response.status_code)
        print('Failed to send. Saving it to local file.')


def read_com(com):
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
        c = a_serial.readline()
        row = re.split(PORT_INFO[com]['separator'], c.decode().strip())
        if len(row) < 4:
            continue
        data = dict(zip(PORT_INFO[com]['header'], row))
        print(data)
        send_to_server(com, data)
        save_to_file(com, row)
