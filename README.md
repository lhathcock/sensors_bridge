# Water Monitor Sensors Bridge

> Receives data from water quality sensors - Ecotriplets 1, 2, and 3, dissolved oxygen, and co2procv.
> It saves data to a folder and sends it to a server.

## User Installation

- The installer and the portable executable are located in `dist` folder of the repository.
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

- server: "https://servername.org/somepath/"
- server_login = "https://water.geosci.msstate.edu/monitoradmin/signin"
- username: "someusername"
- password: "somepassword"
- If you are not sending data to a server make sure to set `send_data` to `false`.

Usage
---
- Run run.py or double click `start_sensors_bridge.bat` file. It will start reading and saving data to the DATA_PATH.
- You can run the script as a schedule task using `sensors_bridge_task.xml`.

## App Info

### Authors
- Wondimagegn Tesfaye Beshah
- Jane Moorhead
- Dr. Padmanava Dash

### Version
1.0.0

### License
 GNU General Public License Version 3
 
Copyright@ Mississippi State University
