
if __name__ == '__main__':
    import multiprocessing
    from multiprocessing import Process
    import json
    from main import Bridge

    with open('config.json') as f:
        config = json.load(f)

    multiprocessing.freeze_support()

    bridge = Bridge(config)

    bridge.delete_old_files()
    processes = []
    # run GPS and meteorology

    msg = 'Sensors Bridge connected to ancillary data (50000)'.format(
        config['basic_options']['udp_port']
    )

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

            msg_with_time = bridge.create_log(msg, sensor['name'])
            if config["server_options"]["send_data"]:
                bridge.connect_to_server(sensor)

            p = Process(target=bridge.read_com, args=(sensor,))
            p.name = sensor['label']
            processes.append(p)

    for p in processes:
        p.start()