import re
import time
import os
import serial
import glob
from datetime import datetime

from urllib.parse import urlencode
import requests
from config import USERNAME,PASSWORD, SERVER_LOGIN, SERVER, PORT_INFO, DATA_PATH
SESSION = None

def connect_to_server():
    global SESSION
    params = urlencode(
        {'username': USERNAME, 'password': PASSWORD, 'f': 'json'})
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    SESSION = requests.Session()

    response = SESSION.post(SERVER_LOGIN, data=params, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        msg = 'Error to login: Error {}. It will save data locally until internet is restored'.format(
            response.status_code)
        print(msg)
        create_log(msg)
        SESSION = None
        return False
    # send data that was not sent due to internet problem

    return True

def create_log(message):
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y %H:%M:%S")

    file_path = os.path.join(DATA_PATH,'error_log.txt')
    with open(file_path, 'a') as data_file:
        data_file.write('{} {}\n'.format(dt_string, message))

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
        data_file.write(','.join(data)+'\n')

def save_to_temp_file(com, data):
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_temp_")
    file_name = '{}_{}.txt'.format(dt_string, PORT_INFO[com]['name'])
    file_path = os.path.join(DATA_PATH, file_name)
    with open(file_path, 'a') as data_file:
        data_file.write(','.join(data)+'\n')
def send_to_server(com, data):
    global SESSION
    # print(SESSION)
    url = '{}{}'.format(SERVER, PORT_INFO[com]['name'])
    response = SESSION.post(url, data=data)

    if response.status_code != 200:
        msg = 'Error: {} Failed to send {} at port {}. Saving it to local file.'.format(
            response.status_code,PORT_INFO[com]['name'], com
        )
        print(msg)
        create_log(msg)

def send_temp_files():
    global SESSION
    if SESSION is None: # dont send if the user hasn't logged in
        return
    temp_files = glob.glob(DATA_PATH+'/*temp*')
    print (temp_files)
    for temp_file in temp_files: # get com port from temp file
        coms = [l for l in PORT_INFO.keys()
                if PORT_INFO[l]['name'] in temp_file]
        print (coms)
        if len(coms) > 0:
            com = coms[0]
        else:
            continue # because it is not a comp file
        with open(temp_file, "r") as f:
            lines = f.readlines()

            for line in lines:

                data = dict(zip(PORT_INFO[com]['header'],
                                line.strip().split(',')))
                send_to_server(com, data)
        os.remove(temp_file) # delete file after all data is sent

def delete_old_files():
    current_time = time.time()
    for f in os.listdir(DATA_PATH):
        creation_time = os.path.getctime(f)
        if (current_time - creation_time) // (24 * 3600) >= 3:
            os.unlink(f)
            print('{} removed'.format(f))

def read_com(com):
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
            c = a_serial.readline()
            row = re.split(PORT_INFO[com]['separator'], c.decode().strip())
            if len(row) < 4:
                continue
            data = dict(zip(PORT_INFO[com]['header'], row))
            if SESSION is not None:
                send_to_server(com, data)
            else:
                save_to_temp_file(com, data)
                connect_to_server()

            save_to_file(com, row)
    except Exception as ex:
        print (ex)
        create_log(ex)

print ('Imported transfer.py')