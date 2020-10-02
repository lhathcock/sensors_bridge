import re
import time
import os
import serial
import requests

PORT_INFO = {
    'COM3': {
        'byte_size': 72, 'baud_rate': 19200,
        'separator': r',',
        'header': ['date']
    },
    'COM4': {
        'byte_size': 48, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1', 'chl_raw',
                   'wavelength2', 'peryth_raw', 'wavelength3',
                   'pcyan_raw', 'wavelength4'],
    },
    'COM5': {
        'byte_size': 44, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1', 'bb_470_raw',
                   'wavelength2', 'bb_532_raw', 'wavelength3',
                   'bb_650_raw', 'wavelength4']
    },
    'COM6': {
        'byte_size': 45, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1',
                   'turbidity_595_nm_raw', 'wavelength2',
                   'turbidity_700_nm_raw', 'wavelength3',
                   'cdom_460_nm_raw', 'wavelength4']
    },
    'COM7': {
        'byte_size': 72, 'baud_rate': 9600,
        'separator': r',',
        'header': ['raw_phase_delay', 'raw_thermistor_voltage',
                   'oxygen_ml_L', 'temperature']
    }
}
API_ENDPOINT = 'https://water.geosci.msstate.edu'

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


# loglines = read_file(file_path)
# for line in loglines:
#     row = re.split(r'\t+', line.strip())
#     # data = dict(zip(eco_1_header, row))
#     # print (data)
#     print(line, end='')

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
        # print (data)
        r = requests.post(url=API_ENDPOINT, data=data)
        # write file to a file as a backup
        yield data


loglines = read_com('COM7')
# print (loglines
for line in loglines:
    # row = re.split(r'\t+', line.strip())
    print(line)
