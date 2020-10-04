SERVER='http://localhost:6000'
SERVER_LOGIN = "http://localhost:6000/signin"
USERNAME='user1'
PASSWORD='password1'
PORT_INFO = {
    'COM3': {
        'byte_size': 72, 'baud_rate': 19200,
        'separator': r',',
        'header': ['start', 'year', 'month', 'day', 'hour',
                   'minute','second', 'zero_ad', 'current_ad', 'measured_co2',
                   'avarage_irga_temperture', 'humidity', 'humidity_sensor_temperature'],
        'name':'co2procv'
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
                   'oxygen_ml_L', 'temperature'],
        'name': 'dissolvedoxygen'
    }
}
