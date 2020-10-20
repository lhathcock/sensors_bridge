from multiprocessing import Process

from transfer import read_com, create_log, connect_to_server, read_udp,delete_old_files
from config import PORT_INFO
delete_old_files()
if __name__ == '__main__':
    processes = []
    # run GPS and meteorology

    msg = 'Sensors Bridge connected to port 50000'
    msg_with_time = create_log(msg)
    print(msg_with_time)

    p0 = Process(target=read_udp)
    processes.append(p0)
    connect_to_server('Ancillary')

    for com in PORT_INFO.keys():
        if 'baud_rate' in PORT_INFO[com].keys():  # To exclude UDP reading
            msg = 'Sensors Bridge connected to {} ({})'.format(
                PORT_INFO[com]['name'], com
            )
            msg_with_time = create_log(msg, False)
            # print(msg_with_time)
            connect_to_server(com)

            p = Process(target=read_com, args=(com,))
            processes.append(p)

    for p in processes:
        p.start()
