import re
import time
import os
import serial
import requests
from config import SERVER, PORT_INFO
#TODO create a log file to store all activity (with options of verbose and error)
# verbose-log:
# all communication-data received,
# successfully sent,
# failed to receive and failed to send
# error-log:
# store only failures to read and send data to the server.
# error log and verbose log will be different files.
# ----------------------------------------
#TODO First - Save all data to file while sending it to the server
#TODO Future - Write it to temporary file, if the script is unable to send to the server
#TODO Connect to all ports in one script using multiprocessing!

file_path = r"C:\Users\User\Desktop\Sensor Data\sensor6.raw"


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
        # c = a_serial.read(PORT_INFO[com]['byte_size'])
        c = a_serial.readline()
        row = re.split(PORT_INFO[com]['separator'], c.decode().strip())
        if len(row) < 4:
            continue

        data = dict(zip(PORT_INFO[com]['header'], row))
        url = '{}/{}'.format(SERVER, PORT_INFO[com]['name'])
        req = requests.post(url=url, data=data)

        # write file to a file as a backup
        yield data


loglines = read_com('COM7')
# print (loglines
for line in loglines:
    # row = re.split(r'\t+', line.strip())
    print(line)
