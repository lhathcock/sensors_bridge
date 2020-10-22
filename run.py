import multiprocessing
from multiprocessing import Process
import json
from main import Bridge, STOP
# from config import PORT_INFO
with open('config.json') as f:
    config = json.load(f)

bridge = Bridge(config)
bridge.delete_old_files()
if __name__ == '__main__':
    multiprocessing.freeze_support()
    # processes = []
    # # run GPS and meteorology
    #
    # msg = 'Sensors Bridge connected to port 50000'
    # msg_with_time = bg.create_log(msg)
    # print(msg_with_time)
    #
    # p0 = Process(target=read_udp)
    # processes.append(p0)
    # connect_to_server('Ancillary')
    #
    # for com in c.keys():
    #     if 'baud_rate' in PORT_INFO[com].keys():  # To exclude UDP reading
    #         msg = 'Sensors Bridge connected to {} ({})'.format(
    #             PORT_INFO[com]['name'], com
    #         )
    #         msg_with_time = create_log(msg, False)
    #         # print(msg_with_time)
    #         connect_to_server(com)
    #
    #         p = Process(target=read_com, args=(com,))
    #         processes.append(p)
    #
    # for p in processes:
    #     p.start()

    processes = []
    # run GPS and meteorology
    # logger_init = False
    msg = 'Sensors Bridge connected to ancillary data (50000)'.format(
        config['basic_options']['udp_port']
    )
    # app.create_log_tab(sensor['label'])
    # XStream.stdout().messageWritten.connect(app.insert_log_text)
    msg_with_time = bridge.create_log(msg, 'gpsposition', )
    # print('gps')
    p0 = Process(target=bridge.read_udp)
    p0.name = 'gpsposition'
    processes.append(p0)
    for sensor in config['sensors_config']:

        if sensor['type'] == 'COM port':  # To exclude UDP reading
            msg = 'Sensors Bridge connected to {} ({})'.format(
                sensor['name'], sensor['code']
            )
            # app.create_log_tab(sensor['label'])
            # if not logger_init:
                # XStream.stdout().messageWritten.connect(app.insert_log_text)
                # logger_init = True
            msg_with_time = bridge.create_log(msg, sensor['name'])
            if config["server_options"]["send_data"]:
                bridge.connect_to_server(sensor)

            p = Process(target=bridge.read_com, args=(sensor,))
            p.name = sensor['label']
            processes.append(p)
        # if sensor['name'] == 'gpsposition':
            # msg = 'Sensors Bridge connected to ancillary data (50000)'.format(
            #     config['basic_options']['udp_port']
            # )
            # # app.create_log_tab(sensor['label'])
            # # XStream.stdout().messageWritten.connect(app.insert_log_text)
            # msg_with_time = bridge.create_log(msg, sensor['name'], )
            # print('gps')
            # p0 = Process(target=bridge.read_udp)
            # p0.name = sensor['label']
            # processes.append(p0)
    # XStream.stdout().messageWritten.connect(app.insert_log_text)
    print (STOP)
    for p in processes:
        p.start()