from multiprocessing import Process
from transfer import read_com, create_log, connect_to_server, read_udp
from config import PORT_INFO

if __name__ == '__main__':
    processes = []
    # run GPS and meteorology
    p0 = Process(target=read_udp)
    processes.append(p0)
    msg = 'Sensors Bridge connected to ancillary data'
    msg_with_time = create_log(msg)
    print(msg_with_time)

    for com in PORT_INFO.keys():
        if 'baud_rate' in PORT_INFO[com].keys():  # To exclude UDP reading
            msg = 'Sensors Bridge connected to {} ({})'.format(
                PORT_INFO[com]['name'], com
            )
            msg_with_time = create_log(msg)
            print(msg_with_time)
            connect_to_server(com)

            p = Process(target=read_com, args=(com,))
            processes.append(p)

    for p in processes:
        p.start()
