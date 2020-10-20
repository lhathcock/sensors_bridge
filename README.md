# Water Monitor Sensors Bridge

> Receives data from water quality sensors - Ecotriplets 1, 2, and 3, dissolved oxygen, and co2procv.
> It saves data to a folder and sends it to a server.

## Installation

- Install Python 3.6 or later 

``` bash
# Install dependencies
pip install -r requirements.txt

```

Configuration
---
In config.py set:
- `DATA_PATH` to your preferred output location
- Change COM3, COM4, COM5, COM6, COM7 to their respective port in which they are connected to your computer.

---
Create connection.py and fill out the following:

- SERVER = 'https://servername.org/somepath/'
- SERVER_LOGIN = "https://water.geosci.msstate.edu/monitoradmin/signin"
- USERNAME = 'someusername'
- PASSWORD = 'somepassword'

Usage
---
- Run main.py or double click `start_sensors_bridge.bat` file. It will start reading and saving data to the DATA_PATH.
- You can run the script as a schedule task using `sensors_bridge_task.xml`.

## App Info

### Authors
- Jane Moorhead
- Wondimagegn Tesfaye Beshah

### Version

1.0.0

### License

Copyright@ Mississippi State University
