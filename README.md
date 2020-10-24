# Water Monitor Sensors Bridge

Sensors Bridge receives data from water quality sensors. It currently support Ecotriplets 1, 2, 
and 3, dissolved oxygen, and co2procv and any sensor sent via UDP such as GPS and water quality 
sensors. It saves data to a folder and sends it to a server. Sensors Bridge is developed under 
the U.S. Army Engineer Research and Development Center (ERDC) funded project coordinated by 
Mississippi State University Geosystems Research Institute. It is initially designed to read 
water quality sensor and ancillary data from MSU SeaTrac Autonomous Boat and send it to a 
receiving server and the [Water Monitor](https://water.geosci.msstate.edu/monitor/) web application. It is customizable to use for other 
sensors but this feature is not yet added. 

It is a free software under GNU General Public License 3.

![Options](images/options.png)
![Sensors Configuration](images/sensors_configuration.png)

## User Installation

- A Windows installer and a portable executable are located in `dist` folder of the repository.
- Install SensorsBridge using the installer SensorsBridgeInstaller_v1.0.0.exe
- You can run SensorsBridgePortable_v1.0.0.exe without installation   


## Developer Installation

- Install Python 3.6 

``` bash
# Install dependencies
pip install -r requirements.txt

```

Configuration
---
In config.json set:
- `data_path` to your preferred output location
- Change COM3, COM4, COM5, COM6, COM7 to their respective port in which they are connected to your computer.
- If you have data streamed through a UDP port, modify `udp_port`
---
In you would like to send data to your server fill out the following:

- "server": "https://servername.org/somepath/"
- "server_login": "https://water.geosci.msstate.edu/monitoradmin/signin"
- "username": "someusername"
- "password": "somepassword"
- If you are not sending data to a server make sure to set `send_data` to `false`.

Usage
---
- Run run.py or double click `start_sensors_bridge.bat` file. It will start reading and saving data to the `data_path`.
- You can run the `main.py` script as a schedule task using `sensors_bridge_task.xml`.

## App Info

### Authors
- Wondimagegn Tesfaye Beshah
- Jane Moorhead
- Dr. Padmanava Dash

### Version
1.0.0

### License
[GNU General Public License Version 3](https://github.com/wondie/sensors_bridge/blob/master/LICENSE)
 
Copyright@ [Mississippi State University](https://www.msstate.edu/)
 
