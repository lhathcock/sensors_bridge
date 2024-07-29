import json
import csv
import re
import time
from os import remove, path, SEEK_END, mkdir
import socket
import glob
import traceback
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests

from os.path import expanduser

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
from tkinter import filedialog
from tkinter import scrolledtext



def load_default_config():
    """
    Load the default configuration if there is no configuration already set.
    :return:
    """
    if path.isfile(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'r') as s:

            config_path = s.readline().strip()
            config_folder = path.dirname(config_path)
    else:
        config_path = path.join(ROOT_PATH, 'config.json')
        config_folder = ROOT_PATH
        with open(SETTINGS_PATH, 'w') as s:
            s.write(config_path)

    if path.isfile(config_path):

        config_folder = config_folder.replace('\\', '/')

        with open(config_path) as f:
            config = json.load(f)
    else:
        config_path = None
            
    return config

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
                    data=params, headers=headers, verify=VERIFY_SECURE, 
                    timeout = 5
                )
                if response.status_code != 200:
                    if not show_no_internet_error:
                        msg = 'Error to login {}. {} ({}) data saved ' \
                              'locally until internet is restored'.format(
                            response.status_code, sensor['label'], sensor['code'])

                        msg_with_time = self.create_log(msg, sensor['name'])
                        printtext(msg_with_time + '\n')
                    SESSION = None
                    return False
                return True
            except:
                msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
                printtext (traceback.format_exc() + '\n')
                # print(msg_with_time)
                return False
                
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
        #print (url)
        #print (sensor, data)
        
        try:
            response = SESSION.post(url, data=data, verify=VERIFY_SECURE, timeout=5)
            #print (response)
            if response.status_code != 200:
                msg = 'Error: {} Failed to send {} at port {}. ' \
                      'Saving it to local file.'.format(
                    response.status_code, sensor['name'], sensor['code']
                )

                msg_with_time = self.create_log(msg, sensor['name'])
                #print(msg_with_time)
                SESSION = None
                return False
            else:
                # if com == 'GPRMC':
                # print ('Sent {} {}'.format(sensor['name'], data))
                return True
        except:
            msg_with_time = self.create_log(traceback.format_exc(), sensor['name'])
            #print(msg_with_time)
            return False
        # print (response.status_code)
        
                
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
        printtext (file_name + '\n')
        file_path = path.join(self.basic_options['data_path'], file_name)
        printtext (file_path + '\n')
        if sensor_name != '':
            msg = '{}$ {} {}\n'.format(sensor_name, dt_string, message)
        else:
            msg = '{} {}\n'.format(dt_string, message)

        with open(file_path, 'a') as data_file:
            data_file.write(msg)
        if show_message:
            printtext(msg.strip() + '\n')
        return msg.strip()


    def send_temp_files(self):
            """
            Send temporary data to the server.
            :return:
            """
            global SESSION
            #if SESSION is None:  # dont send if the user hasn't logged in
            #    return
            temp_files = glob.glob(self.basic_options['data_path'] + '/*.csv')
            #printtext (temp_files + '\n')
            for temp_file in temp_files:  # get com port from temp file

                if not path.exists(temp_file):
                    continue
                sensors = [l for l in self.sensors_config
                           if l['name'] in temp_file]

                if len(sensors) > 0:
                    sensor = sensors[0]
                else:
                    continue  # because it is not a temp file
                #print(temp_file)
                #print(sensor)
                #self.connect_to_server(sensor)
                if SESSION is None:
                    printtext ("No session, returning.\n")
                    return
                

                # debug stuff
                #SESSION = True
                
                #print (sensor)
                
                header = sensor['header'].split(',')
                
                #printtext (header + '\n')
                header.append('datetime')
                msg = 'Sending backup {}'.format(temp_file)
                msg_with_time = self.create_log(msg, sensor['name'])
                # print(msg_with_time)
                lastline = temp_file.split('.')[0] + '_lastline.txt'
                if not path.exists(lastline):
                    f = open(lastline, 'w')
                    f.write('0')
                    f.close()
                    lastlinenum = 0
                    
                else:
                    f = open(lastline, 'r')
                    lastlinenum = int(f.readline())
                    f.close()
                    
                with open(temp_file, "r") as f:
                    lines = f.readlines()

                    for i in range(lastlinenum, len(lines)):
                        if lines[i].endswith('\n'):
                            data = dict(zip(header, lines[i].strip().split(',')))
                            
                            response = self.send_to_server(sensor, data)
                            
                            if response == False:
                                f = open(lastline, 'w')
                                f.write(str(lastlinenum))
                                f.close()
                                return
                            else:
                                lastlinenum = lastlinenum + 1
                                if lastlinenum%50 == 0:
                                    printtext (str(lastlinenum) + "/" + str(len(lines)) + '\n')
                
                # Need to store the last successful processed line.
                f = open(lastline, 'w')
                f.write(str(lastlinenum))
                f.close()
                
                msg2 = 'Completed sending backup {}'.format(temp_file)
                msg_with_time = self.create_log(msg2, sensor['name'])
                #print(msg_with_time)
                header.remove('datetime')
                
def start():
	global running
	running = True
	start_button['state'] = 'disabled'
	stop_button['state'] = 'normal'
	#login_button['state'] = 'disabled'
	#root.update()
	main()
	
def stop():
	global running
	print (running)
	printtext("Stopping execution.\n")
	running = False
	print (running)
	stop_button['state'] = 'disabled'
	start_button['state'] = 'normal'
	#login_button['state'] = 'normal'
	#root.update()

def printstdout(process):
	with process.stdout:
		for line in iter(process.stdout.readline, ''):
			output_text_box.insert(tk.END, line)
			output_text_box.yview(tk.END)
			root.update()
			
def printtext(text):
	for line in text:
		output_text_box.insert(tk.END, line)
		output_text_box.yview(tk.END)
		root.update()

def main():
    global running

    config = load_default_config()
    bridge = Bridge(config)

    for sensor in config['sensors_config']:
        msg = 'Started sending {} data.'.format(
            sensor['label']
        )

        bridge.create_log(msg, sensor['name'])

        if sensor['type'] == 'COM port':  # To exclude UDP reading

            bridge.connect_to_server(sensor)
            #pass
    #bridge.connect_to_server(sensor)
    bridge.send_temp_files()
    tint = time_interval.get()
    print (tint)
    printtext("Sleeping for %s seconds.\n"%(tint))
    if running == True:
        root.after(int(tint) * 1000, main)


# Start main here.
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
print (ROOT_PATH)
print (SB_USER_PATH)
print (SETTINGS_PATH)


        
root = tk.Tk()
root.title('Geosciences Transfer App')
root.geometry('1200x600+50+50')

# /C/UAV_Share/Transfer/
# /ngi/uas/Flight_0126/
time_interval = tk.StringVar()
time_interval.set("30")

#dest_ep = tk.StringVar()
#dest_ep.set("ce1b44b8-8e3f-11ea-b3bf-0ae144191ee3")
#dest_ep.set("0bcd5260-fd3f-4602-838f-4d1b27f5c768")

#source_path = tk.StringVar()
#dest_path = tk.StringVar()



tframe = ttk.Frame(root)
tframe.pack(padx=10, pady=10, fill='x', expand=True)

time_label = ttk.Label(tframe, text='Interval')
time_label.pack(fill='x', expand=True)

time_entry = ttk.Entry(tframe, textvariable=time_interval)
time_entry.pack(fill='x', expand=True)
#sep_entry.insert(0, source_ep.get())
time_entry.focus()

#sep_label = ttk.Label(tframe, text='Source Endpoint')
#sep_label.pack(fill='x', expand=True)
"""
sep_entry = ttk.Entry(tframe, textvariable=source_ep)
sep_entry.pack(fill='x', expand=True)
#sep_entry.insert(0, source_ep.get())
sep_entry.focus()

dep_label = ttk.Label(tframe, text='Destination Endpoint')
dep_label.pack(fill='x', expand=True)

dep_entry = ttk.Entry(tframe, textvariable=dest_ep)
dep_entry.pack(fill='x', expand=True)
#dep_entry.insert(0, dest_ep.get())

spath_label = ttk.Label(tframe, text='Source Path')
spath_label.pack(fill='x', expand=True)

spath_entry = ttk.Entry(tframe, textvariable=source_path)
spath_entry.pack(fill='x', expand=True)
spath_entry.insert(0, '/C/UAV_Share/Transfer/2024-04-11_Test/')

#spath_button = ttk.Button(text='Browse', command=browse_button)
#spath_button.pack(fill='x', expand=True)

dpath_label = ttk.Label(tframe, text='Destination Path')
dpath_label.pack(fill='x', expand=True)

dpath_entry = ttk.Entry(tframe, textvariable=dest_path)
dpath_entry.pack(fill='x', expand=True)
dpath_entry.insert(0, '/ngi/uas/Test/2024-05-17_Test/')
"""


start_button = ttk.Button(text='Start Transfer', command=start)
start_button.pack(fill='x', expand=True)

stop_button = ttk.Button(text='Stop Transfer', command=stop)
stop_button.pack(fill='x', expand=True)
stop_button['state'] = 'disabled'

#login_button = ttk.Button(text='Log in to Globus', command=login)
#login_button.pack(fill='x', expand=True)

output_text_box = scrolledtext.ScrolledText(tframe, wrap=tk.WORD, height=20, width=200, font=("Arial", 8))
output_text_box.pack(padx=10, pady=10)

root.mainloop()