SERVER = 'https://water.geosci.msstate.edu/monitoradmin/'
SERVER_LOGIN = "https://water.geosci.msstate.edu/monitoradmin/signin"
USERNAME = 'msuseatracboat'
PASSWORD = '44dffA33tv'
DATA_PATH = r'C:\Users\User\Desktop\sensors_bridge\data'
PORT_INFO = {
    'COM3': {
        'name': 'co2procv',
        'byte_size': 72, 'baud_rate': 19200,
        'separator': r',',
        'header': ['start', 'year', 'month', 'day', 'hour',
                   'minute', 'second', 'zero_ad', 'current_ad', 'measured_co2',
                   'avarage_irga_temperature', 'humidity', 'humidity_sensor_temperature',
                   'gas_stream_pressure', 'igr_detector_temperature']
    },
    'COM4': {
        'byte_size': 48, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1', 'chl_raw',
                   'wavelength2', 'peryth_raw', 'wavelength3',
                   'pcyan_raw', 'wavelength4'],
        'name': 'ecotriplet1'

    },
    'COM5': {
        'byte_size': 44, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1', 'bb_470_raw',
                   'wavelength2', 'bb_532_raw', 'wavelength3',
                   'bb_650_raw', 'wavelength4'],
        'name': 'ecotriplet2'
    },
    'COM6': {
        'byte_size': 45, 'baud_rate': 19200,
        'separator': r'\t+',
        'header': ['date', 'time', 'wavelength1',
                   'turbidity_595_nm_raw', 'wavelength2',
                   'turbidity_700_nm_raw', 'wavelength3',
                   'cdom_460_nm_raw', 'wavelength4'],
        'name': 'ecotriplet3'
    },
    'COM7': {
        'byte_size': 72, 'baud_rate': 9600,
        'separator': r',',
        'header': ['raw_phase_delay', 'raw_thermistor_voltage',
                   'oxygen_ml_l', 'temperature'],
        'name': 'dissolvedoxygen'
    }
}
LAN_HOST = "10.1.20.88"
LAN_PORT = 50000

GPS_HEADERS = {
    '$HCHDG': ['magnetic_heading', 'magnetic_deviation',
               'deviation_direction', 'magnetic_variation', 'variation_direction'],
    '$GPGGA': ['utc_time','latitude','latitude_direction',
               'longitude', 'longitude_direction','gps_quality',
               'number_of_satellites','hdop','altitude', 'nodata1',
               'geoidal_separation', 'nodata2','age', 'station_id'],
    '$VMVHW': [],
    '$YXXDR': []
}
