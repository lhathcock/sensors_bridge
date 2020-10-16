from multiprocessing import Process
from transfer import read_com, create_log, connect_to_server, read_udp
from config import PORT_INFO

if __name__ == '__main__':
    processes = []
    # run GPS and meteorology
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
        else:

            msg = 'Sensors Bridge connected to {} ({})'.format(
                PORT_INFO[com]['name'], com
            )

            msg_with_time = create_log(msg)
            print(msg_with_time)
            p0 = Process(target=read_udp, args=(com,))
            processes.append(p0)

    for p in processes:
        p.start()
